#!/usr/bin/env python
# coding=utf-8
import datetime
import hashlib
import math
import random
import uuid
import MySQLdb
import threading
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.db import transaction
from django.utils.dateparse import parse_date
from django.utils.dateparse import parse_time
from BanBanTong.db import models
from BanBanTong.forms.new_lesson_name import NewLessonNameForm
from BanBanTong.utils import str_util

DEBUG = True


class Command(BaseCommand):

    def tongji_teacherlogintime(self):
        '''
            根据 TeacherLoginTimeTemp里的数据生成teacherlogintime数据
        '''
        print '--- tongji_teacherlogintime ---'
        now_start = datetime.datetime.now()
        print 'start date: ', now_start

        start = 0
        limit = 5000

        objs = models.TeacherLoginTimeTemp.objects.all()
        obj_count = objs.count()

        print 'obj_count: ', obj_count

        while obj_count > start:
            end = start + limit
            print 'processing: ', start, end
            objs_list = objs[start:end]

            for i in objs_list:
                tl = i.teacherloginlog
                # 每节课的最大上课时间(秒) 结束TIME - 登录时间TIME
                login_time = i.login_time
                # 如果我们的计算时间大于每节课的最大上课时间，则保存设定的最大上课时间
                obj, c = models.TeacherLoginTime.objects.get_or_create(
                    teacherloginlog=tl,
                    defaults={
                        'login_time': login_time,
                        'uuid': str(uuid.uuid1()).upper()
                    }
                )

                # 删除timetemp数据
                #if c: i.delete()

            start += limit

        print 'total use: ', datetime.datetime.now() - now_start

    def handle(self, *args, **options):
        cursor = connection.cursor()
        cursor.execute('SET unique_checks=0')
        cursor.execute('SET foreign_key_checks=0')

        # 2015 04 07 不需要这个了，流水生成的时候，直接生成 TeacherLoginTime
        # 统计上课时长  TeacherLoginTime
        # self.tongji_teacherlogintime()
        # 原先是添加一条time就删除一条timetmpe，我们这里测试用就直接把整表干掉 ， 但不安全
        #cursor.execute('TRUNCATE db_teacherlogintimetemp')
        ##############
        start_now = datetime.datetime.now()

        terms = models.Term.objects.all()
        # 统计所有的total* 表 (update-old-terms 表示历史学期也算)
        # ./manage.py calculate_totalteachers update-old-terms
        # for term in terms:
        #    print 'calculate_totalteachers: ', term.school.name , term.school_year , term.term_type
        #    subprocess.call('python manage.py calculate_totalteachers %s' %term.uuid,shell=True)
        #subprocess.call('python manage.py calculate_totalteachers update-old-terms',shell=True)

        # 统计 db_teacherlogincountweekly 和 db_teacherlogintimeweekly 表
        # ./manage.py calculate_teaching_analysis
        # for term in terms:
        #    print 'calculate_teaching_analysis: ', term.school.name , term.school_year , term.term_type
        #    subprocess.call('python manage.py calculate_teaching_analysis %s' %term.uuid,shell=True)
        #subprocess.call('python manage.py calculate_teaching_analysis',shell=True)

        # 统计 db_statistic表
        # for term in terms:
        #    print 'create_statistic_items: ' , term.school.name , term.school_year , term.term_type
        #    subprocess.call('python manage.py create_statistic_items %s' %term.uuid,shell=True)

        # 重新计算G表的教师已授课时 lessonteacher
        # ./manage.py calculate_teacher_finished_time update-old-terms
        for term in terms:
            print 'calculate_teacher_finished_time: ', term.school.name, term.school_year, term.term_type
            subprocess.call('python manage.py calculate_teacher_finished_time %s' % term.uuid, shell=True)
        #subprocess.call('python manage.py calculate_teacher_finished_time update-old-terms',shell=True)

        print 'success tongji: ', datetime.datetime.now() - start_now

        cursor.execute('SET unique_checks=1')
        cursor.execute('SET foreign_key_checks=1')
