# coding=utf-8
import json
import logging
import urllib
import urllib2
from BanBanTong.db import models
from BanBanTong.utils import create_failure_dict


logger = logging.getLogger(__name__)


def get_group(request):
    host = models.Setting.getvalue('sync_server_host')
    port = models.Setting.getvalue('sync_server_port')
    # key
    key = models.Setting.getvalue('sync_server_key')
    url = 'http://%s:%s/api/sync-server/get-group/?key=%s' % (host, port, key)
    try:
        conn = urllib2.urlopen(url, timeout=5)
        ret = conn.read()
        ret = json.loads(ret)
        return ret
    except urllib2.URLError:
        return create_failure_dict(msg='连接上级服务器失败')
    except:
        logger.exception('')
        return create_failure_dict()


def set(request, *args, **kwargs):
    if request.method == 'POST':
        host = request.POST.get('host')
        port = request.POST.get('port')
        key = request.POST.get('key')
        obj, c = models.Setting.objects.get_or_create(name='sync_server_host')
        obj.value = host
        obj.save()
        obj, c = models.Setting.objects.get_or_create(name='sync_server_port')
        obj.value = port
        obj.save()
        obj, c = models.Setting.objects.get_or_create(name='sync_server_key')
        obj.value = key
        obj.save()
        url = 'http://%s:%s/api/sync-server/check-data/' % (host, port)
        data = {'key': key}
        try:
            conn = urllib2.urlopen(url, urllib.urlencode(data), timeout=5)
            ret = conn.read()
            ret = json.loads(ret)
            if ret:
                node_id = models.Setting.get_node_id_from_top(host, port, key)
                if node_id:
                    obj, c = models.Setting.objects.get_or_create(name='sync_node_id')
                    obj.value = node_id
                    obj.save()
                else:
                    logger.exception('')
                    return create_failure_dict(msg='获取本服务器在上级服务的NODE ID失败')

            return ret
        except urllib2.URLError:
            return create_failure_dict(msg='连接上级服务器失败')
        except:
            logger.exception('')
            return create_failure_dict()


def verify(request, *args, **kwargs):
    '''下级服务器测试连接上级'''
    if request.method == 'POST':
        host = request.POST.get('host')
        port = request.POST.get('port')
        key = request.POST.get('key')

        url = 'http://%s:%s/api/sync-server/verify/' % (host, port)
        data = {'key': key}
        try:
            conn = urllib2.urlopen(url, urllib.urlencode(data), timeout=5)
            ret = conn.read()
            ret = json.loads(ret)
            return ret
        except urllib2.URLError, e:
            return create_failure_dict(msg='连接上级服务器失败', debug=str(e))
        except Exception as e:
            logger.exception('')
            return create_failure_dict(debug=str(e))
