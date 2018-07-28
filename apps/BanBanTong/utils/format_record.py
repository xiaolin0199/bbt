#!/usr/bin/env python
# coding=utf-8
import logging
import datetime
import traceback
from django.conf import settings
from django.core import exceptions
from django.db.models import Q
from django.db.models import Sum
from django.utils.dateparse import parse_date
from BanBanTong.db import models
from BanBanTong.utils import mongo

DEBUG = settings.DEBUG
del settings
logger = logging.getLogger(__name__)


def activity_logged_in(l):
    for d in l:
        d['time_used'] = d['teacherlogintime__login_time']
        del d['teacherlogintime__login_time']
    return l


def activity_logged_in_new(l):
    def __fix_task(obj, seconds):
        """
            如果已经结束的教师登录记录中在TeacherLoginTime没有对应的授课时长条目
            那么这里就会针对性的进行一下修复
            原则是:
                如果在缓存表中有对应的记录,那么使用缓存表中的时长数据
                如果在缓存表中没有对应的记录,那么创建一个时长为0/n的条目
            理论上,这样需要修复的条目不会很多(一次查询中最多25条),所以直接放在这里
        """
        try:
            q = models.TeacherLoginTimeTemp.objects.get(teacherloginlog=obj)
            login_time = q.login_time if q.login_time < seconds else seconds

        except exceptions.ObjectDoesNotExist:
            # 理论上临时表中的数据是不会异常丢失的,但是...
            # 如果临时表中的数据已经丢失了,那么根据登录日志创建一条
            # 创建原则 结束时间-登录时间 (登录时间不在节次内的话则为0)
            # 这样登录日志对应使用时长,整个数据才是完整的.
            if DEBUG:
                traceback.print_exc()
            date = obj.created_at.date()
            s = datetime.datetime.combine(date, obj.lesson_period_start_time)
            e = datetime.datetime.combine(date, obj.lesson_period_end_time)
            if s <= obj.created_at <= e:
                login_time = (e - obj.created_at).total_seconds()
            else:
                login_time = 0
            o = models.TeacherLoginTime(
                teacherloginlog=obj,
                login_time=login_time
            ).save()
            return o
        except exceptions.MultipleObjectsReturned:
            logger.exception('')
            q = models.TeacherLoginTimeTemp.objects.filter(teacherloginlog=obj)[0]
            login_time = q.login_time if q.login_time < seconds else seconds
            if DEBUG:
                traceback.print_exc()
        except:
            logger.exception('')
            if DEBUG:
                traceback.print_exc()
            return None

        o = models.TeacherLoginTime(teacherloginlog=obj, login_time=login_time)
        try:
            o.save()
        except:
            logger.exception('')
        finally:
            # 下面的是为了处理由于在o.save()中lessonteacher.save()引起的异常
            # 而导致的o.save()没有正常返回引发的错误.
            objs = models.TeacherLoginTime.objects.filter(teacherloginlog=obj)
            if objs.exists():
                models.TeacherLoginTimeTemp.objects.filter(teacherloginlog=obj).all().delete()
                return objs[0]

    for d in l:
        obj = models.TeacherLoginLog.objects.get(uuid=d['uuid'])

        if hasattr(obj, 'login_time'):
            d['teacherlogintimetemp'] = 0
            d['time_used'] = obj.login_time
            d['#fix_time_to'] = obj.login_time
        else:
            try:
                teacherlogintimetemp = models.TeacherLoginTimeTemp.objects.get(teacherloginlog=obj)
                d['teacherlogintimetemp'] = teacherlogintimetemp.login_time
            except:
                d['teacherlogintimetemp'] = 0

            try:
                teacherlogintime = models.TeacherLoginTime.objects.get(teacherloginlog=obj)
                d['time_used'] = teacherlogintime.login_time
            except:
                server_type = models.Setting.getvalue('server_type')
                if server_type != 'school':
                    d['time_used'] = 0
                    d['#debug'] = 'no login_time obj'
                else:
                    # 如果是校级,直接从缓存表里面获取并且把定时任务的事给做了
                    now = datetime.datetime.now()
                    s = datetime.datetime.combine(now.date(), obj.lesson_period_start_time)
                    e = datetime.datetime.combine(now.date(), obj.lesson_period_end_time)
                    seconds = (e - s).total_seconds()
                    if obj.created_at.date() >= now.date() and e > now:
                        d['time_used'] = 0
                        d['inclass'] = True
                    else:
                        # 如果课程已经结束,那么这里将缓存表中的授课时长
                        # 更新到TeacherLoginTime表中而不是等待定时任务更新
                        o = __fix_task(obj, seconds)
                        d['time_used'] = o and o.login_time or 0
                        d['#fix_time_to'] = o and o.login_time or 0

        try:
            # 该部分用于格式化电脑教室终端登录日志的年级班级名
            c = d['teacherloginlogtag__created_at__name']
            d['computerclass'] = c
            del d['teacherloginlogtag__created_at__grade__name']
            del d['teacherloginlogtag__created_at__name']
        except:
            if DEBUG:
                traceback.print_exc()
    return l


