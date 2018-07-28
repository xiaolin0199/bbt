#!/usr/bin/env python
# coding=utf-8
import datetime
import logging
from django.db.models import Count
from django.db.models import Q
from django.db.models import Sum
from BanBanTong.db import models
from BanBanTong.utils import datetimeutil
from django.conf import settings
from BanBanTong import constants
DEBUG = settings.DEBUG
del settings


def _calculate_term_lesson_count(term, s, e):
    week = datetimeutil.get_week_number(term, s, e)
    if week < 1:
        return
    # 从TeacherLoginLog找出记录，进行汇总
    q = models.TeacherLoginLog.objects.filter(created_at__range=(s, e),
                                              term=term)
    q = q.values('town_name', 'school_name', 'term', 'grade_name',
                 'class_name').annotate(lesson_count=Count('pk'))
    for i in q:
        term = models.Term.objects.get(uuid=i['term'])
        func = models.TeacherLoginCountWeekly.objects.get_or_create
        obj, c = func(town_name=i['town_name'], school_name=i['school_name'],
                      term=term, grade_name=i['grade_name'],
                      class_name=i['class_name'], week=week)
        if obj.lesson_count != i['lesson_count']:
            obj.lesson_count = i['lesson_count']
            obj.save()


def _calculate_lesson_count(s, e):
    cond = Q(start_date__lte=s.date(), end_date__gte=s.date())
    cond |= Q(start_date__lte=e.date(), end_date__gte=e.date())
    q = models.Term.objects.filter(cond)
    for term in q:
        _calculate_term_lesson_count(term, s, e)


def _calculate_term_weekly_time(term, s, e):
    week = datetimeutil.get_week_number(term, s, e)
    if week < 1:
        return
    # 从TeacherLoginTime找出记录，进行汇总
    q = models.TeacherLoginTime.objects.all()
    q = q.filter(teacherloginlog__created_at__range=(s, e),
                 teacherloginlog__term=term)
    q = q.values('teacherloginlog__town_name', 'teacherloginlog__school_name',
                 'teacherloginlog__term', 'teacherloginlog__grade_name',
                 'teacherloginlog__class_name')
    q = q.annotate(total_time=Sum('login_time'))
    for i in q:
        town_name = i['teacherloginlog__town_name']
        school_name = i['teacherloginlog__school_name']
        term = models.Term.objects.get(uuid=i['teacherloginlog__term'])
        grade_name = i['teacherloginlog__grade_name']
        class_name = i['teacherloginlog__class_name']
        func = models.TeacherLoginTimeWeekly.objects.get_or_create
        obj, c = func(town_name=town_name, school_name=school_name,
                      term=term, grade_name=grade_name,
                      class_name=class_name, week=week)
        if obj.total_time != i['total_time']:
            obj.total_time = i['total_time']
            obj.save()


def _calculate_weekly_time(s, e):
    cond = Q(start_date__lte=s.date(), end_date__gte=s.date())
    cond |= Q(start_date__lte=e.date(), end_date__gte=e.date())
    q = models.Term.objects.filter(cond)
    for term in q:
        _calculate_term_weekly_time(term, s, e)


class Task(object):
    '''
        班班通授课综合分析：1. 生成数据表 2. (TODO)生成缓存
    '''
    if DEBUG:
        run_period = constants.TASK_MAX_RUN_PERIOD
    else:
        run_period = 60 * 60 * 2  # two hours

    logger = logging.getLogger(__name__)

    def __init__(self):
        if models.Setting.getvalue('server_type') == 'school':
            return
        now = datetime.datetime.now()
        if not DEBUG and not (17 < now.hour < 24 or 11 < now.hour < 14):
            # 生产环境下如果当前时间不是在中午或者下午5时以后,那么返回.
            return
        # 遍历本周的所有TeacherLoginLog和TeacherLoginTime，计算到目前为止的一周汇总
        # 注：每周时间为[星期一, 星期天]
        monday = now.date() - datetime.timedelta(days=now.weekday())
        today = now.date()
        s = datetime.datetime.combine(monday, datetime.time.min)
        e = datetime.datetime.combine(today, datetime.time.max)
        if s > e:
            return
        _calculate_lesson_count(s, e)
        _calculate_weekly_time(s, e)
