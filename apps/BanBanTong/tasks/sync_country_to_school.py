# coding=utf-8
import base64
import bz2
import json
import logging
import urllib
import urllib2
from django.core import serializers
from django.db.models import Max
from BanBanTong.db import models


class Task(object):
    '''校级服务器定期执行，向县级服务器抓取需要下发的内容，例如教学大纲'''
    run_period = 60 * 10
    logger = logging.getLogger(__name__)

    def _download_data(self, host, port, key):
        '''向县级服务器发送当前的最大id，获取之后的新增数据'''
        q = models.CountryToSchoolSyncLog.objects.aggregate(Max('created_at'))
        max_created_at = q['created_at__max']
        if not max_created_at:
            max_created_at = 0
        url = "http://%s:%s/api/sync/country-to-school/" % (host, port)
        post_data = {'key': key, 'max_created_at': max_created_at}
        try:
            req = urllib2.urlopen(url, urllib.urlencode(post_data))
        except:
            return
        try:
            ret = req.read()
            req.fp._sock.recv = None
            ret = json.loads(ret)
            if ret['status'] == 'failure':
                return
            data = bz2.decompress(base64.b64decode(ret['data']))
            for line in data.split('\n'):
                try:
                    for obj in serializers.deserialize('json', line):
                        obj.object.save()
                except serializers.base.DeserializationError:
                    pass
        except:
            self.logger.exception('')

    def _save_data(self):
        q = models.CountryToSchoolSyncLog.objects.filter(used=False)
        q = q.order_by('created_at')
        for i in q:
            models.SyncLogPack.unpack_log(i.operation_type, i.operation_content)
            i.used = True
            i.save()

    def __init__(self):
        if models.Setting.getvalue('installed') != 'True':
            return
        if models.Setting.getvalue('server_type') != 'school':
            return
        host = models.Setting.getvalue('sync_server_host')
        port = models.Setting.getvalue('sync_server_port')
        key = models.Setting.getvalue('sync_server_key')
        if host and port and key:
            pass
        else:
            return

        self._download_data(host, port, key)
        self._save_data()
