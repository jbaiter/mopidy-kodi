from __future__ import unicode_literals

import functools
import logging

from jsonrpc_requests import Server
from cachetools import TTLCache, cached as _cached
from mopidy import backend


cache = TTLCache(maxsize=2048, ttl=3600)
logger = logging.getLogger(__name__)


cached = functools.partial(_cached, cache)


class KodiClient(object):
    def __init__(self, config):
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
        return self._make_generator(
            self._api.AudioLibrary.GetArtists, 'artists',
            properties=['musicbrainzartistid', 'thumbnail'])

    @cached()
    def get_albums(self, artist_id=None):
        params = {'properties': ['artist', 'year', 'musicbrainzalbumid',
                                 'displayartist', 'artistid', 'thumbnail'],
                  'data_key': 'albums'}
        if artist_id:
            params['filter'] = {'artistid': artist_id}
        return self._make_generator(self._api.AudioLibrary.GetAlbums, **params)

    @cached()
    def get_songs(self, album_id=None):
        params = {'properties': ['genre', 'duration', 'musicbrainztrackid',
                                 'year', 'album', 'artistid', 'albumid',
                                 'artist', 'comment', 'track', 'file', 'disc'],
                  'data_key': 'songs'}
        if album_id:
            params['filter'] = {'albumid': album_id}
        return self._make_generator(self._api.AudioLibrary.GetSongs, **params)

    @cached()
    def get_url(self, filepath):
        path = self._api.Files.PrepareDownload(filepath)
        return "http://{}{}:{}/{}".format(
            "{}:{}@".format(*self.auth) if self.auth else '',
            self.host, self.port, path['details']['path'])
