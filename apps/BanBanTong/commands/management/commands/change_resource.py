#!/usr/bin/env python
# coding=utf-8
import datetime
import hashlib
import math
import random
import MySQLdb
import traceback


from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

from BanBanTong.db import models

'''
    本脚本只需要遍历TeacherLoginLog表，
    如果有resource_from或resource_tyep的值是不规范的
    就按下面的规则替换
    下面二个dict的key为规范
'''

froms = {
    u'中央电化教育馆教学资源库': [u'中央电教馆', u'中央资源'],
    u'互联网资源': [u'互联网', u'网上资源', u'网络', u'网络下载', u'网络教学资源', u'网络资源', u'百度文库'],
    u'优课网资源': [u'优课', u'优课网', u'优课资源'],
    u'其他资源': [u'其他', u'其它', u'其它资源', u'其它资料'],
    u'农村中小学现代远程教育资源': [u'农村中小学现代yuancheng资源', u'现代远程教育资源', u'远程资源'],
    u'教学点数字教育资源全覆盖': [u'农村教学点资源全覆盖'],
    u'凯瑞教学资源': [u'凯瑞', u'凯瑞资源', u'凯瑞资源库', u'凯瑞资源系统'],
    u'国家基础教育资源网': [u'国家基础教育资源', u'国家平台', u'国家教育资源', u'教育云资源', u'国家资源'],
    u'教材配套自带': [u'教学光盘', u'教材光盘', u'教材配套光盘', u'教材配套资源'],
    u'自制课件': [u'教师自制', u'白板书写', u'自制', u'自制课本', u'自制资源', u'本地资源'],
    u'电信网教育资源': [u'电信资源', u'翼校通'],
    u'课内网资源': [u'课内网', u'课内网www.iknei.com'],
    u'': [u'音频', u'动画片', u'文档', u'电脑', u'音视频', u'PPT']
}

types = {
    u'PPT幻灯片': [u'PPT 幻灯片'],
    u'其他': [u'其它']
}


class Command(BaseCommand):

    new_froms = {}
    new_types = {}

    def _adjust(self):
        '''重新整一下字典'''
        for k, v in froms.iteritems():
            for i in v:
                self.new_froms[i] = k

        for k, v in types.iteritems():
            for i in v:
                self.new_types[i] = k

    def _change(self):
        source = 0
        count = 0
        error = 0
        from_keys = self.new_froms.keys()
        type_keys = self.new_types.keys()

        objs = models.TeacherLoginLog.objects.all()
        for obj in objs:
            print 'source:', source
            resource_from = obj.resource_from.strip()
            resource_type = obj.resource_type.strip()

            is_save = False
            if resource_from in from_keys:
                obj.resource_from = self.new_froms[resource_from]
                is_save = True
            if resource_type in type_keys:
                obj.resource_type = self.new_types[resource_type]
                is_save = True
            if is_save:
                try:
                    obj.save()
                    count += 1
                except:
                    traceback.print_exc()
                    error += 1

            source += 1

        print 'total change:', count
        print 'total error:', error

    def handle(self, *args, **options):
        cursor = connection.cursor()
        cursor.execute('SET unique_checks=0')
        cursor.execute('SET foreign_key_checks=0')
        # 重新整一下字典
        self._adjust()

        self._change()

        cursor.execute('SET unique_checks=1')
        cursor.execute('SET foreign_key_checks=1')


#  更改恩施流水数据中的resource_from
#  有规范的书写将其规范

# 中央电教馆			(中央电化教育馆教学资源库)
# 中央资源			(中央电化教育馆教学资源库)
# 互联网				(互联网资源)
# 网上资源			(互联网资源)
# 网络				(互联网资源)
# 网络下载			(互联网资源)
# 网络教学资源			(互联网资源)
# 网络资源			(互联网资源)
# 优课				(优课网资源)
# 优课网				(优课网资源)
# 优课资源			(优课网资源)
# 其他				(其他资源)
# 其它				(其他资源)
# 其它资源			(其他资源)
# 农村中小学现代yuancheng资源	(农村中小学现代远程教育资源)
# 现代远程教育资源		(农村中小学现代远程教育资源)
# 远程资源			(农村中小学现代远程教育资源)
# 农村教学点资源全覆盖		(教学点数字教育资源全覆盖)
# 凯瑞				(凯瑞教学资源)
# 凯瑞资源			(凯瑞教学资源)
# 凯瑞资源库			(凯瑞教学资源)
# 凯瑞资源系统			(凯瑞教学资源)
# 国家基础教育资源		(国家基础教育资源网)
# 国家平台			(国家基础教育资源网)
# 国家教育资源			(国家基础教育资源网)
# 教育云资源			(国家基础教育资源网)
# 教学光盘			(教材配套自带)
# 教材光盘			(教材配套自带)
# 教材配套光盘			(教材配套自带)
# 教材配套资源			(教材配套自带)
# 教师自制			(自制课件)
# 白板书写			(自制课件)
# 自制				(自制课件)
# 自制课本			(自制课件)
# 自制资源			(自制课件)
# 电信资源			(电信网教育资源)
# 翼校通				(电信网教育资源)
# 课内网				(课内网资源)
# 课内网www.iknei.com		(课内网资源)
