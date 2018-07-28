# coding=utf-8
import os
import json
import logging
import datetime
import hashlib
from django.core.management.base import BaseCommand
from BanBanTong import constants
from BanBanTong.db import models
from django.conf import settings
DEBUG = settings.DEBUG
del settings

logger = logging.getLogger(__name__)


def generaotr(node):
    try:
        obj = models.Group.objects.get(name=node.name)
        school = obj
    except:
        logger.exception('')
        return

    lst = [
        {"pk": models._make_uuid(), "model": "db.setting", "fields": {"name": 'server_type', "value": 'school'}},
        {"pk": models._make_uuid(), "model": "db.setting", "fields": {"name": 'install_step', "value": -1}},
        {"pk": models._make_uuid(), "model": "db.setting", "fields": {"name": 'installed', "value": True}}
    ]

    while obj:
        lst.append({
            "pk": obj.pk,
            "model": "db.setting",
            "fields": {
                "name": obj.group_type,
                "value": obj.name
            }
        })
        obj = obj.parent

    user = [{
        "pk": models._make_uuid(), "model": "db.user", "fields": {
            "username": "admin", "qq": "", "remark": u"系统管理员",
            "realname": "", "level": "school", "mobile": "",
            "created_at": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "sex": "", "status": "active", "role": "", "email": "",
            "password": "d033e22ae348aeb5660fc2140aec35850c4da997"
        }}, {
        "pk": models._make_uuid(), "model": "db.user", "fields": {
            "username": "oseasy", "qq": "", "remark": u"系统管理员",
            "realname": "", "level": "school", "mobile": "",
            "created_at": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "sex": "", "status": "active", "role": "", "email": "",
            "password": str(hashlib.sha1('0512').hexdigest())
        }}, ]
    data = json.dumps(lst) + '\n'
    user = json.dumps(user) + '\n'
    data += user

    f = os.path.join(constants.CACHE_TMP_ROOT, str(node.pk) + '.setting')
    if os.path.exists(f):
        print 'already exists:', f
    else:
        print 'create: %s' % f
        f = open(f, 'w')
        f.write(data)
        f.close()
        logger.debug('create %s.setting, content:%s' % (node.pk, data))

    f = os.path.join(constants.CACHE_TMP_ROOT, str(node.pk) + '.node')
    if os.path.exists(f):
        print 'already exists:', f
    else:
        print 'create: %s' % f
        f = open(f, 'w')
        f.write(str(school.pk))
        f.close()
        logger.debug('create %s.node, content:%s' % (node.pk, school.pk))


class Command(BaseCommand):
    """
        创建缺失的.node和.setting文件的脚本
        调用命令 python manage.py generate_node_setting_cachefiles
    """

    def traveller(self, *args, **kwargs):
        nodes = models.Node.objects.all()
        for o in nodes[:]:
            generaotr(o)

    def handle(self, *args, **options):
        self.traveller()
        print 'finished.'


def run_by_http(request):
    from django.http import HttpResponse
    cmd = Command()
    cmd.handle()
    return HttpResponse('创建缺失的.node文件完毕,<a href="/">返回</a>')
