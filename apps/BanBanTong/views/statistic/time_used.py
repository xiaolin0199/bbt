# coding=utf-8
import datetime
import os
import uuid
from django.core.urlresolvers import reverse
from django.db.models import Sum
from django.utils.dateparse import parse_date
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.utils import page_object
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
import xlwt
from BanBanTong.views.statistic import time_used_old as old_views
from .utils import (sort_statistic, common_query_for_statistic)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('time_used_statistic')
def _query(request, node_type, export):
    o, conditions = common_query_for_statistic(request, node_type)
    class_count = o.aggregate(x=Sum('class_count'))['x']
    finished_time = o.aggregate(x=Sum('teach_count'))['x']
    teach_time = o.aggregate(x=Sum('teach_time'))['x']

    class_count = class_count and class_count or 0
    finished_time = finished_time and finished_time or 0
    teach_time = teach_time and teach_time or 0
    o = sort_statistic(o, node_type)

    total = {
        # 'total_time_used': _divmod(teach_time, 1)
        'total_time_used': teach_time
    }

    # hack 按自然时间查询的合计栏:
    # 既然按照学年学期和按照自然时间查询的时候,只是实际授课次数字段值不同
    # 那么可以直接先从Statistic表获取节点数据,然后更新一下授课时长字段值
    # 这样节点获取的效率会更高一点
    start_date = request.REQUEST.get('start_date', None)
    end_date = request.REQUEST.get('end_date', None)
    if start_date and end_date:
        d = {}
        if 'school_year' in conditions:
            d['term_school_year'] = conditions['school_year']
        if 'term_type' in conditions:
            d['term_type'] = conditions['term_type']

        base_objs = models.TeacherLoginLog.objects.filter(**d)

        s = parse_date(start_date)
        e = parse_date(end_date)
        s = datetime.datetime.combine(s, datetime.time.min)
        e = datetime.datetime.combine(e, datetime.time.max)
        base_objs = base_objs.filter(created_at__range=(s, e))

        key = node_type != 'class' and node_type or 'class_uuid'
        lst = [i.key for i in o]
        d2 = {'%s__in' % key: lst}
        objs = base_objs.filter(**d2)
        #result = objs.aggregate(x=Sum('lesson_period_sequence'))['x']
        if 'login_time' in models.TeacherLoginLog._meta.get_all_field_names():
            result = objs.aggregate(x=Sum('login_time'))['x']
        else:
            objs = objs.values('uuid')
            result = models.TeacherLoginTime.objects.filter(school_year=d['term_school_year'], term_type=d['term_type'],
                                                            teacherloginlog_id__in=objs).aggregate(x=Sum('login_time'))['x']
        result = result and result or 0
        total['total_time_used'] = result

    paged_info = {'total': total}
    if not export:
        o, paged_info = page_object(request, o, total=total)

    # hack
    # 然后呢,只是更新需要显示的那一部分的条目的数据,减少查询次数
    if start_date and end_date:
        for i in o:
            key = i.type != 'class' and i.type or 'class_uuid'
            d2 = {key: i.key}
            objs = base_objs.filter(**d2)
            result = objs.count()
            setattr(i, 'teach_count', result)
            #result = objs.aggregate(x=Sum('lesson_period_sequence'))['x']
            if 'login_time' in models.TeacherLoginLog._meta.get_all_field_names():
                result = objs.aggregate(x=Sum('login_time'))['x']
            else:
                objs = objs.values('uuid')
                result = models.TeacherLoginTime.objects.filter(school_year=d['term_school_year'], term_type=d['term_type'],
                                                                teacherloginlog_id__in=objs).aggregate(x=Sum('login_time'))['x']
            result = result and result or 0
            # setattr(i, 'teach_time', _divmod(result, 1))
            setattr(i, 'teach_time', result)

    return o, paged_info


def _divmod(x, y):
    try:
        y = y and y or 1
        result = '%.2f' % (x / 60.0 / y)
        return float(result)
    except:
        return 0.00


def by_country(request, export=False):
    pass


def by_town(request, export=False):
    """班班通授课时长统计>按乡镇街道统计"""
    o, paged_info = _query(request, 'town', export)
    records = map(lambda i: {
        'town_name': i.name,
        'class_count': i.class_count,
        'lesson_count': i.teach_count,
        # 'time_used_average': _divmod(i.teach_time, i.teach_count),
        'total_time_used': i.teach_time,
    }, o)
    if export:
        return records, paged_info['total']
    else:
        paged_info['records'] = records
        paged_info['total_time_used'] = paged_info['total']['total_time_used']
    return create_success_dict(data=paged_info)


def by_school(request, export=False):
    o, paged_info = _query(request, 'school', export)
    records = map(lambda i: {
        'town_name': i.parent.name,
        'school_name': i.name,
        'class_count': i.class_count,
        'lesson_count': i.teach_count,
        # 'time_used_average': _divmod(i.teach_time, i.teach_count),
        'total_time_used': i.teach_time,
    }, o)
    if export:
        return records, paged_info['total']
    else:
        paged_info['records'] = records
        paged_info['total_time_used'] = paged_info['total']['total_time_used']
    return create_success_dict(data=paged_info)


