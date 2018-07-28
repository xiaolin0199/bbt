# coding=utf-8
import datetime
import json
import logging
import upyun
import urllib2
from django.core.cache import cache
from django.utils.dateparse import parse_date
from BanBanTong.db import models
from BanBanTong.utils import cloud_service
from BanBanTong.utils.get_cache_timeout import get_timeout


def _delete_upyun_folder(up, name):
    res = up.getlist(name)
    for i in res:
        if i['type'] == 'F':
            _delete_upyun_folder(up, name + i['name'] + '/')
        else:
            up.delete(name + i['name'])
    up.delete(name)


class Task(object):
    '''
    1. 校级服务器从县级获取upyun设置
    2. 校级服务器删除过期的实时桌面预览
    3. 县级服务器定期清除超过desktop-preview-days-to-keep的upyun文件
    '''
    run_period = 60
    logger = logging.getLogger(__name__)

    def _get_set_value(self, name, value):
        obj, c = models.Setting.objects.get_or_create(name=name)
        if obj.value != str(value):
            obj.value = str(value)
            obj.save()

    def _delete_expired_records(self):
        '''根据QC 772，删掉超过14分钟的实时预览'''
        s = datetime.datetime.now() - datetime.timedelta(minutes=14)
        q = models.DesktopGlobalPreview.objects.filter(pic__created_at__lt=s)
        q.delete()

    def _delete_cloud_service_files(self):
        today = datetime.date.today()
        buf = cache.get('cloud-service-clean-date')
        if buf and parse_date(buf) == today:
            # 今天已经运行过一次，不用再运行了
            return
        value = models.Setting.getvalue('desktop-preview-days-to-keep')
        try:
            days = int(value)
        except:
            return
        username = models.Setting.getvalue('desktop-preview-username')
        password = models.Setting.getvalue('desktop-preview-password')
        if not username or not password:
            return
        bucket = cloud_service.generate_bucket_name()
        up = upyun.UpYun(bucket, username, password, endpoint=upyun.ED_AUTO)
        res = up.getlist('/')
        for i in res:
            if i['type'] != 'F':
                continue
            folder_date = parse_date(i['name'])
            if folder_date is None:
                continue
            if (today - folder_date).days > days:
                _delete_upyun_folder(up, '/' + i['name'] + '/')
        cache.set('cloud-service-clean-date', str(today), get_timeout('cloud-service-clean-date', None))

    def __init__(self):
        try:
            if models.Setting.getvalue('server_type') == 'country':
                self._delete_cloud_service_files()
            if models.Setting.getvalue('server_type') != 'school':
                return
            host = models.Setting.getvalue('sync_server_host')
            port = models.Setting.getvalue('sync_server_port')
            if not host or not port:
                print 'DesktopPreviewCron: no host/port'
                return
            url = 'http://%s:%s/api/desktop-preview/get/' % (host, port)
            try:
                req = urllib2.urlopen(url)
            except:
                return
            ret = req.read()
            req.fp._sock.recv = None
            req.close()
            ret = json.loads(ret)
            if ret['status'] == 'success':
                interval = ret['data']['desktop-preview-interval']
                days = ret['data']['desktop-preview-days-to-keep']
                sp = ret['data']['cloud-service-provider']
                username = ret['data']['cloud-service-username']
                password = ret['data']['cloud-service-password']
            else:
                print 'DesktopPreviewCron: status not success'
                return
            self._get_set_value('desktop-preview-interval', interval)
            self._get_set_value('desktop-preview-days-to-keep', days)
            self._get_set_value('cloud-service-provider', sp)
            self._get_set_value('cloud-service-username', username)
            self._get_set_value('cloud-service-password', password)
            self._delete_expired_records()
        except:
            self.logger.exception('')
