#!/usr/bin/env python
# coding=utf-8
import logging
import os
import qiniu
import qiniu.config
import time
from BanBanTong.db import models

logger = logging.getLogger(__name__)


def generate_bucket_name():
    '''
        生成upyun的oebbt-nnnnnn格式的bucket名字
    '''
    if models.Setting.getvalue('server_type') not in ('country', 'school'):
        return ''
    province_name = models.Setting.getvalue('province')
    city_name = models.Setting.getvalue('city')
    country_name = models.Setting.getvalue('country')
    province = models.GroupTB.objects.get(name=province_name)
    city = models.GroupTB.objects.get(name=city_name, parent=province)
    obj = models.GroupTB.objects.get(name=country_name, parent=city)
    return 'oebbt-' + str(obj.group_id)


def qiniu_upload_content(content, bucket_name, key, mime_type):
    '''
        把content内容上传为七牛文件
        content: str
        bucket_name: 七牛的bucket
        key: 七牛的文件名
    '''
    ACCESS_KEY = 'yEo5y1hDiekGBTYBflQmwTcuLa-PR9WKQJfkimFo'
    SECRET_KEY = 'wzDziYgcU5qaUAlzV_T0k5ZaZrs9gjKNT5Fl4g3o'
    q = qiniu.Auth(ACCESS_KEY, SECRET_KEY)
    token = q.upload_token(bucket_name, key)
    ret, info = qiniu.put_data(token, key, content, mime_type=mime_type)
    logger.debug('ret: %s', ret)
    logger.debug('info: %s', info)


def qiniu_upload_filepath(filepath, bucket_name, key, mime_type):
    '''
        把位于filepath的文件上传到七牛
        filepath: str
        bucket_name: 七牛的bucket
        key: 七牛的文件名
    '''
    ACCESS_KEY = 'yEo5y1hDiekGBTYBflQmwTcuLa-PR9WKQJfkimFo'
    SECRET_KEY = 'wzDziYgcU5qaUAlzV_T0k5ZaZrs9gjKNT5Fl4g3o'
    q = qiniu.Auth(ACCESS_KEY, SECRET_KEY)
    token = q.upload_token(bucket_name, key)
    progress_handler = lambda progress, total: progress
    ret, info = qiniu.put_file(token, key, filepath, mime_type=mime_type,
                               progress_handler=progress_handler)
    logger.debug('ret: %s', ret)
    logger.debug('info: %s', info)


def qiniu_upload_fileobj(obj, bucket_name, ext=None):
    '''
        把request.FILES里的文件对象上传到七牛
        obj: 文件对象
        bucket_name: 七牛的bucket
        ext: 为七牛的key追加的扩展名，包含.符号
    '''
    ACCESS_KEY = 'yEo5y1hDiekGBTYBflQmwTcuLa-PR9WKQJfkimFo'
    SECRET_KEY = 'wzDziYgcU5qaUAlzV_T0k5ZaZrs9gjKNT5Fl4g3o'
    if not ext:
        ext = os.path.splitext(obj.name)[1]
    key = '%.06f%s' % (time.time(), ext)
    q = qiniu.Auth(ACCESS_KEY, SECRET_KEY)
    token = q.upload_token(bucket_name, key)
    data = ''
    for chunk in obj.chunks():
        data += chunk
    ret, info = qiniu.put_data(token, key, data, mime_type=obj.content_type)
    if ret:
        return key
    else:
        logger.debug('qiniu upload err: %s', info)