def by_grade(request, export=False):
    o, paged_info = _query(request, 'grade', export)
    records = map(lambda i: {
        'town_name': i.parent.parent.name,
        'school_name': i.parent.name,
        'grade_name': i.name,
        'class_count': i.class_count,
        'lesson_count': i.teach_count,
        # 'time_used_average': _divmod(i.teach_time, i.teach_count),
        'total_time_used': i.teach_time,
    }, o)
    if export:
        return records, paged_info['total']
    else:
        paged_info['records'] = records
        paged_info['total_time_used'] = paged_info['total']['total_time_used']
    return create_success_dict(data=paged_info)


def by_class(request, export=False):
    o, paged_info = _query(request, 'class', export)
    records = map(lambda i: {
        'town_name': i.parent.parent.parent.name,
        'school_name': i.parent.parent.name,
        'grade_name': i.parent.name,
        'class_name': i.name,
        'class_count': i.class_count,
        'lesson_count': i.teach_count,
        # 'time_used_average': _divmod(i.teach_time, i.teach_count),
        'total_time_used': i.teach_time,
    }, o)
    if export:
        return records, paged_info['total']
    else:
        paged_info['records'] = records
        paged_info['total_time_used'] = paged_info['total']['total_time_used']
    return create_success_dict(data=paged_info)


def by_teacher(request, export=False):
    return old_views.by_teacher(request)


def by_lessonteacher(request, export=False):
    return old_views.by_lessonteacher(request)


def _export(excel_header, dict_keys, records, total, node_type):
    cached_id = str(uuid.uuid1())
    tmp_file = os.path.join(constants.CACHE_TMP_ROOT, cached_id)
    xls = xlwt.Workbook(encoding='utf8')
    sheet = xls.add_sheet(node_type)

    for i, v in enumerate(excel_header):
        sheet.write(0, i, v)

    row = 1
    if records:
        for record in records:
            for i, k in enumerate(dict_keys):
                if k == 'time_used_average':
                    sheet.write(row, i, _divmod(record['total_time_used'], record['lesson_count']))
                elif k == 'total_time_used':
                    sheet.write(row, i, _divmod(record['total_time_used'], 1))
                else:
                    sheet.write(row, i, record[k])
            row += 1

        sheet.write(row, dict_keys.index('total_time_used') - 1, '合计')
        for k in total:
            if k.startswith('#') or not k in dict_keys:
                continue
            if k == 'total_time_used':
                sheet.write(row, dict_keys.index(k), _divmod(total[k], 1))
            else:
                sheet.write(row, dict_keys.index(k), total[k])

    xls.save(tmp_file)
    d = {
        'town': u'乡镇街道',
        'school': u'学校',
        'grade': u'年级',
        'class': u'班级'
    }
    filename = u'教师授课时长统计_按%s导出.xls' % d[node_type]
    xls.save(tmp_file)

    return create_success_dict(
        url=reverse('base:xls_download',
                    kwargs={'cached_id': cached_id, 'name': filename})
    )


def by_country_export(request):
    pass


def by_town_export(request):
    records, total = by_town(request, True)
    excel_header = (
        u'街道乡镇',
        u'班级总数',
        u'授课节次总数',
        u'平均时长/节次(分钟)',
        u'总授课时长(分钟)'
    )
    dict_keys = (
        'town_name',
        'class_count',
        'lesson_count',
        'time_used_average',
        'total_time_used'
    )
    return _export(excel_header, dict_keys, records, total, 'town')


def by_school_export(request):
    records, total = by_school(request, True)
    excel_header = (
        u'街道乡镇',
        u'学校',
        u'班级总数',
        u'授课节次总数',
        u'平均时长/节次(分钟)',
        u'总授课时长(分钟)'
    )
    dict_keys = (
        'town_name',
        'school_name',
        'class_count',
        'lesson_count',
        'time_used_average',
        'total_time_used'
    )
    return _export(excel_header, dict_keys, records, total, 'school')


def by_grade_export(request):
    records, total = by_grade(request, True)
    excel_header = (
        u'街道乡镇',
        u'学校',
        u'年级',
        u'班级总数',
        u'授课节次总数',
        u'平均时长/节次(分钟)',
        u'总授课时长(分钟)'
    )
    dict_keys = (
        'town_name',
        'school_name',
        'grade_name',
        'class_count',
        'lesson_count',
        'time_used_average',
        'total_time_used'
    )
    return _export(excel_header, dict_keys, records, total, 'school')


def by_class_export(request):
    records, total = by_class(request, True)
    excel_header = (
        u'街道乡镇',
        u'学校',
        u'年级',
        u'班级',
        u'授课节次总数',
        u'平均时长/节次(分钟)',
        u'总授课时长(分钟)'
    )
    dict_keys = (
        'town_name',
        'school_name',
        'grade_name',
        'class_name',
        'lesson_count',
        'time_used_average',
        'total_time_used'
    )
    return _export(excel_header, dict_keys, records, total, 'school')


def by_teacher_export(request, *args, **kwargs):
    return old_views.by_teacher_export(request, *args, **kwargs)


def by_lessonteacher_export(request, *args, **kwargs):
    return old_views.by_lessonteacher_export(request, *args, **kwargs)