def activity_logged_in_force_index(l):
    for d in l:
        t = models.TeacherLoginLog.objects.get(uuid=d['uuid'])
        try:
            d['time_used'] = t.teacherlogintime.login_time
        except:
            d['time_used'] = None
    return l


def asset_type_total_in_use(l, conditions=None):
    if conditions:
        country_name = conditions.get('country_name')
        town_name = conditions.get('town_name')
        school_name = conditions.get('school_name')
    else:
        country_name = ''
        town_name = ''
        school_name = ''
    ret = []
    for i in l:
        d = {}
        if 'uuid' in i:
            d['uuid'] = i['uuid']
            q = models.Asset.objects.filter(asset_type__uuid=d['uuid'],
                                            status='在用')
            q = q.aggregate(total=Sum('number'))
            d['unit_count'] = q['total']
        d['name'] = i['name']
        d['icon'] = i['icon']
        d['unit_name'] = i['unit_name']
        if 'unit_count' not in d:
            q = models.Asset.objects.all()
            q = q.filter(asset_type__name=d['name'],
                         asset_type__icon=d['icon'],
                         asset_type__unit_name=d['unit_name'],
                         status='在用')
            if country_name:
                q = q.filter(school__parent__parent__name=country_name)
            if town_name:
                q = q.filter(school__parent__name=town_name)
            if school_name:
                q = q.filter(school__name=school_name)
            q = q.aggregate(total=Sum('number'))
            d['unit_count'] = q['total']
        ret.append(d)
    return ret


def global_desktop_preview(l):
    ret = []
    for d in l:
        d_new = {}
        d_new['grade_name'] = d['pic__grade__name']
        d_new['class_name'] = d['pic__class_uuid__name']
        d_new['lesson_name'] = d['pic__lesson_name']
        d_new['teacher_name'] = d['pic__teacher_name']
        d_new['lesson_period_sequence'] = d['pic__lesson_period_sequence']
        d_new['host'] = d['pic__host']
        d_new['url'] = d['pic__url']
        ret.append(d_new)
    return ret


def syllabus_content_list(l):
    ret = []
    for d in l:
        d_new = d
        #d_new['sequence'] = '-'.join([str(d['seq']), str(d['subseq'])]) if d['subseq'] else str(d['seq'])
        ret.append(d_new)
    return ret


