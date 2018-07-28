# coding=utf-8
import base64
import bz2
import datetime
import hashlib
import json
import logging
import os
import traceback
from django.core.cache import cache
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils.get_cache_timeout import get_timeout

logger = logging.getLogger(__name__)


def clear_expired_node_communicate_tokens():
    expire = datetime.datetime.now() - datetime.timedelta(hours=1)
    models.Token.objects.filter(token_type='node_sync',
                                created_at__lt=expire).delete()


def last_active(request):
    if request.method == 'POST':
        try:
            if models.Setting.getvalue('server_type') == 'school':
                return
            token = request.POST.get('token')
            data = request.POST.get('data')
        except:
            logger.exception('')
        try:
            models.Token.objects.get(token_type='node_sync', value=token)
            d = json.loads(data)
            for key in d:
                cache.set(key, d[key], get_timeout(key, 360))
            return create_success_dict()
        except:
            traceback.print_exc()
            return create_failure_dict(msg='错误的token！')


def login_status(request):
    if models.Setting.getvalue('server_type') not in ['country', 'city']:
        return
    if request.method == 'POST':
        try:
            token = request.POST.get('token')
            data = request.POST.get('data')
        except:
            logger.exception('')
        try:
            models.Token.objects.get(token_type='node_sync', value=token)
            d = json.loads(data)
            for key in d:
                cache.set(key, d[key], get_timeout(key, None))
            return create_success_dict()
        except:
            traceback.print_exc()
            return create_failure_dict(msg='错误的token！')


def _backup_login_data(request):
    setting = request.POST.get('setting')
    if isinstance(setting, list):
        setting = setting[0]
    role = request.POST.get('role')
    if isinstance(role, list):
        role = role[0]
    user = request.POST.get('user')
    if isinstance(user, list):
        user = user[0]
    roleprivilege = request.POST.get('roleprivilege')
    if isinstance(roleprivilege, list):
        roleprivilege = roleprivilege[0]
    usbkeyteacher = request.POST.get('usbkeyteacher')
    if isinstance(usbkeyteacher, list):
        usbkeyteacher = usbkeyteacher[0]
    node = request.POST.get('node')
    if isinstance(node, list):
        node = node[0]
    l = [setting, role, user, roleprivilege, usbkeyteacher, node]
    return '\n'.join(l)


def login(request, *args, **kwargs):
    if request.method == 'POST':
        if models.Setting.getvalue('server_type') == 'school':
            return
        communicate_key = request.POST.get('communicate_key')
        name = request.POST.get('name')
        db_version = request.POST.get('db_version')
        school_uuid = request.POST.get('school_uuid')
        max_sync_id = request.POST.get('max_sync_id')
        if isinstance(communicate_key, list):
            communicate_key = communicate_key[0]
        if isinstance(name, list):
            name = name[0]
        if isinstance(db_version, list):
            db_version = db_version[0]
        if isinstance(school_uuid, list):
            school_uuid = school_uuid[0]
        if isinstance(max_sync_id, list):
            max_sync_id = max_sync_id[0]
        try:
            node = models.Node.objects.get(communicate_key=communicate_key)
        except:
            return create_failure_dict(msg='错误的服务器密钥！')
        if db_version:
            node.db_version = int(db_version)
            node.save()
        if school_uuid:
            tmp = 'node_%d_school_uuid' % node.id
            s, c = models.Setting.objects.get_or_create(name=tmp)
            if c:
                s.value = school_uuid
                s.save()
            elif s.value != school_uuid:
                # 如果校级服务器的uuid核对错误，说明校级可能重装过，就设置sync_status为-1
                if node.sync_status == 0:
                    logger.debug('client_sync.login change: %s - %s status to -1' % (node.name, node.key))
                    # print 'client_sync.login change: %s - %s status to -1' % (node.name, node.key)
                    node.sync_status = -1
                    node.save()
                return create_failure_dict(msg='密钥与服务器身份不匹配！')
            elif s.value == school_uuid and node.sync_status == -1:
                # 如果校级服务器的uuid核对正确，就恢复同步状态为0
                node.sync_status = 0
                logger.debug('client_sync.login reset: %s - %s status from -1 to 0' % (node.name, node.key))
                node.save()
        if max_sync_id:
            if node.last_upload_id > max_sync_id:
                # 上级的数据比下级还多，说明下级丢失了一部分同步数据
                # 例如：下级用Ghost做了备份/恢复
                node.sync_status = -2
                node.save()
                return create_failure_dict(msg='检测到下级服务器数据丢失！')
        if name:
            node.name = name
        data = _backup_login_data(request)
        f = open(os.path.join(constants.CACHE_TMP_ROOT,
                              str(node.id) + '.setting'), 'w')
        f.write(data)
        f.close()
        now = datetime.datetime.now()
        node.host = request.META['REMOTE_ADDR']
        node.last_active_time = now
        node.save()

        clear_expired_node_communicate_tokens()
        t, c = models.Token.objects.get_or_create(token_type='node_sync',
                                                  info=str(node.pk))
        if not t.value:
            token_value = '%d-%s' % (node.pk, str(now))
            token_value = hashlib.sha1(token_value).hexdigest()
            t.value = token_value
            t.save()
        ret = {'token': t.value}
        return create_success_dict(data=ret)


