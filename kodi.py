from __future__ import unicode_literals

import functools
import logging

from jsonrpc_requests import Server
from cachetools import TTLCache, cachedmethod
from mopidy import backend


logger = logging.getLogger(__name__)
cached = functools.partial(cachedmethod, lambda x: x._cache)


PROPERTIES = {
    'artist': ['musicbrainzartistid', 'thumbnail'],
    'album': ['artist', 'year', 'musicbrainzalbumid', 'displayartist',
              'artistid', 'thumbnail'],
    'song': ['genre', 'duration', 'musicbrainztrackid', 'year', 'album',
             'artistid', 'albumid', 'artist', 'comment', 'track', 'file',
             'disc']
}


class KodiClient(object):
    def __init__(self, config):
        self._cache = TTLCache(maxsize=2048, ttl=3600)
        if 'user' in config and 'password' in config:
            self.auth = (config['user'], config['password'])
        else:
            self.auth = None
        self.host = config['host']
        self.port = config['port']
        self.chunk_size = 750
        self._api = Server(
            url='http://{host}:{port}/jsonrpc'.format(**config),
            auth=self.auth)

    def _make_generator(self, method, data_key, **params):
        logger.debug("Fetching first chunk of {}".format(data_key))
        params.update({'limits': {'start': 0, 'end': self.chunk_size}})
        resp = method(**params)
        for d in resp[data_key]:
            yield d
        num_total = resp['limits']['total']
        cur_start = self.chunk_size
        while cur_start < num_total:
            params['limits']['start'] = cur_start
            params['limits']['end'] = cur_start + self.chunk_size
            logger.debug("Fetching next chunk from #{}".format(cur_start))
            resp = method(**params)
            for d in resp[data_key]:
                yield d
            cur_start += self.chunk_size

    @cached()
    def get_artists(self):
        artists = list(self._make_generator(
            self._api.AudioLibrary.GetArtists, 'artists',
            properties=PROPERTIES['artist']))
        self._cache.update({'artist.{}'.format(a['artistid']): a
                            for a in artists})
        return artists

    def get_artist(self, artist_id):
        artist_id = int(artist_id)
        cached = self._cache.get('artist.{}'.format(artist_id))
        if cached is None:
            try:
                artist = self._api.AudioLibrary.GetArtistDetails(
                    artistid=artist_id,
                    properties=PROPERTIES['artist'])['artistdetails']
                cached['artist.{}'.format(artist_id)] = artist
                return artist
            except Exception as e:
                cached['artist.{}'.format(artist_id)] = None
                return None
        else:
            return cached

    @cached()
    def get_albums(self, artist_id=None, recently_added=False):
        if recently_added:
            return self._api.AudioLibrary.GetRecentlyAddedAlbums()['albums']
        if artist_id is not None:
            artist_id = int(artist_id)
        params = {'properties': PROPERTIES['album'],
                  'data_key': 'albums'}
        if artist_id:
            params['filter'] = {'artistid': artist_id}
        albums = list(self._make_generator(
            self._api.AudioLibrary.GetAlbums, **params))
        self._cache.update({'album.{}'.format(a['albumid']): a
                            for a in albums})
        return albums

    def get_album(self, album_id):
        album_id = int(album_id)
        cached = self._cache.get('album.{}'.format(album_id))
        if cached is None:
            try:
                artist = self._api.AudioLibrary.GetAlbumDetails(
                    albumid=album_id,
                    properties=PROPERTIES['album'])['albumdetails']
                cached['album.{}'.format(album_id)] = album
                return album
            except Exception as e:
                cached['album.{}'.format(album_id)] = None
                return None
        else:
            return cached


    @cached()  # First-level cache for accessing all tracks
    def get_songs(self, album_id=None):
        if album_id is not None:
            album_id = int(album_id)
        params = {'properties': PROPERTIES['song'],
                  'data_key': 'songs'}
        if album_id:
            params['filter'] = {'albumid': album_id}
        songs = list(self._make_generator(
            self._api.AudioLibrary.GetSongs, **params))
        # Second level cache so that get_song doesn't have to make an API call
        self._cache.update({'song.{}'.format(s['songid']): s for s in songs})
        self._cache.update({'songpath.{}'.format(s['file']): s['songid']
                           for s in songs})
        return songs

    def get_song(self, song_id):
        song_id = int(song_id)
        cached = self._cache.get('song.{}'.format(song_id))
        if cached is None:
            try:
                song = self._api.AudioLibrary.GetSongDetails(
                    songid=song_id,
                    properties=PROPERTIES['song'])['songdetails']
                cached['song.{}'.format(song_id)] = song
                return song
            except Exception as e:
                cached['song.{}'.format(song_id)] = None
                return None
        else:
            return cached

    def lookup_song(self, uri):
        filename = self._cache.get('trackurl.{}'.format(uri))
        if not filename:
            return None
        song_id = self._cache.get('songpath.{}'.format(filename))
        if not song_id:
            return None
        return self._cache.get('song.{}'.format(song_id))

    @cached()
    def get_url(self, filepath):
        path = self._api.Files.PrepareDownload(filepath)
        url = "http://{}{}:{}/{}".format(
            "{}:{}@".format(*self.auth) if self.auth else '',
            self.host, self.port, path['details']['path'])
        self._cache['trackurl.{}'.format(url)] = filepath
        return url
