#!/usr/bin/env python
# coding=utf-8
from django.core.management.base import BaseCommand
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.utils import mongo


class Command(BaseCommand):
    '''
        1. 把TeacherLoginLog的数据从MySQL导入到MongoDB
        2. 把TeacherLoginTime导入MongoDB
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
        # db.drop_collection('teacherloginlog')
        collection = db.teacherloginlog

        q = models.TeacherLoginLog.objects.all()
        #s = datetime.datetime(2014, 10, 30, 23, 59, 59)
        #e = datetime.datetime(2014, 11, 30, 23, 59, 59)
        #q = q.filter(created_at__range=(s, e))
        print q.count()
        i = 0
        for obj in q:
            i += 1
            collection.insert(mongo._obj_to_dict(obj))
            if i % 100 == 0:
                print 'TeacherLoginLog', i

        q = models.TeacherLoginTime.objects.all()
        print q.count()
        i = 0
        for obj in q:
            i += 1
            collection.update({'uuid': obj.teacherloginlog.uuid},
                              {'$set': {'time_used': obj.login_time}})
            if i % 200 == 0:
                print 'TeacherLoginTime', i
