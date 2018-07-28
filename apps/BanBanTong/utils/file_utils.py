#!/usr/bin/env python
# coding=utf-8
from django.conf import settings
import logging
import os
import zipfile
from BanBanTong.db import models

logger = logging.getLogger(__name__)


def package_client_file():
    '''
        校级服务器打包班级客户端，县级服务器打包教学点客户端
    '''
    host = models.Setting.getvalue('host')
    port = models.Setting.getvalue('port')
    server_type = models.Setting.getvalue('server_type')
    conf_file = os.path.join(settings.PUBLIC_ROOT, 'settings.ini')
    with open(conf_file, 'w') as f:
        f.write('[server]\nip=%s\nport=%s\nrequest_times=3' % (host, port))
    zip_file = os.path.join(settings.PUBLIC_ROOT, 'client.zip')
    z = zipfile.ZipFile(zip_file, 'w')
    z.write(conf_file, os.path.basename(conf_file))
    try:
        if server_type == 'school':
            exe = 'DadsTerminalSetup.exe'
        elif server_type == 'country':
            exe = 'EduClientSetup.exe'
        else:
            return
        client_file = os.path.join(settings.PUBLIC_ROOT, exe)
        z.write(client_file, os.path.basename(client_file))
    except:
        logger.exception('')
    z.close()