# 街道乡镇，未登录教师总数
def teacher_absent(l, total_teachers,
                   start_date, end_date, school_year, term_type):
    q_all = models.TeacherLoginLog.objects.all()
    q_all = q_all.filter(teacher__deleted=False)
    q_all = q_all.filter(teacher__in=total_teachers)
    if start_date and end_date:
        s = parse_date(start_date)
        e = parse_date(end_date)
        s = datetime.datetime.combine(s, datetime.time.min)
        e = datetime.datetime.combine(e, datetime.time.max)
        q_all = q_all.filter(created_at__range=(s, e))
    if school_year:
        q_all = q_all.filter(term__school_year=school_year)
    if term_type:
        q_all = q_all.filter(term__term_type=term_type)
    ret = []
    for d in l:
        d_new = {}
        q = q_all
        if 'class_uuid__grade__term__school__parent__parent__name' in d:
            d_new['country_name'] = d['class_uuid__grade__term__school__parent__parent__name']
            q = q.filter(country_name=d_new['country_name'])
        if 'class_uuid__grade__term__school__parent__name' in d:
            d_new['town_name'] = d['class_uuid__grade__term__school__parent__name']
            q = q.filter(town_name=d_new['town_name'])
        if 'class_uuid__grade__term__school__name' in d:
            d_new['school_name'] = d['class_uuid__grade__term__school__name']
            q = q.filter(school_name=d_new['school_name'])
        if 'class_uuid__grade__name' in d:
            d_new['grade_name'] = d['class_uuid__grade__name']
            q = q.filter(grade_name=d_new['grade_name'])
        if 'lesson_name__name' in d:
            d_new['lesson_name'] = d['lesson_name__name']
            q = q.filter(lesson_name=d_new['lesson_name'])
        d_new['total_teachers'] = d['total_teachers']
        n = q.values('teacher').distinct().count()
        d_new['absent_teachers'] = d_new['total_teachers'] - n
        ret.append(d_new)
    return ret


# 教师授课人数比例统计
def teacher_active(l, total_teachers,
                   start_date, end_date, school_year, term_type):
    q_all = models.TeacherLoginLog.objects.all()
    q_all = q_all.filter(teacher__deleted=False)
    q_all = q_all.filter(teacher__in=total_teachers)
    if start_date and end_date:
        s = parse_date(start_date)
        e = parse_date(end_date)
        s = datetime.datetime.combine(s, datetime.time.min)
        e = datetime.datetime.combine(e, datetime.time.max)
        q_all = q_all.filter(created_at__range=(s, e))
    if school_year:
        q_all = q_all.filter(term__school_year=school_year)
    if term_type:
        q_all = q_all.filter(term__term_type=term_type)
    ret = []
    for d in l:
        d_new = {}
        q = q_all
        if 'class_uuid__grade__term__school__parent__parent__name' in d:
            d_new['country_name'] = d['class_uuid__grade__term__school__parent__parent__name']
            q = q.filter(country_name=d_new['country_name'])
        if 'class_uuid__grade__term__school__parent__name' in d:
            d_new['town_name'] = d['class_uuid__grade__term__school__parent__name']
            q = q.filter(town_name=d_new['town_name'])
        if 'class_uuid__grade__term__school__name' in d:
            d_new['school_name'] = d['class_uuid__grade__term__school__name']
            q = q.filter(school_name=d_new['school_name'])
        if 'class_uuid__grade__name' in d:
            d_new['grade_name'] = d['class_uuid__grade__name']
            q = q.filter(grade_name=d_new['grade_name'])
        if 'lesson_name__name' in d:
            d_new['lesson_name'] = d['lesson_name__name']
            q = q.filter(lesson_name=d_new['lesson_name'])
        d_new['total_teachers'] = d['total_teachers']
        n = q.values('teacher').distinct().count()
        d_new['active_teachers'] = n
        ret.append(d_new)
    return ret


def new_teacher_active(l, cond):
    start_date = cond.get('start_date')
    end_date = cond.get('end_date')
    school_year = cond.get('school_year')
    term_type = cond.get('term_type')
    q_all = models.ActiveTeachers.objects.all()
    #q_all = q_all.filter(teacher__deleted=False)

    if start_date and end_date:
        s = parse_date(start_date)
        e = parse_date(end_date)
        q_all = q_all.filter(active_date__range=(s, e))
    if school_year:
        q_all = q_all.filter(school_year=school_year)
    if term_type:
        q_all = q_all.filter(term_type=term_type)

    ret = []
    for d in l:
        d_new = {}
        q = q_all
        if 'country_name' in d:
            d_new['country_name'] = d['country_name']
            q = q.filter(country_name=d_new['country_name'])
        if 'town_name' in d:
            d_new['town_name'] = d['town_name']
            q = q.filter(town_name=d_new['town_name'])
        if 'school_name' in d:
            d_new['school_name'] = d['school_name']
            q = q.filter(school_name=d_new['school_name'])
        if 'grade_name' in d:
            d_new['grade_name'] = d['grade_name']
            q = q.filter(grade_name=d_new['grade_name'])
        if 'lesson_name' in d:
            d_new['lesson_name'] = d['lesson_name']
            q = q.filter(lesson_name=d_new['lesson_name'])
        if 'term__school_year' in d:
            d_new['school_year'] = d['term__school_year']
        if 'term__term_type' in d:
            d_new['term_type'] = d['term__term_type']
        if 'term' in d:
            d_new['term_uuid'] = d['term']
        d_new['total_teachers'] = d['total']
        n = q.values('teacher').distinct().count()
        d_new['active_teachers'] = n
        ret.append(d_new)
    return ret


