from __future__ import unicode_literals

import logging
import os

from mopidy import config, ext


__version__ = '0.1.0'

logger = logging.getLogger(__name__)


class Extension(ext.Extension):

    dist_name = 'Mopidy-Kodi'
    ext_name = 'kodi'
    version = __version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        schema['host'] = config.Hostname()
        schema['port'] = config.Port()
        schema['user'] = config.String(optional=True)
        schema['password'] = config.Secret(optional=True)
        return schema

    def setup(self, registry):
        from .backend import KodiBackend
        registry.add('backend', KodiBackend)
