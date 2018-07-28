# coding=utf-8
import logging
import datetime
from django.utils.dateparse import parse_date
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import format_record
from BanBanTong.utils import get_page_info
from BanBanTong.utils import is_admin
from BanBanTong.utils import model_list_to_dict
from BanBanTong.utils import mongo
from BanBanTong.utils import page_object
logger = logging.getLogger(__name__)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('logged_in')
def grid_data(request, *args, **kwargs):
    '''使用记录->班班通登录日志'''
    page_info = get_page_info(request)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    lesson_period = request.GET.get('lesson_period')
    country_name = request.GET.get('country_name')
    town_name = request.GET.get('town_name')
    school_name = request.GET.get('school_name')
    grade_name = request.GET.get('grade_name')
    class_name = request.GET.get('class_name')
    lesson_name = request.GET.get('lesson_name')
    teacher_name = request.GET.get('teacher_name')
    only_computerclass = kwargs.get('cc', False)
    if not end_date and not lesson_period \
            and not grade_name and not class_name and not lesson_name \
            and not teacher_name and not town_name and not school_name \
            and not country_name:
        e = parse_date(end_date)
        if e == datetime.date.today():
            data = force_index_query(page_info)
            return create_success_dict(data=data)

    t = models.TeacherLoginLog.objects.all()
    if only_computerclass:
        logs_base = models.TeacherLoginLogTag.objects.all()
        cc_name = request.GET.get('class_name',
                                  request.GET.get('name',
                                                  request.GET.get('grade_name')))
        if cc_name:
            logs_base = logs_base.filter(created_at__name=cc_name)
        t = t.filter(teacherloginlogtag__in=logs_base)

    if start_date and end_date:
        s = parse_date(start_date)
        e = parse_date(end_date) + datetime.timedelta(days=1)
        s = datetime.datetime.combine(s, datetime.time())
        e = datetime.datetime.combine(e, datetime.time())
        t = t.filter(created_at__range=(s, e))
    if lesson_period:
        t = t.filter(lesson_period_sequence=lesson_period)
    if grade_name and not only_computerclass:
        t = t.filter(grade_name=grade_name)
    if class_name and not only_computerclass:
        t = t.filter(class_name=class_name)

    if lesson_name:
        t = t.filter(lesson_name__contains=lesson_name)
    if teacher_name:
        t = t.filter(teacher_name__contains=teacher_name)
    if country_name:
        t = t.filter(country_name=country_name)
    if town_name:
        t = t.filter(town_name=town_name)
    if school_name:
        t = t.filter(school_name=school_name)

    if not is_admin(request.current_user):
        permitted_groups = request.current_user.permitted_groups.all()
        uuids = [g.uuid for g in permitted_groups]
        t = t.filter(school__uuid__in=uuids)
    t = t.order_by('-created_at')

    # 这是老的方法
    '''
    values = t.values('province_name', 'city_name',
                      'country_name', 'town_name',
                      'school_name', 'grade_name',
                      'class_name', 'teacher_name',
                      'lesson_period_sequence',
                      'lesson_name',
                      'created_at', 'teacherlogintime__login_time',
                      'teacherlogintimetemp')
    '''
    '''
        这个方法有几个严重的性能问题：
        1. teacherlogintime__login_time和teacherlogintimetemp在其他表里，
           获取values会导致两次LEFT OUTER JOIN
        2. 获取record_count时，SQL语句是SELECT COUNT(*) FROM (SELECT ...) subquery，
           MySQL对subquery的优化很差（MariaDB可以解决此问题）
        3. 上述两点相加导致查询时获取了大量无用数据
        程序上的解决办法是：
        1. QuerySet.values()只获取TeacherLoginLog的字段，其他字段通过format_record取得，
           每个页面只需要取25条相关数据
        2. record_count只使用TeacherLoginLog计算
    '''
    if only_computerclass:
        values = t.values('uuid', 'town_name',
                          'school_name',
                          'grade_name', 'class_name',
                          'teacher_name',
                          'lesson_period_sequence',
                          'lesson_name',
                          'created_at',

                          'teacherloginlogtag__created_at__grade__name',
                          'teacherloginlogtag__created_at__name')
    else:
        values = t.values('uuid', 'town_name',
                          'school_name', 'grade_name',
                          'class_name', 'teacher_name',
                          'lesson_period_sequence',
                          'lesson_name',
                          'created_at')
    # changed at 2015-01-23 add 'total'
    records, data = page_object(request, values)
    records = format_record.activity_logged_in_new(records)
    data['total'] = t.count()
    data['records'] = list(records)
    return create_success_dict(data=data)


def force_index_query(page_info):
    timelog = []
    timelog.append({'start': str(datetime.datetime.now())})
    sql = '''SELECT uuid, province_name, city_name,
             country_name, town_name, school_name, grade_name,
             class_name, teacher_name, lesson_period_sequence,
             lesson_name, created_at
             FROM TeacherLoginLog
             FORCE INDEX (TeacherLoginLog_96511a37)
             ORDER BY created_at DESC
             LIMIT %s OFFSET %s'''
    limit = page_info['page_size']
    offset = limit * (page_info['page_num'] - 1)
    q = models.TeacherLoginLog.objects.raw(sql, [limit, offset])
    timelog.append({'1': str(datetime.datetime.now())})

    count = models.TeacherLoginLog.objects.count()
    timelog.append({'2': str(datetime.datetime.now())})
    records = model_list_to_dict(q)
    timelog.append({'3': str(datetime.datetime.now())})
    if page_info['page_num'] != 1:
        records = format_record.activity_logged_in_force_index(records)
        timelog.append({'4': str(datetime.datetime.now())})
    data = {
        'records': records,
        'page': 1,
        'page_size': 25,
        'record_count': count,
        'page_count': (count + 25) / 25,
        'timelog': timelog,
    }
    timelog.append({'end': str(datetime.datetime.now())})
    return data


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('logged_in')
def get(request):
    if constants.BANBANTONG_USE_MONGODB:
        return mongo.get_teacherloginlog(request)
    else:
        return grid_data(request)


@decorator.authorized_user_with_redirect
#@decorator.authorized_privilege('computer_room_logged_in')
@decorator.authorized_privilege('logged_in')
def computerclass_loged_info(request, *args, **kwargs):
    """使用记录>电脑教室登录日志"""

    return grid_data(request, cc=True)