def new_teacher_absent(l, cond):
    start_date = cond.get('start_date')
    end_date = cond.get('end_date')
    school_year = cond.get('school_year')
    term_type = cond.get('term_type')
    q_all = models.ActiveTeachers.objects.all()
    q_all = q_all.filter(teacher__deleted=False)
    if start_date and end_date:
        s = parse_date(start_date)
        e = parse_date(end_date)
        q_all = q_all.filter(active_date__range=(s, e))
    if school_year:
        q_all = q_all.filter(school_year=school_year)
    if term_type:
        q_all = q_all.filter(term_type=term_type)
    ret = []
    for d in l:
        d_new = {}
        q = q_all
        if 'country_name' in d:
            d_new['country_name'] = d['country_name']
            q = q.filter(country_name=d_new['country_name'])
        if 'town_name' in d:
            d_new['town_name'] = d['town_name']
            q = q.filter(town_name=d_new['town_name'])
        if 'school_name' in d:
            d_new['school_name'] = d['school_name']
            q = q.filter(school_name=d_new['school_name'])
        if 'grade_name' in d:
            d_new['grade_name'] = d['grade_name']
            q = q.filter(grade_name=d_new['grade_name'])
        if 'lesson_name' in d:
            d_new['lesson_name'] = d['lesson_name']
            q = q.filter(lesson_name=d_new['lesson_name'])
        if 'term__school_year' in d:
            d_new['school_year'] = d['term__school_year']
        if 'term__term_type' in d:
            d_new['term_type'] = d['term__term_type']
        if 'term' in d:
            d_new['term_uuid'] = d['term']
        d_new['total_teachers'] = d['total']
        n = q.values('teacher').distinct().count()
        #d_new['active_teachers'] = n
        d_new['absent_teachers'] = d_new['total_teachers'] - n
        ret.append(d_new)
    return ret


def teaching_time(lesson_teacher_objs, start_date, end_date, **kwargs):
    # 用于by_lessonteacher, by_teacher
    # 已有学校、年级、班级、计划课时、（实际课时）
    # 需要街道乡镇、（实际课时）
    ##
    # {
    #     "town_name": "关山街道",
    #     "school_name": "大白菜中学",
    #     "grade_name": "一",
    #     "class_name": "1",
    #     "teacher_name": "体瑜",
    #     "lesson_name": "品德与社会",
    #     "finished_time": 1,
    #     "schedule_time": 20,
    #     "finished_rate": "5.00%"
    # }
    ret = []
    for d in lesson_teacher_objs:
        d_new = {}
        d_new['town_name'] = d['class_uuid__grade__term__school__parent__name']
        d_new['school_name'] = d['class_uuid__grade__term__school__name']
        d_new['grade_name'] = d.get('class_uuid__grade__name')
        d_new['class_name'] = d.get('class_uuid__name')
        d_new['teacher_name'] = d.get('teacher__name')
        d_new['teacher__birthday'] = d.get('teacher__birthday')
        d_new['teacher__pk'] = d.get('teacher__pk')
        d_new['lesson_name'] = d.get('lesson_name__name')
        d_new['schedule_time'] = d.get('schedule_time', d.get('group_schedule', 0))

        if 'group_finished' in d:
            # by teacher
            d_new['finished_time'] = d['group_finished']
        else:
            q = models.TeacherLoginLog.objects.filter(
                teacher__deleted=False,
                # lesson_teacher__isnull=False
            )
            school_year = kwargs.get('school_year')
            term_type = kwargs.get('term_type')
            if school_year:
                q = q.filter(term_school_year=school_year)
            if term_type:
                q = q.filter(term_type=term_type)
            q = q.filter(school_name=d_new['school_name'])
            if d_new['grade_name']:
                q = q.filter(grade_name=d_new['grade_name'])
            if d_new['class_name']:
                q = q.filter(class_name=d_new['class_name'])
            if d_new['teacher_name']:
                q = q.filter(teacher_name=d_new['teacher_name'])
            if d_new['teacher__pk']:
                q = q.filter(teacher__pk=d_new['teacher__pk'])
            if d_new['lesson_name']:
                q = q.filter(lesson_name=d_new['lesson_name'])
            if start_date and end_date:
                s = parse_date(start_date)
                e = parse_date(end_date)
                s = datetime.datetime.combine(s, datetime.time.min)
                e = datetime.datetime.combine(e, datetime.time.max)
                q = q.filter(created_at__range=(s, e))

            d_new['finished_time'] = q.count()
        try:
            d_new['finished_rate'] = '%0.2f%%' % (d_new['finished_time'] * 100.0 / d_new['schedule_time'])
        except ZeroDivisionError:
            d_new['finished_rate'] = '0.00%%'

        ret.append(d_new)
    return ret


