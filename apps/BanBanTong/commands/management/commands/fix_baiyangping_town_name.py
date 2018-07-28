# coding=utf-8
"""
    现象: 白杨坪乡改名为白杨坪镇
    原因分析: GroupTB表中数据变更
    处理方法:
        程序段批处理

"""
import datetime
import hashlib
import math
import random
import MySQLdb
import traceback

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import F

from BanBanTong.db import models


class Command(BaseCommand):

    def handle(self, *args, **options):
        print 'begin'
        o = models.GroupTB.objects.get(group_id=422801204)
        o.name = u'白杨坪镇'
        o.save()
        print 'end'

