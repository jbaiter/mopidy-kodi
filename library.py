from __future__ import unicode_literals

import logging
import re
import urllib
from collections import OrderedDict

from mopidy import backend, models


URI_PAT = re.compile(r'^kodi:(.*?)/(.*)$')

logger = logging.getLogger(__name__)


def make_uri(_type, id=None, **params):
    if params:
        param_str =  "&".join("{}={}".format(k, v) for k, v in params.items())
    else:
        param_str = ''
    uri = 'kodi:/{}{}{}'.format(_type,
                                '/{}'.format(id) if id else '',
                                '?' + param_str if param_str else '')
    logging.debug("URI for type={}, id={}, params={} is {}".format(
        _type, id, params, uri))
    return uri


def parse_params(param_str):
    return dict(item.split('=') for item in param_str.split('&'))


def parse_uri(uri):
    uri = uri.replace('kodi:/', '')
    parts = uri.split('?')
    if len(parts) == 2:
        params = parse_params(parts[1])
    else:
        params = {}
    parts = parts[0].split('/')
    _type = parts[0]
    if not _type:
        _type, item_id = None, None
    elif len(parts) > 1:
        item_id = int(parts[1])
    else:
        item_id = None
    return _type, item_id, params


def new_directory(name, _type):
    return models.Ref.directory(uri=make_uri(_type, id=None), name=name)

def make_artist_ref(artist):
    uri = make_uri('album', artist_id=artist['artistid'])
    return models.Ref.artist(uri=uri, name=artist['label'])

def make_album_ref(album):
    uri = make_uri('song', album_id=album['albumid'])
    return models.Ref.album(uri=uri, name=album['label'])

class KodiLibraryProvider(backend.LibraryProvider):
    root_directory = models.Ref.directory(uri='kodi:/', name='Kodi')

    def browse(self, uri):
        _type, _id, params = parse_uri(uri)
        if uri in (None, self.root_directory.uri):
            return [
                new_directory(title, _type)
                for title, _type in (
                    ('Artists', 'artist'), ('Albums', 'album'))]
        elif _type == 'album':
            return [make_album_ref(album)
                    for album in self.backend.remote.get_albums(**params)]
        elif _type == 'artist':
            return [make_artist_ref(artist)
                    for artist in self.backend.remote.get_artists()]
        elif _type == 'song':
            refs = [self._make_track_ref(song)
                    for song in self.backend.remote.get_songs(**params)]
            return refs

    def lookup(self, uri):
        return self._make_track(self.backend.remote.lookup_song(uri))

    def _make_track(song):
        artists = [self._make_artist(self.backend.remote.get_artist(aid))
                   for aid in song['artistid']]
        album = self._make_album(
            self.backend.remote.get_album(song['albumid']))
        return models.Track(
            uri=make_uri('song', song['songid']),
            name=song['label'],
            artists=artists,
            album=album,
            genre=", ".join(song['genre']),
            track_no=song['track'],
            disc_no=song['disc'],
            date=str(song['year']),
            length=1000*song['duration'],
            comment=song['comment'],
            musicbrainzid=song['musicbrainzid'] or None)

    def _make_album(self, album):
        artists = [self._make_artist(self.backend.remote.get_artist(aid))
                   for aid in album['artistid']]
        tracks = self.backend.remote.get_songs(albumid=album['albumid'])
        num_discs = len(set(t['disc'] for t in tracks))
        return models.Album(
            uri=make_uri('album', album['albumid']),
            name=album['label'],
            artists=artists,
            num_tracks=len(tracks),
            num_discs=num_discs,
            date=str(album['year']),
            musicbrainzid=album['musicbrainzid'] or None,
            images=[self._api.get_url(imguri)
                    for imguri in album['thumbnail']])

    def _make_artist(self, artist):
        return models.Artist(
            uri=make_uri('artist', artist['artistid']),
            name=artist['label'],
            musicbrainzid=artist['musicbrainzid'] or None)

    def _make_track_ref(self, song):
        return models.Ref.track(
            uri=self.backend.remote.get_url(song['file']),
            name=song['label'])
