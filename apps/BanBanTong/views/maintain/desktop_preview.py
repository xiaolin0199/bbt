#!/usr/bin/env python
# coding=utf-8
import base64
import ftplib
import os
import time
import traceback
import upyun
import uuid
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict

bucket = 'oe-test1'
data = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAT0'
    'lEQVQ4jWNgGAVUBRoMDAzvGRgYgvCoCYGq0cAmycXAwHCYgYHh'
    'Nw5DQqByh6FqsQIeHIYga+bB40KshpCkGZshJGtGNmQ/FJOseR'
    'SQAADkGBSp0UkGrgAAAABJRU5ErkJggg=='
)


def _upload_pic_http(host, username, password):
    # print 'testing http', host
    up = upyun.UpYun(bucket, username, password, timeout=5,
                     endpoint=host)
    path = '/diagnose/%.06f.png' % time.time()
    try:
        up.put(path, data)
    except Exception as e:
        return {'address': host, 'method': 'HTTP',
                'status': False, 'msg': str(e)}
    up.delete(path)
    return {'address': host, 'method': 'HTTP', 'status': True}


def _upload_pic_ftp(host, username, password):
    # print 'testing ftp', host
    try:
        ftp = ftplib.FTP(timeout=5)
        ftp.connect(host)
        ftp.login('%s/%s' % (username, bucket), password)
        ftp.mkd('diagnose')
        ftp.cwd('diagnose')
        filename = '%.06f.png' % time.time()
        cached_id = str(uuid.uuid1())
        tmp_file = os.path.join(constants.CACHE_TMP_ROOT, cached_id)
        f = open(tmp_file, 'wb')
        f.write(data)
        f.close()
        f = open(tmp_file, 'rb')
        ftp.storbinary('STOR %s' % filename, f)
        f.close()
        os.remove(tmp_file)
        ftp.delete(filename)
        ftp.quit()
    except Exception as e:
        traceback.print_exc()
        return {'address': host, 'method': 'FTP',
                'status': False, 'msg': str(e)}
    return {'address': host, 'method': 'FTP', 'status': True}


def network_diagnose(request):
    username = models.Setting.getvalue('cloud-service-username')
    password = models.Setting.getvalue('cloud-service-password')
    if not username or not password:
        return create_failure_dict(msg='未设置用户名/密码')
    records = []
    for host in (upyun.ED_AUTO, upyun.ED_CNC, upyun.ED_CTT, upyun.ED_TELECOM):
        records.append(_upload_pic_ftp(host, username, password))
        records.append(_upload_pic_http(host, username, password))
    return create_success_dict(data={'records': records})
