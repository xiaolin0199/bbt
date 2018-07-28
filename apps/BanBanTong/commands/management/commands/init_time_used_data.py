#coding=utf-8
from django.core.management.base import BaseCommand
from django.db import connection
from BanBanTong.db import models

import math
import random
import uuid


class Command(BaseCommand):
    
    def run(self):
        logs = models.TeacherLoginLog.objects.all()
        count = 0
        for log in logs:
            login_time = t = int(math.ceil((45 - abs(random.gauss(0, 4))) * 60))
            try:
                a = models.TeacherLoginTime.objects.create(uuid=str(uuid.uuid1()).upper(),teacherloginlog=log,login_time=login_time)
                models.TeacherLoginTimeCache.objects.create(teacherlogintime=a,town=log.town,school=log.school,grade=log.grade,class_uuid=log.class_uuid,teacher=log.teacher,lesson_name=log.lesson_name)
            except Exception,e:
                pass
            count += 1
            print count , log.uuid
    
    def handle(self, *args, **options):
        cursor = connection.cursor()
        cursor.execute('SET unique_checks=0')
        cursor.execute('SET foreign_key_checks=0')
       
        self.run()
        
        cursor.execute('SET unique_checks=1')
        cursor.execute('SET foreign_key_checks=1')    



