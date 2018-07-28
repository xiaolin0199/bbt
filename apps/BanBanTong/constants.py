#!/usr/bin/env python
# coding=utf-8
'''
    C:\Program Files\OsEasy\DADS:
        settings.ini:                                   DADS_SETTING_FILE 升级URL
        WebServer\
            DadsServer\
                Apache24\
                app\
                    settings.ini:   MySQL               BANBANTONG_SETTINGS_FILE
                    version.ini:                        BANBANTONG_VERSION_FILE
                    memcached.ini:  memcached
                    mongo.ini:      mongodb
                    websocket.ini:  websocket server
                    BanBanTong\                         BANBANTONG_BASE_PATH
                        constants.py
                        settings.py
                    files\
                        edufiles\                       EDU_UPDATES_PATH
                        logs\                           LOG_PATH
                            vnc_tokens\                   VNC_INI_PATH
                        public\
                            DadsTerminalSetup.exe
                            OeCreatekey.exe
                        templates\
                        tmp\                            TMP_ROOT
                            backup\                       BACKUP_TMP_ROOT
                            cache\                        CACHE_TMP_ROOT
                                export\
                                static\
                            upload\                       UPLOAD_TMP_ROOT
                        updates\                        UPDATES_PATH
                memcached\
                nodejs\
                Python27\
            mysql\
                bin\
                    mysqldump.exe
    以上是主要目录结构
'''
import os
from conf import CONF as conf
from django.conf import settings

BANBANTONG_BASE_PATH = settings.BASE_DIR
DADS_SETTING_FILE = os.path.join(BANBANTONG_BASE_PATH, '..', '..', '..', 'settings.ini')

BANBANTONG_SETTINGS_FILE = os.path.join(BANBANTONG_BASE_PATH, 'settings.ini')
BANBANTONG_VERSION_FILE = os.path.join(BANBANTONG_BASE_PATH, 'version.ini')

LOG_PATH = conf.log_path

VNC_INI_PATH = os.path.join(LOG_PATH, 'vnc_tokens')
if not os.path.exists(VNC_INI_PATH):
    os.mkdir(VNC_INI_PATH)

TMP_ROOT = conf.tmp_dir
if not os.path.exists(TMP_ROOT):
    os.mkdir(TMP_ROOT)
BACKUP_TMP_ROOT = os.path.join(TMP_ROOT, 'backup')
if not os.path.exists(BACKUP_TMP_ROOT):
    os.mkdir(BACKUP_TMP_ROOT)
CACHE_TMP_ROOT = os.path.join(TMP_ROOT, 'cache')
if not os.path.exists(CACHE_TMP_ROOT):
    os.mkdir(CACHE_TMP_ROOT)
if not os.path.exists(os.path.join(CACHE_TMP_ROOT, 'static')):
    os.mkdir(os.path.join(CACHE_TMP_ROOT, 'static'))
if not os.path.exists(os.path.join(CACHE_TMP_ROOT, 'export')):
    os.mkdir(os.path.join(CACHE_TMP_ROOT, 'export'))
# UPLOAD_TMP_ROOT = os.path.join(TMP_ROOT, 'upload')
# if not os.path.exists(UPLOAD_TMP_ROOT):
#     os.mkdir(UPLOAD_TMP_ROOT)
MEDIA_ROOT = conf.media_root
if not os.path.exists(MEDIA_ROOT):
    os.mkdir(MEDIA_ROOT)
UPLOAD_TMP_ROOT = 'upload'


UPDATES_PATH = conf.updates_dir
if not os.path.exists(UPDATES_PATH):
    os.mkdir(UPDATES_PATH)
EDU_UPDATES_PATH = conf.edufiles_dir
if not os.path.exists(EDU_UPDATES_PATH):
    os.mkdir(EDU_UPDATES_PATH)

BANBANTONG_DB_HOST = conf.db.host
BANBANTONG_DB_PORT = conf.db.port
BANBANTONG_DB_USER = conf.db.user
BANBANTONG_DB_PASSWORD = conf.db.password
BANBANTONG_DB_NAME = conf.db.name
BANBANTONG_DB_AUTO_OPTIMIZE = conf.db.auto_optimize
BANBANTONG_DB_AUTO_OPTIMIZE_PERIOD = conf.db.auto_optimize_days

BANBANTONG_DEBUG = conf.debug
BANBANTONG_NTP_CRON = conf.server.ntp_cron
RESOURCE_PLATFORM_HOST = 'http://%s' % conf.server.rp_host
VNC_PROXY_PORT = conf.server.vnc_proxy_port
BANBANTONG_ZMQ_PORT = conf.server.zmq_port
AUTO_LESSONSCHEDULE = conf.server.auto_lessonschedule
BANBANTONG_DEFAULT_EXPORT_TYPE = conf.server.default_export_type

# 开发环境下的配置项
NO_MODIFY_UPDATE_PATH = conf.server.no_modify_update_path  # 安装不配置升级路径
MYSQL_PATH = conf.server.mysql_path  # 自定义mysql_path
TASK_MAX_RUN_PERIOD = conf.server.task_max_run_period
ACTIVATE_DIRECTLY = conf.server.activate_directly  # 开发环境下授权激活验证直接通过


# mongo
BANBANTONG_USE_MONGODB = conf.mongodb.ebable

# websocket server
WEBSOCKET_LOG_TO_FILE = False


# 用于解密从服务器获取的信息.
TOKENURL = 'http://license.os-easy.com/token'
ACQUIREURL = 'http://license.os-easy.com/acquire'
AES_KEY = 'b6lUu-Ws)4aitz@7S1Ats17f$qA$RtQC'
AES_SALT = 'b6lUu-Ws)4aitz@7S1Ats17f$qA$RtQC'
ACTIVATE_USER = 'banbantong'
