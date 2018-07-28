#!/usr/bin/env python
# coding=utf-8
import datetime
import hashlib
import math
import random
import uuid
import MySQLdb
import threading
import multiprocessing

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

    # RESOURCE_FROM
    RESOURCE_FROM = models.ResourceFrom.objects.all().values_list('value', flat=True)
    # RESOURCE_TYPE
    RESOURCE_TYPE = models.ResourceType.objects.all().values_list('value', flat=True)

    print_count = 10000

    def _work_create_teacherloginlog(self, term):

        # print 'start date: ' , datetime.datetime.now()
        # 获得线程名
        threadname = threading.currentThread().getName()

        count = 0

        school = term.school
        #
        grades = term.grade_set.all()

        # 找出该学校的所有学期班级数据
        country = models.Group.objects.get(group_type='country')
        # city obj
        city = models.Group.objects.get(group_type='city')
        # province obj
        province = models.Group.objects.get(group_type='province')

        town = school.parent

        #classes = models.Class.objects.select_related('grade__term').filter(grade__term__school=school)

        #grades = models.Grade.objects.select_related().filter(term__school=school)

        for g in grades.iterator():
            temp_activeteacher_list = []
            classes = g.class_set.all()
            for c in classes.iterator():
                # 找到某学期该班级对应的（学年学期及课程表）
                grade = g

                term_school_year = term.school_year
                term_type = term.term_type
                term_start_date = term.start_date
                term_end_date = term.end_date

                querysetlist_log = []
                querysetlist_time = []
                querysetlist_time_cache = []

                # activeteacher 并不是直接插入，而是需要先比较，有重复的就去掉
                querysetlist_activeteacher = []

                while term_start_date <= term_end_date:
                    # print term_start_date
                    weekday = term_start_date.strftime('%a').lower()
                    # 找到该班级该天的课程
                    ls = models.LessonSchedule.objects.filter(class_uuid=c, weekday=weekday)

                    # 开始一节一节的上课
                    for one in ls.iterator():
                        lesson_name = one.lesson_name
                        lesson_period = one.lesson_period
                        lesson_period_sequence = lesson_period.sequence
                        lesson_period_start_time = lesson_period.start_time
                        lesson_period_end_time = lesson_period.end_time

                        # 查找授课老师
                        objs = models.LessonTeacher.objects.filter(class_uuid=c, lesson_name=lesson_name)
                        if objs:
                            lesson_teacher = objs[0]
                            teacher = lesson_teacher.teacher
                            teacher_name = teacher.name
                        else:
                            lesson_teacher = None
                            teacher = None
                            teacher_name = u''

                        created_at = datetime.datetime(year=term_start_date.year, month=term_start_date.month, day=term_start_date.day,
                                                       hour=lesson_period_start_time.hour, minute=lesson_period_start_time.minute, second=lesson_period_start_time.second)

                        resource_from = random.choice(self.RESOURCE_FROM)
                        resource_type = random.choice(self.RESOURCE_TYPE)

                        # 插入流水 TeacherLoginLog
                        ret = models.TeacherLoginLog(
                            uuid=str(uuid.uuid1()).upper(),
                            teacher_name=teacher_name, lesson_name=lesson_name.name,
                            province_name=province.name, city_name=city.name,
                            country_name=country.name, town_name=town.name,
                            school_name=school.name, term_school_year=term.school_year,
                            term_type=term.term_type, term_start_date=term.start_date,
                            term_end_date=term.end_date,
                            grade_name=grade.name,
                            class_name=c.name,
                            lesson_period_sequence=lesson_period_sequence,
                            lesson_period_start_time=lesson_period_start_time,
                            lesson_period_end_time=lesson_period_end_time,
                            weekday=weekday, teacher=teacher,
                            province=province, city=city, country=country, town=town,
                            school=school, term=term, grade=grade,
                            class_uuid=c, lesson_period=lesson_period,
                            lesson_teacher=lesson_teacher, created_at=created_at,
                            resource_from=resource_from, resource_type=resource_type
                        )
                        querysetlist_log.append(ret)

                        # 处理 activeteachers
                        one_temp = {
                            'teacher': teacher,
                            'active_date': created_at.date(),
                            'country_name': country.name,
                            'town_name': town.name,
                            'school_name': school.name,
                            'school_year': term.school_year,
                            'term_type': term.term_type,
                            'lesson_name': lesson_name.name,
                            'grade_name': grade.name
                        }
                        if one_temp not in temp_activeteacher_list:
                            temp_activeteacher_list.append(one_temp)
                            # 非
                            ret_active_teacher = models.ActiveTeachers(**one_temp)

                            querysetlist_activeteacher.append(ret_active_teacher)

                        # 插入流水的上课时间 TeacherLoginTime
                        seconds = (lesson_period_end_time.hour * 3600 + lesson_period_end_time.minute * 60 + lesson_period_end_time.second) - \
                            (lesson_period_start_time.hour * 3600 + lesson_period_start_time.minute * 60 + lesson_period_start_time.second) - 15

                        ret_time = models.TeacherLoginTime(
                            uuid=str(uuid.uuid1()).upper(),
                            teacherloginlog=ret,
                            login_time=seconds
                        )
                        querysetlist_time.append(ret_time)

                        # 插入上课时间 TeacherLoginTimeCache
                        ret_time_cache = models.TeacherLoginTimeCache(
                            teacherlogintime=ret_time,
                            town=town,
                            school=school,
                            grade=grade,
                            class_uuid=c,
                            teacher=teacher,
                            lesson_name=lesson_name.name

                        )
                        querysetlist_time_cache.append(ret_time_cache)

                        count += 1

                        if count % self.print_count == 0:
                            print threadname, school, ' teacherloginlog adding: ', count

                        # if count == 500:
                        #    print 'end date: ' , datetime.datetime.now()

                        #    asdfadfaf

                    # 下一天
                    term_start_date += datetime.timedelta(days=1)

                # 统一批量插入
                models.TeacherLoginLog.objects.bulk_create(querysetlist_log)
                models.ActiveTeachers.objects.bulk_create(querysetlist_activeteacher)
                models.TeacherLoginTime.objects.bulk_create(querysetlist_time)
                models.TeacherLoginTimeCache.objects.bulk_create(querysetlist_time_cache)

    def create_teacherloginlog(self, *args):
        '''
            13. 生成每个班级的流水上课日志 ( 20个学期即 51000 * 6 * 90(平均每学期上课时间) = 27540000 )；
        '''
        print '--- teacherloginlog ---'
        now_start = datetime.datetime.now()
        print 'start date: ', now_start

        # 一个进程处理一个学期一个学校，如果是20个学期100个学样，那一共要处理2000个进程?
        term_uuid, = args

        #school_list = models.Group.objects.filter(group_type='school')

        # for school in school_list:
        #    self._work_create_teacherloginlog(school)

        # 某学校的某学年信息
        term = models.Term.objects.get(uuid=term_uuid)

        self._work_create_teacherloginlog(term)

        '''
        # 启动线程
        threads = []

        for school in school_list:
            t = threading.Thread(target=self._work_create_teacherloginlog, args=(school,))
            threads.append(t)

        for t in threads:
            t.start()

        for t in threads:
            t.join()
        '''

        print 'total use: ', datetime.datetime.now() - now_start

    """
    def create_activeteachers(self):
        '''
            根据 TeacherLoginLog生成ActiveTeachers数据
        '''
        print '--- ActiveTeachers ---'
        now_start = datetime.datetime.now()
        print 'start date: ' , now_start

        start = 0
        limit = 5000

        objs = models.TeacherLoginLog.objects.select_related().all()
        obj_count = objs.count()

        print 'obj_count: ' , obj_count

        while obj_count > start:
            end = start + limit
            print 'processing activeteachers: ', start  , end
            objs_list = objs[start:end]

            for i in objs_list:
                models.ActiveTeachers.objects.get_or_create(
                    teacher = i.teacher,
                    active_date = i.created_at.date(),
                    country_name = i.country_name,
                    town_name = i.town_name,
                    school_name = i.school_name,
                    school_year = i.term_school_year,
                    term_type = i.term_type,
                    lesson_name = i.lesson_name,
                    grade_name = i.grade_name
                )

            start += limit

        print 'total use: ' , datetime.datetime.now() - now_start
    """

    def handle(self, *args, **options):
        cursor = connection.cursor()
        cursor.execute('SET unique_checks=0')
        cursor.execute('SET foreign_key_checks=0')

        # 生成流水数据，暂时只生成 teacherloginlog 上课纪录流水
        self.create_teacherloginlog(*args)

        # 生成 activeteachers数据
        # self.create_activeteachers()

        cursor.execute('SET unique_checks=1')
        cursor.execute('SET foreign_key_checks=1')
