from __future__ import unicode_literals

import logging

from mopidy import backend

import pykka

from .library import KodiLibraryProvider
from .kodi import KodiClient


logger = logging.getLogger(__name__)


class KodiBackend(pykka.ThreadingActor, backend.Backend):
    def __init__(self, config, audio):
        super(KodiBackend, self).__init__()
        self.config = config
        self.remote = KodiClient(config['kodi'])
        self.library = KodiLibraryProvider(backend=self)
        self.playback = KodiPlaybackProvider(audio=audio, backend=self)
        self.uri_schemes = ['kodi']


class KodiPlaybackProvider(backend.PlaybackProvider):
    def translate_uri(self, uri):
        return self.backend.library.resolve_track_uri(uri)
