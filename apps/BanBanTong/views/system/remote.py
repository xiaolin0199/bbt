# coding=utf-8
import base64
import bz2
import json
import logging
import os
import urllib
import urllib2
from django.core.cache import cache
from django.core import serializers
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.views.system.install import _modify_update_path
from BanBanTong.views.system.install import _package_client_file
from BanBanTong.views.system.install import _truncate_tables

logger = logging.getLogger(__name__)


def check_data(request, *args, **kwargs):
    if request.method == 'GET':
        host = models.Setting.getvalue('sync_server_host')
        port = models.Setting.getvalue('sync_server_port')
        key = models.Setting.getvalue('sync_server_key')
        if not host or not port or not key:
            return create_failure_dict(msg='未设置上级服务器')
        url = 'http://%s:%s/api/remote/check-data/' % (host, port)
        data = {'key': key}
        try:
            conn = urllib2.urlopen(url, urllib.urlencode(data), timeout=5)
            ret = conn.read()
            ret = json.loads(ret)
            return ret
        except urllib2.URLError:
            return create_failure_dict(msg='连接上级服务器失败')
        except:
            logger.exception('')
            return create_failure_dict()


def _restore_syllabus(syllabus):
    '''首先保存CountryToSchoolSyncLog，然后生成Syllabus*'''
    try:
        for obj in serializers.deserialize('json', syllabus):
            obj.object.save()
    except:
        logger.exception('')
    q = models.CountryToSchoolSyncLog.objects.filter(used=False)
    q = q.order_by('created_at')
    for i in q:
        models.SyncLogPack.unpack_log(i.operation_type, i.operation_content)
        i.used = True
        i.save()


def _setting():
    q = models.Setting.objects.all()
    data = serializers.serialize('json', q)
    return data

# 下级服务器从上级抓取数据进行恢复


def restore(request):
    if request.method == 'POST':
        host = request.POST.get('host')
        port = request.POST.get('port')
        key = request.POST.get('key')
        url = 'http://%s:%s/api/restore/' % (host, port)
        data = {'key': key}
        cache.set('restore-status', 'start')
        try:
            logger.debug('before restore: %s', _setting())
            conn = urllib2.urlopen(url, urllib.urlencode(data))
            ret = conn.read()
            ret = json.loads(ret)
            if ret['status'] == 'failure':
                logger.debug('upstream restore failure: %s', ret)
                return ret
            # 上级返回的结果是压缩之后再base64的内容
            cache.set('restore-status', 'download', None)
            f = open(os.path.join(constants.LOG_PATH,
                                  'restore.log'), 'w')
            syllabus = bz2.decompress(base64.b64decode(ret['syllabus']))
            f.write(syllabus + '\n')
            data = base64.b64decode(ret['data'])
            data = bz2.decompress(data)
            f.write(data)
            f.close()
            lines = data.split('\n')
            cache.set('restore-status', 'import', None)
            _truncate_tables()
            logger.debug('after truncate tables: %s', _setting())
            models.Setting.objects.all().exclude(name__in=('migration_step',
                                                           'host_new')).delete()
            logger.debug('after settings all delete: %s', _setting())
            _restore_syllabus(syllabus)
            total = len(lines)
            cache.set('restore-total', '%d' % total, None)
            i = 0
            for line in lines:
                if len(line) < 2:
                    continue
                models.SyncLogPack.unpack_log('add', line)
                i += 1
                cache.set('restore-count', '%d' % i)
            logger.debug('after unpack_log: %s', _setting())
            province = models.Group.objects.get(group_type='province').name
            city = ''
            country = ''
            server_type = models.Setting.getvalue('server_type')
            if server_type != 'province':
                city = models.Group.objects.get(group_type='city').name
                if server_type != 'city':
                    try:
                        country = models.Group.objects.get(group_type='country')
                        country = country.name
                    except:
                        # 市直属，没有区县
                        pass
            _modify_update_path(province, city, country)
            if models.Setting.getvalue('server_type') == 'school':
                try:
                    obj = models.Setting.objects.get(name='host_new')
                    obj2 = models.Setting.objects.get(name='host')
                    obj2.value = obj.value
                    obj2.save()
                    obj.delete()
                except:
                    logger.exception('')
                logger.debug('before package client file: %s', _setting())
                _package_client_file()
                logger.debug('after package client file: %s', _setting())
            for obj in models.LessonTeacher.objects.all():
                models.LessonTeacher.calculate_total_teachers(obj)
            cache.set('restore-status', 'complete')
            return create_success_dict(msg='数据恢复成功')
        except:
            logger.exception('')
            return create_failure_dict()


# 下级服务器测试连接上级
def restore_test(request, *args, **kwargs):
    if request.method == 'POST':
        host = request.POST.get('host')
        port = request.POST.get('port')
        key = request.POST.get('key')

        url = 'http://%s:%s/api/restore/test/' % (host, port)
        data = {'key': key}
        try:
            conn = urllib2.urlopen(url, urllib.urlencode(data), timeout=5)
            ret = conn.read()
            ret = json.loads(ret)
            return ret
        except urllib2.URLError:
            return create_failure_dict(msg='连接上级服务器失败')
        except:
            logger.exception('')
            return create_failure_dict()


def status(request):
    c = cache.get('restore-status')
    if not c:
        return create_failure_dict(msg='数据恢复尚未准备完毕')
    count = cache.get('restore-count')
    total = cache.get('restore-total')
    if count:
        count = int(count)
    else:
        count = 0
    if total:
        total = int(total)
    else:
        total = 0
    return create_success_dict(progress=c, count=count, total=total)
