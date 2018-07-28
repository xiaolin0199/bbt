# coding=utf-8
import os
import bz2
import json
import base64
import time
import datetime
from BanBanTong import constants
from BanBanTong.db import models
from ws.dispatchers.sync import generaotr_node_setting_files
import ws.dbapi
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('key', help=u'连接密钥.')

    def handle(self, *args, **options):
        key = options.pop('key')
        start = time.time()
        node = models.Node.objects.get(communicate_key=key)
        generaotr_node_setting_files(node)

        f = open(os.path.join(constants.CACHE_TMP_ROOT, str(node.id) + '.node'))
        uuids = [line.strip('\r\n') for line in f]
        school = models.Group.objects.get(group_type='school', name=node.name)
        uuids.append(school.pk)

        data = ''
        count = 0

        _data, _count = ws.dbapi.backup_group(uuids)
        data += _data

        count += _count
        print u'# 4.1 打包学校的Group表数据', _count

        _data, _count = ws.dbapi.backup_teacher(uuids)
        data += _data
        count += _count
        print u'# 4.2 打包学校的授课教师数据', _count

        _data, _count = ws.dbapi.backup_assets(uuids)
        data += _data
        count += _count
        print u'# 4.3 打包学校的资产管理部分的数据', _count

        _data, _count = ws.dbapi.backup_class(uuids)
        data += _data
        count += _count
        print u'# 4.4 打包学校的年级班级的数据', _count

        _data, _count = ws.dbapi.backup_lesson(uuids)
        data += _data
        count += _count
        print u'# 4.5 打包学校的课程/节次/课表的数据', _count

        _data, _count = ws.dbapi.backup_loginlog(uuids)
        data += _data
        count += _count
        print u'# 4.6 打包学校的教师登录日志', _count

        # _data, _count = ws.dbapi.backup_absentlog(uuids)
        # data += _data
        # count += _count
        # print u'# 4.7 打包学校的未登录日志', _count

        _data, _count = ws.dbapi.backup_desktoppic(uuids)
        data += _data
        count += _count
        print u'# 4.8 打包学校的桌面截图日志', _count

        _data, _count = ws.dbapi.backup_courseware(uuids)
        data += _data
        count += _count
        print u'# 4.9 打包学校的教材大纲数据', _count

        _data, _count = ws.dbapi.backup_resource(uuids)
        data += _data
        count += _count
        print u'# 4.10 打包学校的课程资源数据', _count

        _data, _count = ws.dbapi.backup_setting(node)
        data += _data
        count += _count
        print u'# 4.11 打包学校的服务器配置数据', _count

        syllabus = models.CountryToSchoolSyncLog.pack_all_data()
        print u'# 4.12 打包同步数据'

        _data, _count = ws.dbapi.backup_machinetimeused(uuids)
        data += _data
        count += _count
        print u'# 4.13 打包机器时长数据', _count

        _data, _count = ws.dbapi.backup_activate_quota(node)
        data += _data
        count += _count
        print u'# 4.14 打包学校的授权激活的配额信息', _count

        data = bz2.compress(data)
        data = base64.b64encode(data)

        restore_data = {
            'data': data,
            'count': count,
            'syllabus': syllabus
        }

        t = datetime.datetime.now().strftime('%Y%m%d')
        with open(os.path.join(constants.CACHE_TMP_ROOT, t + '-' + key + '.bak'), 'w') as f:
            f.write(json.dumps(restore_data))
        end = time.time()

        print 'Stored at:', os.path.abspath(os.path.join(constants.CACHE_TMP_ROOT, t + '-' + key + '.bak'))
        print 'Items:', count
        print 'Time Use:', end - start