def teaching_time_class_total(l, start_date, end_date, school_year, term_type):
    # 用于by_country, by_town, by_school, by_grade
    # 已有乡镇 （街道、学校、年级）、计划授课次数
    # 需要班级总数、实际授课次数、班级平均授课数、计划授课总数
    klass = models.Class.objects.all().exclude(grade__number=13)  # 不统计电脑教室
    if start_date and end_date:
        s = parse_date(start_date)
        e = parse_date(end_date)
        s = datetime.datetime.combine(s, datetime.time.min)
        e = datetime.datetime.combine(e, datetime.time.max)
        cond = Q(grade__term__start_date__lte=s,
                 grade__term__end_date__gte=s)
        cond |= Q(grade__term__start_date__gte=s,
                  grade__term__end_date__lte=e)
        cond |= Q(grade__term__start_date__lte=e,
                  grade__term__end_date__gte=e)
        klass = klass.filter(cond)
    if school_year:
        klass = klass.filter(grade__term__school_year=school_year)
    if term_type:
        klass = klass.filter(grade__term__term_type=term_type)

    term = klass[0].grade.term
    ret = []
    for d in l:
        d_new = {}
        q = klass
        if 'class_uuid__grade__term__school__parent__parent__name' in d:
            # 地市州
            d_new['country_name'] = d['class_uuid__grade__term__school__parent__parent__name']
            q = q.filter(grade__term__school__parent__parent__name=d_new['country_name'])
            rate_obj_pk = d.get('class_uuid__grade__term__school__parent__parent__pk')
        if 'class_uuid__grade__term__school__parent__name' in d:
            # 区县市 按乡镇街道
            d_new['town_name'] = d['class_uuid__grade__term__school__parent__name']
            q = q.filter(grade__term__school__parent__name=d_new['town_name'])
            rate_obj_pk = d.get('class_uuid__grade__term__school__parent__pk')
        if 'class_uuid__grade__term__school__name' in d:
            # 校级 按学校
            d_new['school_name'] = d['class_uuid__grade__term__school__name']
            q = q.filter(grade__term__school__name=d_new['school_name'])
            rate_obj_pk = d.get('class_uuid__grade__term__school__pk')
        if 'class_uuid__grade__name' in d:
            # 年级 按学校年级
            d_new['grade_name'] = d['class_uuid__grade__name']
            q = q.filter(grade__name=d_new['grade_name'])
            rate_obj_pk = d.get('class_uuid__grade__pk')
        d_new['class_total'] = q.distinct().count()

        if 'schedule_time' in d:
            d_new['schedule_time'] = d['schedule_time']
            d_new['class_schedule_time'] = d['schedule_time']
        else:
            d_new['class_schedule_time'] = d['class_uuid__grade__term__schedule_time']
            d_new['schedule_time'] = d_new['class_total'] * d['class_uuid__grade__term__schedule_time']

        if 'group_finished' in d:
            d_new['finished_time'] = d['group_finished']
        else:
            # 否则根据流水统计达标授课总数
            q = models.TeacherLoginLog.objects.all()
            if 'country_name' in d_new:
                q = q.filter(country_name=d_new['country_name'])
            if 'town_name' in d_new:
                q = q.filter(town_name=d_new['town_name'])
            if 'school_name' in d_new:
                q = q.filter(school_name=d_new['school_name'])
            if 'grade_name' in d_new:
                q = q.filter(grade_name=d_new['grade_name'])
            if school_year:
                q = q.filter(term__school_year=school_year)
            if term_type:
                q = q.filter(term__term_type=term_type)
            if start_date and end_date:
                s = parse_date(start_date)
                e = parse_date(end_date)
                s = datetime.datetime.combine(s, datetime.time.min)
                e = datetime.datetime.combine(e, datetime.time.max)
                q = q.filter(created_at__range=(s, e))
            d_new['finished_time'] = q.count()
        try:
            average = d_new['finished_time'] * 1.0 / d_new['class_total']
        except:
            average = 0.0
        d_new['class_average'] = '%0.2f' % average
        d_new['finished_rate'] = '%0.2f%%' % (d_new['finished_time'] * 100.0 / d_new['schedule_time'])

        # V 4.2.5 新增需求:
        # 学校达标与班级达标字段
        if rate_obj_pk:
            d_new.update(models.Statistic.get_rate_info(term, rate_obj_pk))
            if not 'class_uuid__grade__term__school__parent__pk' in d:
                try:
                    del d_new['finished_rate_school']
                except:
                    pass

        ret.append(d_new)
    return ret


