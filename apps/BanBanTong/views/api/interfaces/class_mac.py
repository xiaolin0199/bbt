#!/usr/bin/env python
# coding=utf-8
import datetime
import hashlib
import json
import logging
import traceback
from django.conf import settings
from django.core.cache import cache
from BanBanTong.db import models
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import simplecache
from BanBanTong.utils.get_cache_timeout import get_timeout
DEBUG = settings.DEBUG

logger = logging.getLogger(__name__)


def set_active_status(request):
    '''下级服务器发送班级在线状态'''
    key = request.POST.get('key')
    data = request.POST.get('data', '{}')
    if not key:
        return create_failure_dict(msg=u'获取密钥失败！')
    try:
        models.Node.objects.get(communicate_key=key)
    except models.Node.DoesNotExist:
        return create_failure_dict(msg='错误的key')
    except Exception as e:
        return create_failure_dict(msg='错误的key', debug=str(e))
    res = json.loads(data)
    for k in res.keys():
        cache.set(k, res[k], get_timeout(k, 90))
    return create_success_dict()

#


def user_login(request):
    '''管理员登录进行班级申报'''
    if models.Setting.getvalue('server_type') != 'school':
        return create_failure_dict()

    username = request.GET.get('username')
    password = request.GET.get('password')
    if not (username and password):
        return create_failure_dict(msg=u'请输入用户名/密码')

    if username not in settings.ADMIN_USERS:
        return create_failure_dict(msg=u'只允许管理员用户使用此功能')

    try:
        passhash = hashlib.sha1(password).hexdigest()
        obj = models.User.objects.get(username=username, password=passhash)
        if obj.status == 'suspended':
            return create_failure_dict(msg=u'用户已停用！')
    except models.User.DoesNotExist:
        return create_failure_dict(msg=u'错误的用户名或密码！')
    except Exception as e:
        return create_failure_dict(msg=u'错误的用户名或密码！', debug=str(e))

    terms = models.Term.get_current_term_list()
    if not terms:
        return create_failure_dict(msg=u'无可用学年学期！')

    # 默认返回的是(当前/下一个)学年学期的普通班级信息
    objs = models.Class.objects.exclude(grade__number=13)
    objs = objs.filter(classmacv2__isnull=True, grade__term=terms[0]).order_by('grade__number', 'number')
    objs = objs.values('grade__uuid', 'grade__name', 'uuid', 'name')

    g = {}
    for c in objs:
        if c['grade__uuid'] not in g:
            g[c['grade__uuid']] = {
                'uuid': c['grade__uuid'],
                'name': c['grade__name'],
                'classes': []
            }
        g[c['grade__uuid']]['classes'].append({
            'uuid': c['uuid'],
            'name': c['name']
        })

    grades = []
    for key in g:
        grades.append(g[key])
    s = '%s-%s' % (username, str(datetime.datetime.now()))
    token = hashlib.sha1(s).hexdigest()
    models.Token.objects.create(token_type='user_login', value=token)
    return create_success_dict(data={'grades': grades, 'token': token})

#


def get_mac_status(request, *args, **kwargs):
    '''从MAC地址查询班级申报状态'''
    if models.Setting.getvalue('server_type') != 'school':
        return create_failure_dict()
    terms = models.Term.get_current_term_list()
    if not terms:
        return create_failure_dict(msg=u'当前时间不在任何学期内')

    mac = request.GET.get('mac', '').strip()
    ip = request.META['REMOTE_ADDR']
    data = {
        'reported': False,
        'computerclass': False,
        'class_uuid': None,
        'grade_uuid': None
    }

    if not mac:
        return create_failure_dict(msg=u'客户端MAC获取失败.')
    try:
        o = models.ClassMacV2.objects.get(
            mac=mac,
            class_uuid__grade__term__in=terms
        )
        if o.ip != ip:
            o.ip = ip
            o.save()
        data['reported'] = True
        data['class_uuid'] = o.class_uuid.uuid
        data['grade_uuid'] = o.class_uuid.grade.uuid
        data['computerclass'] = (o.class_uuid.grade.number == 13)
    except models.ClassMacV2.DoesNotExist:
        simplecache.set_class_noreport_heartbeat_ip(ip)
    except Exception as e:
        logger.exception('')
        return create_failure_dict(data=data, msg=u'客户端状态获取失败', debug=str(e))
    return create_success_dict(data=data)

#


def report_mac(request, *args, **kwargs):
    '''申报班级MAC'''
    if models.Setting.getvalue('server_type') != 'school':
        return create_failure_dict(msg=u'客户端需要连接校级服务器')
    token = request.GET.get('token')
    mac = request.GET.get('mac')
    grade_uuid = request.GET.get('grade_uuid')
    class_uuid = request.GET.get('class_uuid')
    if not (token and mac and grade_uuid and class_uuid):
        return create_failure_dict(msg=u'信息不完整')

    try:
        obj = models.Token.objects.get(token_type='user_login', value=token)
    except Exception as e:
        return create_failure_dict(msg=u'错误的token！', debug=str(e))

    terms = models.Term.get_current_term_list()
    if not terms:
        return create_failure_dict(msg=u'尚未设置当前学期')

    if models.ClassMacV2.objects.filter(
            class_uuid__grade__term=terms[0], mac=mac).exists():
        return create_failure_dict(msg=u'该客户端已被申报！')

    try:
        g = models.Grade.objects.get(uuid=grade_uuid, term=terms[0])
        c = models.Class.objects.get(uuid=class_uuid, grade=g)
        if c.classmacv2_set.count() > 0:
            return create_failure_dict(msg=u'该班级已被申报！')
        models.ClassMacV2(class_uuid=c, mac=mac).save(force_insert=True)
        obj.delete()
    except Exception as e:
        if DEBUG:
            traceback.print_exc()
        return create_failure_dict(msg=str(e))
    return create_success_dict()
