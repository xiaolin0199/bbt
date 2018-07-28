# coding=utf-8
import datetime
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from BanBanTong.utils import decorator
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import is_admin
from BanBanTong.utils import get_page_info
from BanBanTong.utils import model_list_to_dict
from BanBanTong.db import models


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('not_logged_in')
def grid_data(request, *args, **kwargs):
    '''使用记录->班班通未登录日志'''
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

    if not end_date and not lesson_period \
            and not grade_name and not class_name and not lesson_name \
            and not teacher_name and not town_name and not school_name \
            and not country_name:
        e = parse_date(end_date)
        if e == datetime.date.today():
            data = force_index_query(page_info)
            return create_success_dict(data=data)

    t = models.TeacherAbsentLog.objects.all()
    if start_date and end_date:
        s = parse_date(start_date)
        e = parse_date(end_date) + datetime.timedelta(days=1)
        s = datetime.datetime.combine(s, datetime.time())
        e = datetime.datetime.combine(e, datetime.time())
        t = t.filter(created_at__range=(s, e))
    if lesson_period:
        t = t.filter(lesson_period_sequence=lesson_period)
    if grade_name:
        t = t.filter(grade_name=grade_name)
    if class_name:
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

    values = t.values('province_name', 'city_name',
                      'country_name', 'town_name',
                      'school_name', 'grade_name',
                      'class_name', 'teacher_name',
                      'lesson_period_sequence',
                      'lesson_name',
                      'created_at')
    paginator = Paginator(values, page_info['page_size'])
    records = list(paginator.page(page_info['page_num']).object_list)
    page = page_info['page_num']
    page_size = page_info['page_size']
    record_count = paginator.count
    page_count = paginator.num_pages
    return create_success_dict(data={
        'records': records,
        'page': page,
        'page_size': page_size,
        'record_count': record_count,
        'page_count': page_count,
    })


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('not_logged_in')
def force_index(request, *args, **kwargs):
    '''使用记录->班班通未登录日志'''
    page_info = get_page_info(request)
    sql = '''SELECT uuid, province_name, city_name, country_name, town_name,
             school_name, grade_name, class_name, teacher_name,
             lesson_period_sequence, lesson_name, created_at
             FROM TeacherAbsentLog FORCE INDEX
             (TeacherAbsentLog_96511a37) ORDER BY created_at DESC
             LIMIT %s OFFSET %s'''
    limit = page_info['page_size']
    offset = limit * (page_info['page_num'] - 1)
    q = models.TeacherAbsentLog.objects.raw(sql, [limit, offset])

    count = models.TeacherAbsentLog.objects.count()
    return create_success_dict(data={
        'records': model_list_to_dict(q),
        'page': 1,
        'page_size': 25,
        'record_count': count,
        'page_count': (count + 25) / 25,
    })


def force_index_query(page_info):
    timelog = []
    timelog.append({'start': str(datetime.datetime.now())})
    sql = '''SELECT uuid, province_name, city_name, country_name, town_name,
             school_name, grade_name, class_name, teacher_name,
             lesson_period_sequence, lesson_name, created_at
             FROM TeacherAbsentLog FORCE INDEX
             (TeacherAbsentLog_96511a37) ORDER BY created_at DESC
             LIMIT %s OFFSET %s'''
    limit = page_info['page_size']
    offset = limit * (page_info['page_num'] - 1)
    q = models.TeacherAbsentLog.objects.raw(sql, [limit, offset])
    timelog.append({'1': str(datetime.datetime.now())})

    count = models.TeacherAbsentLog.objects.count()
    timelog.append({'2': str(datetime.datetime.now())})
    records = model_list_to_dict(q)
    timelog.append({'3': str(datetime.datetime.now())})
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