def teaching_time_by_town(records, start_date, end_date, school_year, term_type):
    # 用于by_town
    # 已有街道、计划授课次数
    # 需要班级总数、实际授课次数、班级平均授课数、计划授课总数
    ret = []
    for d in records:
        d_new = {}
        mongo_cond = {}
        q = models.Class.objects.all().exclude(grade__number=13)
        d_new['town_name'] = d['town_name']
        mongo_cond['town_name'] = d['town_name']
        q = q.filter(grade__term__school__parent__uuid=d['town_uuid'],
                     grade__number__lt=13)
        if start_date and end_date:
            s = parse_date(start_date)
            e = parse_date(end_date)
            s = datetime.datetime.combine(s, datetime.time.min)
            e = datetime.datetime.combine(e, datetime.time.max)
            cond = Q(grade__term__start_date__lte=s,
                     grade__term__end_date__gte=s)
            cond |= Q(grade__term__start_date__gte=s,
                      grade__term__end_date__lte=e)
            cond |= Q(grade__term__start_date__lte=e,
                      grade__term__end_date__gte=e)
            q = q.filter(cond)
            mongo_cond['start_date'] = start_date
            mongo_cond['end_date'] = end_date
        if school_year:
            q = q.filter(grade__term__school_year=school_year)
            mongo_cond['school_year'] = school_year
        if term_type:
            q = q.filter(grade__term__term_type=term_type)
            mongo_cond['term_type'] = term_type
        d_new['class_total'] = q.distinct().count()
        d_new['class_schedule_time'] = d['schedule_time']
        d_new['schedule_time'] = d['schedule_time'] * d_new['class_total']

        d_new['finished_time'] = mongo.count_teacherloginlog(mongo_cond)
        try:
            average = d_new['finished_time'] * 1.0 / d_new['class_total']
        except:
            average = 0.0
        d_new['class_average'] = '%0.2f' % average
        ret.append(d_new)
    return ret