def school(request, *args, **kwargs):
    if request.method == 'POST':
        if models.Setting.getvalue('server_type') == 'school':
            return
        token = request.POST.get('token')
        school_uuid = request.POST.get('school_uuid')
        try:
            t = models.Token.objects.get(token_type='node_sync',
                                         value=token)
            node = models.Node.objects.get(id=int(t.info))
            tmp_file = os.path.join(constants.CACHE_TMP_ROOT,
                                    str(node.id) + '.node')
            f = open(tmp_file, 'w')
            for uu in school_uuid.split(','):
                f.write(uu + '\n')
            f.close()
            obj, c = models.Setting.objects.get_or_create(name='sync_upload_school')
            obj.value = 'True'
            obj.save()
            return create_success_dict()
        except:
            traceback.print_exc()
            return create_failure_dict()


def status(request, *args, **kwargs):
    if request.method == 'POST':
        if models.Setting.getvalue('server_type') == 'school':
            return
        token = request.POST.get('token')
        try:
            t = models.Token.objects.get(token_type='node_sync',
                                         value=token)
            node = models.Node.objects.get(id=int(t.info))
            data = {'last_upload_id': node.last_upload_id}
            node_file = os.path.join(constants.CACHE_TMP_ROOT,
                                     str(node.id) + '.node')
            if not os.path.isfile(node_file):
                data['school'] = True
            node.last_active_time = datetime.datetime.now()
            node.save()
            return create_success_dict(data=data)
        except:
            traceback.print_exc()
            return create_failure_dict()


def upload(request, *args, **kwargs):
    try:
        if models.Setting.getvalue('server_type') == 'school':
            return
        clear_expired_node_communicate_tokens()
        token_name = kwargs.get('token')
    except:
        logger.exception('')
    if token_name:
        try:
            token = models.Token.objects.get(value=token_name,
                                             token_type='node_sync')
        except:
            return create_failure_dict(msg='错误的token！')
        try:
            node = models.Node.objects.get(pk=int(token.info))
            node.last_active_time = datetime.datetime.now()
            node.save()
        except:
            return create_failure_dict(msg='无效的token！')
        if request.POST.get('empty'):
            return True

        logger.debug('get upload from %s %s', node.pk, node.name)
        try:
            _do_upload(request, node, *args, **kwargs)
        except:
            logger.exception('')
            return create_failure_dict()

    return create_success_dict()


def _do_upload(request, node, *args, **kwargs):
    data = bz2.decompress(base64.b64decode(request.POST.get('data')))
    lines = data.split('\n')
    for line in lines:
        if line:
            record = json.loads(line)
            created_at = record['created_at']
            operation_type = record['operation_type']
            operation_content = record['operation_content']
            models.SyncLogPack.unpack_log(operation_type, operation_content)
            node.last_upload_id = created_at
            node.last_upload_time = datetime.datetime.now()
            node.save()
