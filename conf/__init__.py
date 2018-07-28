# coding=utf-8
from oslo_config import cfg
import os
import site
import logging

import sync_api

logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONF = cfg.CONF

site.register_opts(CONF)
sync_api.register_opts(CONF)


def load_conf(argv=None, default_config_files=None):
    if argv is None:
        argv = []
    options = dict([k.split('=', 1) for k in argv if '=' in k and len(k.split('=', 1)) == 2])
    default_config_files = default_config_files or []
    if options.get('config-file') and os.path.exists(options['config-file']):
        default_config_files.insert(0, os.path.abspath(options['config-file']))
    elif not default_config_files and os.path.exists(os.path.join(BASE_DIR, 'settings.ini')):
        default_config_files = [os.path.join(BASE_DIR, 'settings.ini')]
    logger.debug('app using config: %s', default_config_files)
    CONF(argv[1:], project='banbantong', default_config_files=default_config_files)

load_conf()