def time_used(l, cache_key):
    ret = []
    # 仅按乡镇，按学校，按年级时统计班级总数, 这样可以减少不需要统计时对数据库的操作
    if cache_key in ['time-used-by-grade', 'time-used-by-school', 'time-used-by-town', 'time-used-by-country']:
        calc_class = True
    else:
        calc_class = False

    for d in l:
        d_new = {}
        if calc_class:
            q = models.Class.objects.all().exclude(grade__number=13)
            if 'town__name' in d:
                q = q.filter(grade__term__school__parent__name=d['town__name'])
            if 'school__name' in d:
                q = q.filter(grade__term__school__name=d['school__name'])
            if 'grade__name' in d:
                q = q.filter(grade__name=d['grade__name'])
            d_new['class_count'] = q.count()
        else:
            d_new['class_count'] = -1  # 不计算

        if 'town__parent__name' in d:
            d_new['town_parent_name'] = d['town__parent__name']
        if 'town__name' in d:
            d_new['town_name'] = d['town__name']
        if 'school__name' in d:
            d_new['school_name'] = d['school__name']
        if 'grade__name' in d:
            d_new['grade_name'] = d['grade__name']
        if 'class_uuid__name' in d:
            d_new['class_name'] = d['class_uuid__name']
        if 'teacher__name' in d:
            d_new['teacher_name'] = d['teacher__name']
        if 'lesson_name' in d:
            d_new['lesson_name'] = d['lesson_name']
        d_new['lesson_count'] = d['lesson_count']
        d_new['total_time_used'] = d['total_time_used']
        ret.append(d_new)

    return ret


