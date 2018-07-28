# coding=utf-8
import os
import platform
from oslo_config import cfg
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


default_opts = [
    cfg.BoolOpt('debug', default=False, help='DEBUG'),
    cfg.StrOpt('language_code', default='zh-hans', help='LANGUAGE_CODE'),
    cfg.StrOpt('time_zone', default='Asia/Shanghai', help='TIME_ZONE'),
    cfg.BoolOpt('use_i18n', default=True, help='USE_I18N'),
    cfg.BoolOpt('use_l10n', default=True, help='USE_L10N'),
    cfg.BoolOpt('use_tz', default=False, help='USE_TZ'),
    cfg.StrOpt('static_url', default='/public/', help='STATIC_URL'),
    cfg.ListOpt('allowed_hosts', default=['*'], help='ALLOWED_HOSTS'),
    cfg.ListOpt('staticfiles_dirs', default=[
        os.path.join(BASE_DIR, 'files', 'public'),
        os.path.join(BASE_DIR, 'static')
    ], help='STATICFILES_DIRS'),
    cfg.ListOpt('locale_paths', default=[os.path.join(BASE_DIR, 'locale')], help='LOCALE_PATHS'),
    cfg.StrOpt('static_root', default=os.path.join(BASE_DIR, 'files', 'public'), help='STATIC_ROOT'),
    cfg.StrOpt('media_root', default=os.path.join(BASE_DIR, 'files', 'upload'), help='MEDIA_ROOT'),
    cfg.StrOpt('tmp_dir', default=os.path.join(BASE_DIR, 'files', 'tmp'), help='TMP_DIR'),
    cfg.StrOpt('updates_dir', default=os.path.join(BASE_DIR, 'files', 'updates'), help='UPDATES_DIR'),
    cfg.StrOpt('edufiles_dir', default=os.path.join(BASE_DIR, 'files', 'edufiles'), help='EDUFILES_DIR'),
    cfg.StrOpt('log_path', default=os.path.join(BASE_DIR, 'files', 'logs'), help='LOG_PATH'),
]

if platform.system() == 'Windows':
    cache_opts = [
        cfg.StrOpt('backend', default='django.core.cache.backends.memcached.MemcachedCache', help='The port for the cache BACKEND.'),
        cfg.StrOpt('location', default='127.0.0.1:11211', help='The port for the cache LOCATION.'),
        cfg.DictOpt('options', default='', help='The port for the cache OPTIONS.'),
    ]

else:
    cache_opts = [
        cfg.StrOpt('backend', default='django_redis.cache.RedisCache', help='The port for the cache BACKEND.'),
        cfg.StrOpt('location', default='redis://127.0.0.1:6379/1', help='The port for the cache LOCATION.'),
        cfg.DictOpt('options', default={'CLIENT_CLASS': 'django_redis.client.DefaultClient'}, help='The port for the cache OPTIONS.'),
    ]

template_opts = [
    cfg.StrOpt('backend', default='django.template.backends.django.DjangoTemplates', help='TEMPLATES[BACKEND]'),
    cfg.ListOpt('dirs', default=[
        os.path.join(BASE_DIR, 'files/templates'),
        os.path.join(BASE_DIR, 'templates'),
        'django.template.loaders.filesystem.Loader'
    ], help='TEMPLATES[DIRS]'),
    cfg.BoolOpt('app_dirs', default=True, help='TEMPLATES[APP_DIRS]'),
    cfg.DictOpt('options', default={
        'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                ],
    }, help='TEMPLATES[OPTIONS]'),
]

db_opts = [
    # cfg.StrOpt('engine', default='django.db.backends.mysql', help='DATABASE[ENGINE]'),
    cfg.StrOpt('engine', default='django_mysqlpool.backends.mysqlpool', help='DATABASE[ENGINE]'),
    cfg.HostAddressOpt('host', default='127.0.0.1', help='DATABASE[HOST]'),
    cfg.PortOpt('port', default=3306, help='DATABASE[PORT]'),
    cfg.StrOpt('name', default='banbantong', help='DATABASE[NAME]'),
    cfg.StrOpt('user', default='root', help='DATABASE[USER]'),
    cfg.StrOpt('password', default='oseasydads_db', help='DATABASE[PASSWORD]'),
    # cfg.DictOpt('test', default={'CHARSET': 'utf8'}, help='DATABASE[TEST]'),
    cfg.BoolOpt('auto_optimize', default=True, help='DATABASE[AUTO_OPTIMIZE]'),
    cfg.IntOpt('auto_optimize_days', default=5, help='DATABASE[AUTO_OPTIMIZE_DAYS]'),
    cfg.IntOpt('conn_max_age', default=3600, help='DATABASE[CONN_MAX_AGE]'),
]


