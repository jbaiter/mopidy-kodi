from __future__ import unicode_literals

import logging

from mopidy import backend


logger = logging.getLogger(__name__)


class KodiLibraryProvider(backend.LibraryProvider):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError

    def add_to_vfs(self, _model):
        raise NotImplementedError

    def browse(self, uri):
        raise NotImplementedError

    def lookup(self, uri):
        raise NotImplementedError
