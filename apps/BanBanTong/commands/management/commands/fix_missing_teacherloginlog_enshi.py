#!/usr/bin/env python
# coding=utf-8
import datetime
from django.core.management.base import BaseCommand
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.utils import mongo


class Command(BaseCommand):
    '''
        恩施TeacherLoginLog写入mongodb时漏了一段，用这个程序补充完整
    '''

    def handle(self, *args, **options):
        if not constants.BANBANTONG_USE_MONGODB:
            print 'not using mongodb'
            return
        client = mongo._get_conn()
        if not client:
            print 'failed to get mongodb client'
            return
        db = client.banbantong
        collection = db.teacherloginlog

        q = models.TeacherLoginLog.objects.all()
        q = q.filter(created_at__gt=datetime.datetime(2014, 10, 29, 17, 55, 22))
        q = q.filter(created_at__lte=datetime.datetime(2014, 10, 30, 9, 10, 0))
        q = q.exclude(uuid='789DD24F-5FD1-11E4-AD06-001FC645A69B')
        print q.count()
        i = 0
        for obj in q:
            i += 1
            d = mongo._obj_to_dict(obj)
            try:
                login_time = obj.teacherlogintime.login_time
                d['time_used'] = login_time
            except:
                pass
            collection.insert(d)
            if i % 100 == 0:
                print 'TeacherLoginLog', i
        client.close()