server_opts = [
    cfg.HostAddressOpt('rp_host', default='banbantong.os-easy.com', help='SERVER[RP_HOST]'),
    cfg.PortOpt('vnc_proxy_port', default=6081, help='SERVER[VNC_PROXY_PORT]'),
    cfg.PortOpt('zmq_port', default=9527, help='SERVER[ZMQ_PORT]'),
    cfg.BoolOpt('ntp_cron', default=True, help='SERVER[NTP_CRON]'),
    cfg.BoolOpt('auto_lessonschedule', default=True, help='SERVER[AUTO_LESSONSCHEDULE]'),
    cfg.StrOpt('default_export_type', default='xls', help='SERVER[DEFAULT_EXPORT_TYPE]'),

    cfg.BoolOpt('no_modify_update_path', default=False, help='SERVER[NO_MODIFY_UPDATE_PATH]'),
    cfg.StrOpt('mysql_path', default='', help='SERVER[MYSQL_PATH]'),
    cfg.IntOpt('task_max_run_period', default=3600, help='SERVER[TASK_MAX_RUN_PERIOD]'),
    cfg.BoolOpt('activate_directly', default=False, help='SERVER[ACTIVATE_DIRECTLY]'),
    cfg.BoolOpt('sync_resource_enable', default=True, help='SERVER[SYNC_RESOURCE_ENABLE]'),  # 服务器保存数据的时候是否进行 CountryToResourcePlatformSyncLog.add_log 操作
    cfg.BoolOpt('sync_log_enable', default=True, help='SERVER[SYNC_LOG_ENABLE]'),  # 服务器保存数据的时候是否进行 SyncLog.add_log 操作
    cfg.BoolOpt('update_statistic_onchange', default=True, help='SERVER[UPDATE_STATISTIC_ONCHANGE]'),  # 服务器数据更新的时候出发Statistic更新

    # cfg.DictOpt('test', default={'CHARSET': 'utf8'}, help='DATABASE[TEST]'),
    cfg.BoolOpt('auto_optimize', default=True, help='DATABASE[AUTO_OPTIMIZE]'),
    cfg.IntOpt('auto_optimize_days', default=5, help='DATABASE[AUTO_OPTIMIZE_DAYS]'),
    cfg.IntOpt('conn_max_age', default=3600, help='DATABASE[CONN_MAX_AGE]'),
    cfg.DictOpt('grade_map', default={
        u'一': u'一', u'二': u'二', u'三': u'三', u'四': u'四', u'五': u'五', u'六': u'六',
        u'七': u'七', u'八': u'八', u'九': u'九', u'十': u'十', u'十一': u'十一', u'十二': u'十二',
        # u'七': u'初一', u'八': u'初一', u'九': u'初一',  u'十': u'高一', u'十一': u'高二', u'十二': u'高三',
        u'电脑教室': u'电脑教室'
    }, help='TEMPLATES[GRADE_MAP]'),
]

mongodb_opts = [
    cfg.BoolOpt('ebable', default=False, help='MONGODB[EBABLE]'),
]

websocket_opts = [
    cfg.BoolOpt('debug', default=False, help='DEBUG'),
    cfg.StrOpt("wsurl", default=u"ws://0.0.0.0:8001", help='WebSocket URL (must suit the endpoint), e.g. ws://0.0.0.0:8001.'),
    cfg.StrOpt("websocket", default="tcp:8001", help='WebSocket server Twisted endpoint descriptor, e.g. "tcp:8001" or "unix:/tmp/mywebsocket".'),
]

server_group = cfg.OptGroup(name='server', title='Options for the SERVER')
cache_group = cfg.OptGroup(name='cache', title='Options for the CACHES')
db_group = cfg.OptGroup(name='db', title='Options for the DATABASE')
template_group = cfg.OptGroup(name='template', title='Options for the TEMPLATES')
mongodb_group = cfg.OptGroup(name='mongodb', title='Options for the TEMPLATES')
websocket_group = cfg.OptGroup(name='websocket', title='Options for the TEMPLATES')


def register_opts(conf):
    conf.register_group(cache_group)
    conf.register_group(db_group)
    conf.register_group(template_group)
    conf.register_group(server_group)
    conf.register_group(mongodb_group)
    conf.register_group(websocket_group)

    conf.register_opts(default_opts)
    conf.register_opts((cache_opts), cache_group)
    conf.register_opts((db_opts), db_group)
    conf.register_opts((template_opts), template_group)
    conf.register_opts((server_opts), server_group)
    conf.register_opts((mongodb_opts), mongodb_group)
    conf.register_opts((websocket_opts), websocket_group)


def list_opts():
    return {
        "DEFAULT": default_opts,
        cache_group: cache_opts,
        db_group: db_opts,
        template_group: template_opts,
        server_group: server_opts,
        mongodb_group: mongodb_opts,
        websocket_group: websocket_opts
    }