def new_time_used(o, cache_key, start_date, end_date, school_year, term_type):
    ret = []
    # 仅按乡镇，按学校，按年级时统计班级总数, 这样可以减少不需要统计时对数据库的操作
    if cache_key in ['time-used-by-grade', 'time-used-by-school', 'time-used-by-town', 'time-used-by-country']:
        calc_class = True
    else:
        calc_class = False

    for d in o:
        d_new = {}
        #l = models.TeacherLoginTimeCache.objects.all()
        if calc_class:
            q = models.Class.objects.all().exclude(grade__number=13)
            if school_year:
                q = q.filter(grade__term__school_year=school_year)
            if term_type:
                q = q.filter(grade__term__term_type=term_type)
            if start_date and end_date:
                s = parse_date(start_date)
                e = parse_date(end_date)
                s = datetime.datetime.combine(s, datetime.time.min)
                e = datetime.datetime.combine(e, datetime.time.max)
                cond = Q(grade__term__start_date__lte=s,
                         grade__term__end_date__gte=s)
                cond |= Q(grade__term__start_date__gte=s,
                          grade__term__end_date__lte=e)
                cond |= Q(grade__term__start_date__lte=e,
                          grade__term__end_date__gte=e)
                q = q.filter(cond)
            if 'class_uuid__grade__term__school__parent__parent__name' in d:
                q = q.filter(grade__term__school__parent__parent__name=d['class_uuid__grade__term__school__parent__parent__name'])
            if 'class_uuid__grade__term__school__parent__name' in d:
                q = q.filter(grade__term__school__parent__name=d['class_uuid__grade__term__school__parent__name'])
            if 'class_uuid__grade__term__school__name' in d:
                q = q.filter(grade__term__school__name=d['class_uuid__grade__term__school__name'])
            if 'class_uuid__grade__name' in d:
                q = q.filter(grade__name=d['class_uuid__grade__name'])
            d_new['class_count'] = q.count()
        else:
            d_new['class_count'] = -1  # 不计算

        if 'class_uuid__grade__term__school__parent__parent__name' in d:
            d_new['country_name'] = d['class_uuid__grade__term__school__parent__parent__name']
            #l = l.filter(town__parent__name=d['class_uuid__grade__term__school__parent__parent__name'])
        if 'class_uuid__grade__term__school__parent__name' in d:
            d_new['town_name'] = d['class_uuid__grade__term__school__parent__name']
            #l = l.filter(town__name=d['class_uuid__grade__term__school__parent__name'])
        if 'class_uuid__grade__term__school__name' in d:
            d_new['school_name'] = d['class_uuid__grade__term__school__name']
            #l = l.filter(school__name=d['class_uuid__grade__term__school__name'])
        if 'class_uuid__grade__name' in d:
            d_new['grade_name'] = d['class_uuid__grade__name']
            #l = l.filter(grade__name=d['class_uuid__grade__name'])
        if 'class_uuid__name' in d:
            d_new['class_name'] = d['class_uuid__name']
            #l = l.filter(class_uuid__name=d['class_uuid__name'])
        if 'teacher__name' in d:
            d_new['teacher_name'] = d['teacher__name']
        if 'teacher__pk' in d:
            d_new['teacher__pk'] = d['teacher__pk']
            #l = l.filter(teacher__name=d['teacher__name'])
        if 'lesson_name__name' in d:
            d_new['lesson_name'] = d['lesson_name__name']
            #l = l.filter(lesson_name=d['lesson_name__name'])
        if 'lesson_count' in d:
            d_new['lesson_count'] = d['lesson_count']
        else:
            l = models.TeacherLoginTimeCache.objects.all()
            if 'country_name' in d_new:
                l = l.filter(town__parent__name=d_new['country_name'])
            if 'town_name' in d_new:
                l = l.filter(town__name=d_new['town_name'])
            if 'school_name' in d_new:
                l = l.filter(school__name=d_new['school_name'])
            if 'grade_name' in d_new:
                l = l.filter(grade__name=d_new['grade_name'])
            if 'class_name' in d_new:
                l = l.filter(class_uuid__name=d_new['class_name'])
            if 'teacher_name' in d_new:
                l = l.filter(teacher__name=d_new['teacher_name'])
            if 'teacher__pk' in d_new:
                l = l.filter(teacher__pk=d_new['teacher__pk'])
            if 'lesson_name' in d_new:
                l = l.filter(lesson_name=d_new['lesson_name'])
            if school_year:
                l = l.filter(teacherlogintime__teacherloginlog__term_school_year=school_year)
            if term_type:
                l = l.filter(teacherlogintime__teacherloginlog__term_type=term_type)
            if start_date and end_date:
                s = parse_date(start_date)
                e = parse_date(end_date)
                s = datetime.datetime.combine(s, datetime.time.min)
                e = datetime.datetime.combine(e, datetime.time.max)
                l = l.filter(teacherlogintime__teacherloginlog__created_at__range=(s, e))
            d_new['lesson_count'] = l.count()

        if 'total_time_used' in d:
            d_new['total_time_used'] = d['total_time_used']
        else:
            l = models.TeacherLoginTimeCache.objects.all()
            if 'country_name' in d_new:
                l = l.filter(town__parent__name=d_new['country_name'])
            if 'town_name' in d_new:
                l = l.filter(town__name=d_new['town_name'])
            if 'school_name' in d_new:
                l = l.filter(school__name=d_new['school_name'])
            if 'grade_name' in d_new:
                l = l.filter(grade__name=d_new['grade_name'])
            if 'class_name' in d_new:
                l = l.filter(class_uuid__name=d_new['class_name'])
            if 'teacher_name' in d_new:
                l = l.filter(teacher__name=d_new['teacher_name'])
            if 'lesson_name' in d_new:
                l = l.filter(lesson_name=d_new['lesson_name'])
            if school_year:
                l = l.filter(teacherlogintime__teacherloginlog__term_school_year=school_year)
            if term_type:
                l = l.filter(teacherlogintime__teacherloginlog__term_type=term_type)
            if start_date and end_date:
                s = parse_date(start_date)
                e = parse_date(end_date)
                s = datetime.datetime.combine(s, datetime.time.min)
                e = datetime.datetime.combine(e, datetime.time.max)
                l = l.filter(teacherlogintime__teacherloginlog__created_at__range=(s, e))

            if l:
                d_new['total_time_used'] = l.aggregate(total=Sum('teacherlogintime__login_time'))['total']
            else:
                d_new['total_time_used'] = 0

        '''
        if l:
            #aa = l.aggregate(total_time_used=Sum('teacherlogintime__login_time'),lesson_count=Count('teacherlogintime__teacherloginlog',distinct=True))
            #d_new['lesson_count'] = aa['lesson_count']
            #d_new['total_time_used'] = aa['total_time_used']
            #d_new['lesson_count'] = l.values('teacherlogintime__teacherloginlog').distinct().count()
            d_new['total_time_used'] = l.aggregate(total_time_used=Sum('teacherlogintime__login_time'))['total_time_used']
        else:
            #d_new['lesson_count'] = 0
            d_new['total_time_used'] = 0
        '''
        ret.append(d_new)

    return ret
