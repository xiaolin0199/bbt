# coding=utf-8
import os
from conf import CONF

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEBUG = CONF.debug
ALLOWED_HOSTS = CONF.allowed_hosts

INSTALLED_APPS = [
    # 'django.contrib.admin',
    # 'django.contrib.auth',
    # 'django.contrib.contenttypes',
    'django.contrib.sessions',
    # 'django.contrib.messages',
    'django.contrib.staticfiles',

    'BanBanTong.db',
    'BanBanTong.views',
    'BanBanTong.commands',
    'ws',
    # 'websocket_server',
    'machine_time_used',
    'edu_point',
    'activation',

    'django_rq'
    # 'south',
    # 'django_extensions',
]

MIDDLEWARE = [
    # 'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    # 'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'BanBanTong.utils.middleware.ValidateDateRangeMiddleware',
    'utils.middleware.JsonResponseMiddleware',
]

ROOT_URLCONF = 'urls'
DEFAULT_CONTENT_TYPE = 'text/html'
TEMPLATES = [
    {
        'BACKEND': CONF.template.backend,
        'DIRS': CONF.template.dirs,
        'APP_DIRS': CONF.template.app_dirs,
        'OPTIONS': CONF.template.options,
    },
]


WSGI_APPLICATION = 'wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': CONF.db.engine,
        'NAME': CONF.db.name,
        'USER': CONF.db.user,
        'PASSWORD': CONF.db.password,
        'HOST': CONF.db.host,
        'PORT': CONF.db.port,
        'CONN_MAX_AGE': CONF.db.conn_max_age,
        'OPTIONS': {'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"},
        'TEST_CHARSET': "utf8",
        'TEST_COLLATION': "utf8_general_ci",
    }
}
LANGUAGE_CODE = CONF.language_code
TIME_ZONE = CONF.time_zone
USE_I18N = CONF.use_i18n
USE_L10N = CONF.use_l10n
USE_TZ = CONF.use_tz
LOCALE_PATHS = CONF.locale_paths
STATIC_URL = CONF.static_url
PUBLIC_ROOT = os.path.join(BASE_DIR, 'files', 'public')
DOC_JSON_ROOT = os.path.join(BASE_DIR, 'doc', 'source', 'static', 'json')
if DEBUG:
    # STATICFILES_DIRS = ('', os.path.join(BASE_DIR, 'static'))
    STATICFILES_DIRS = CONF.staticfiles_dirs
else:
    STATIC_ROOT = CONF.static_root

MEDIA_ROOT = CONF.media_root
MEDIA_URL = ''


ADMINS = (
    ('admin', 'admin@admin.com'),
    ('oseasy', 'admin@admin.com'),
)

ADMIN_USERS = ['admin', 'oseasy']


CACHES = {
    'default': {
        'BACKEND': CONF.cache.backend,
        'LOCATION': CONF.cache.location,
        'OPTIONS': CONF.cache.options
    }
}


MYSQLPOOL_BACKEND = 'QueuePool'
MYSQLPOOL_ARGUMENTS = {
    'max_overflow': -1,
    'pool_size': 10,
    'use_threadlocal': False,
}


PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)


# Make this unique, and don't share it with anybody.
SECRET_KEY = '$gw&!)$p5-&xgm%$&=1c1vi5lgya2u96zve4-#95i9bp@)%dz5'

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True


ACTIVATE_DIRECTLY = CONF.server.activate_directly
AUTO_LESSONSCHEDULE = CONF.server.auto_lessonschedule


# See https://docs.djangoproject.com/en/1.10/topics/logging
# log levels: CRITICAL > ERROR > WARNING(default) > INFO > DEBUG > NOTSET
LOG_PATH = CONF.log_path
if not os.path.exists(LOG_PATH):
    os.mkdir(LOG_PATH)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s [%(name)s:%(lineno)d] %(levelname)s- %(message)s',
        },
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'costom': {
            'format': '\n%(levelname)s %(asctime)s@%(name)s.%(funcName)s:%(lineno)d %(message)s'
        },
        'command-line': {
            'format': '%(levelname)s@%(name)s.%(lineno)d: %(message)s'
        },
        'console': {
            'format': '\n%(levelname)s %(asctime)s@%(name)s.%(funcName)s:%(lineno)d\n%(message)s'
        },
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[%(server_time)s] %(message)s',
        }
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        # 'require_level_matched_debug': {
        #     '()': 'utils.logger.RequireLevelMachedFilter',
        #     '.': {'require_level': 'DEBUG'}
        # }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'utils.logger.ColorFormatter',
            'formatter': 'console'
        },
        'command': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'utils.logger.ColorFormatter',
            'formatter': 'command-line'
        },
        'django.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'debug': {
            'backupCount': 5,
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'filename': os.path.join(LOG_PATH, 'debug.log'),
            'formatter': 'costom',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 5242880
        },
        'warning': {
            'backupCount': 5,
            'level': 'WARNING',
            'filename': os.path.join(LOG_PATH, 'warning.log'),
            'formatter': 'costom',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 5242880
        },
        'error': {
            'backupCount': 5,
            'level': 'ERROR',
            'filename': os.path.join(LOG_PATH, 'error.log'),
            'formatter': 'costom',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 5242880
        },
        'null': {
            'class': 'logging.NullHandler',
            'level': 'DEBUG',
        },
        'exceptions': {
            'backupCount': 9,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_PATH, 'exception.log'),
            'formatter': 'default',
        },
        'websocket': {
            'backupCount': 9,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_PATH, 'websocket.log'),
            'maxBytes': 5242880,
            'formatter': 'default',
            'level': 'INFO',
        },
    },
    'loggers': {
        '': {
            'handlers': ['debug', 'warning', 'error', 'mail_admins'],
            'level': 'DEBUG',
        },
        'django': {
            'handlers': ['console', 'mail_admins'],
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['debug', 'warning', 'error', 'mail_admins', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['django.server'],
            'level': 'INFO',
            'propagate': False,
        },
        'utils.middleware': {
            'handlers': ['exceptions'],
        },
        'ws': {
            'handlers': ['debug', 'warning', 'error', 'websocket', 'console'],
            'level': 'DEBUG',
        },
        'cmd': {
            'handlers': ['command'],
            'level': 'DEBUG',
        },
        'rq.worker': {
            'handlers': ['debug', 'warning', 'error', 'console'],
            'level': 'INFO',
        }
    }
}
for app in INSTALLED_APPS:
    key = app.split('.', 1)[0]
    if key.startswith('django') or key in LOGGING['loggers']:
        continue
    LOGGING['loggers'][key] = {'handlers': ['debug', 'warning', 'error', 'console'], 'level': 'DEBUG', }

# the monkey patch
import utils
utils.monkey_patch()
utils.add_apps_into_sys_path(BASE_DIR)
utils.patch_technical_500_response(DEBUG)
del utils


RQ_QUEUES = {
    'default': {
        'USE_REDIS_CACHE': 'default',
    },
}
