# coding=utf-8
import os
import uuid
import logging
import datetime
from django.db.models import Sum, Q
from django.core.urlresolvers import reverse
from django.utils.dateparse import parse_date
from BanBanTong.db import models
from BanBanTong import constants
import xlwt
from BanBanTong.utils import decorator
from BanBanTong.utils import page_object
from BanBanTong.utils import create_success_dict
# from BanBanTong.views.statistic import teaching_time_old as old_views
from .utils import (sort_statistic, common_query_for_statistic, get_schedule_time)

logger = logging.getLogger(__name__)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def _query(request, node_type, export, sort_type=None):
    sort_type = sort_type or node_type
    objs, conditions = common_query_for_statistic(request, node_type)
    class_count = objs.aggregate(x=Sum('class_count'))['x']
    finished_time = objs.aggregate(x=Sum('teach_count'))['x']

    class_count = class_count and class_count or 0
    finished_time = finished_time and finished_time or 0
    if objs.exists():
        term_schedule_time = get_schedule_time(objs[0].school_year, objs[0].term_type)
    else:
        term_schedule_time = 0
    total = {
        'schedule_time': term_schedule_time * class_count,
        'finished_time': finished_time
    }

    objs1 = models.Statistic.get_items_descendants(objs, 'school')
    objs2 = models.Statistic.get_items_descendants(objs, 'class')
    total_extra = {
        'finished_rate_school': models.Statistic.rate_them(objs1, term_schedule_time),
        'finished_rate_class': models.Statistic.rate_them(objs2, term_schedule_time)
    }
    total.update(total_extra)

    objs = sort_statistic(objs, sort_type)

    # 按自然时间查询:
    # 既然按照学年学期和按照自然时间查询的时候,只是实际授课次数字段值不同
    # 那么可以直接先从Statistic表获取节点条目信息
    # 这样节点获取的效率会更高一点
    start_date = request.REQUEST.get('start_date')
    end_date = request.REQUEST.get('end_date')
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
        lst = [i.key for i in objs]
        d = {'%s__in' % key: lst}
        result = base_objs.filter(**d).count()
        total['finished_time'] = result

    try:
        total_percent = total['finished_time'] * 100.0 / total['schedule_time']
    except:
        total_percent = 0.0
    total['finished_rate'] = '%.2f%%' % total_percent

    paged_info = {'total': total}
    if not export:
        objs, paged_info = page_object(request, objs, total=total)

    # 然后呢,只是更新需要显示的那一部分的条目的数据,减少查询次数
    if start_date and end_date:
        for i in objs:
            key_name = i.type != 'class' and i.type or 'class_uuid'
            d = {key_name: i.key}
            result = base_objs.filter(**d).count()
            setattr(i, 'teach_count', result)

    return objs, term_schedule_time, paged_info


def _get_sth(obj, schedule_time):
    try:
        s = '%.2f%%' % (obj.teach_count * 100.0 / (obj.class_count * schedule_time))
    except ZeroDivisionError:
        s = '0.00%'
    except:
        s = ''
    return s


def _divmod(x, y):
    try:
        return '%.2f%%' % (x * 100.0 / y)
    except ZeroDivisionError:
        return '0.00%'
    except:
        return ''


def by_country(request, export=False):
    pass


def by_town(request, export=False):
    """班班通授课次数统计>按乡镇街道统计"""
    o, schedule_time, paged_info = _query(request, 'town', export)

    records = map(lambda i: {
        'class_total': i.class_count,
        'class_average': '{0:.2f}'.format(i.teach_count * 1.0 / (
            i.class_count and i.class_count or 1
        )),
        'town_name': i.name,
        "class_schedule_time": schedule_time,
        'schedule_time': i.class_count * schedule_time,
        'finished_time': i.teach_count,
        'finished_rate': _get_sth(i, schedule_time),
        'finished_rate_school': i.rate_me('school', schedule_time),
        'finished_rate_class': i.rate_me('class', schedule_time)
    }, o)
    if export:
        return records, paged_info['total']
    else:
        paged_info['records'] = records
    return create_success_dict(data=paged_info)


def by_school(request, export=False):
    """班班通授课次数统计>按学校统计"""
    o, schedule_time, paged_info = _query(request, 'school', export)
    del paged_info['total']['finished_rate_school']
    records = map(lambda i: {
        'town_name': i.parent.name,
        'school_name': i.name,
        'class_total': i.class_count,

        'schedule_time': i.class_count * schedule_time,
        "class_schedule_time": schedule_time,
        'finished_time': i.teach_count,
        'finished_rate': _get_sth(i, schedule_time),
        'finished_rate_class': i.rate_me('class', schedule_time),
        'class_average': '{0:.2f}'.format(i.teach_count * 1.0 / (
            i.class_count and i.class_count or 1
        )),
    }, o)
    if export:
        return records, paged_info['total']
    else:
        paged_info['records'] = records
    return create_success_dict(data=paged_info)


def by_grade(request, export=False):
    """班班通授课次数统计>按年级统计"""
    o, schedule_time, paged_info = _query(request, 'grade', export)
    del paged_info['total']['finished_rate_school']
    records = map(lambda i: {
        'town_name': i.parent.parent.name,
        'school_name': i.parent.name,
        'grade_name': i.name,
        'class_total': i.class_count,

        'schedule_time': i.class_count * schedule_time,
        "class_schedule_time": schedule_time,
        'finished_time': i.teach_count,
        'finished_rate': _get_sth(i, schedule_time),
        'finished_rate_class': i.rate_me('class', schedule_time),
        'class_average': '{0:.2f}'.format(i.teach_count * 1.0 / (
            i.class_count and i.class_count or 1
        )),
    }, o)
    if export:
        return records, paged_info['total']
    else:
        paged_info['records'] = records
    return create_success_dict(data=paged_info)


def by_class(request, export=False):
    """班班通授课次数统计>按班级统计"""
    o, schedule_time, paged_info = _query(request, 'class', export)
    del paged_info['total']['finished_rate_school']
    del paged_info['total']['finished_rate_class']
    records = map(lambda i: {
        'town_name': i.parent.parent.parent.name,
        'school_name': i.parent.parent.name,
        'grade_name': i.parent.name,
        'class_name': i.name,
        'class_total': i.class_count,
        'finished_rate': _get_sth(i, schedule_time),
        'schedule_time': i.class_count * schedule_time,
        "class_schedule_time": schedule_time,
        'finished_time': i.teach_count,
        'class_average': '{0:.2f}'.format(i.teach_count * 1.0 / (
            i.class_count and i.class_count or 1
        )),
    }, o)
    if export:
        return records, paged_info['total']
    else:
        paged_info['records'] = records
    return create_success_dict(data=paged_info)


def by_lesson(request, export=False):
    objs, schedule_time, paged_info = _query(request, 'lesson', export=export)


def by_lessonteacher(request, export=False):
    # return old_views.by_lessonteacher(request)
    """班班通授课次数统计>按班级教师课程统计"""
    all_objs, schedule_time, old_paged_info = _query(request, 'teacher', export=True, sort_type='lessonteacher')
    lt_pk = list(all_objs.values_list(
        'parent__parent__key', 'parent__key', 'key',  # 班级 课程 教师
    ).distinct())
    class_count = all_objs.exists() and all_objs.first().parent.parent.parent.parent.count_child('class') or 0
    if not export:
        lt_pk, paged_info = page_object(request, lt_pk)
    else:
        paged_info = old_paged_info
    paged_info['total'] = old_paged_info['total']
    paged_info['total']['schedule_time'] = schedule_time * class_count
    try:
        total_percent = paged_info['total']['finished_time'] * 100.0 / paged_info['total']['schedule_time']
    except:
        total_percent = 0.0
    paged_info['total']['finished_rate'] = '%.2f%%' % total_percent

    for i, lst in enumerate(lt_pk):
        if i == 0:
            cond = Q(parent__parent__key=lst[0], parent__key=lst[1], key=lst[2])
        else:
            cond |= Q(parent__parent__key=lst[0], parent__key=lst[1], key=lst[2])
    if cond:
        paged_objs = all_objs.filter(cond)
    else:
        paged_objs = all_objs.none()

    pk_lst = list(paged_objs.values_list('pk', flat=True))
    all_objs = all_objs.filter(pk__in=pk_lst)
    record_objs = all_objs.values(
        'parent__parent__parent__parent__parent__name',
        'parent__parent__parent__parent__name',
        'parent__parent__parent__name',
        'parent__parent__name',
        'parent__parent__key',
        'parent__name',
        'parent__key',
        'key',
        'name',
    ).annotate(teach_count_sum=Sum('teach_count')).distinct()
    records = map(lambda i: {
        'town_name': i['parent__parent__parent__parent__parent__name'],
        'school_name': i['parent__parent__parent__parent__name'],
        'grade_name': i['parent__parent__parent__name'],
        'class_name': i['parent__parent__name'],
        'lesson_name': i['parent__name'],
        'teacher_name': i['name'],
        'finished_time': i['teach_count_sum'],
        'schedule_time': schedule_time,
        'finished_rate': _divmod(i['teach_count_sum'], schedule_time),
    }, record_objs)
    if export:
        return records, paged_info['total']
    else:
        paged_info['records'] = records
    return create_success_dict(data=paged_info)


def by_teacher(request, export=False):
    # return old_views.by_teacher(request)
    """班班通授课次数统计>按教师统计"""
    all_objs, schedule_time, old_paged_info = _query(request, 'teacher', export=True)
    lt_pk = list(all_objs.values_list(  # 学校 教师
        'parent__parent__parent__parent__key', 'key'
    ).distinct())
    class_count = all_objs.exists() and all_objs.first().parent.parent.parent.parent.count_child('class') or 0
    if not export:
        lt_pk, paged_info = page_object(request, lt_pk)
    else:
        paged_info = old_paged_info
    paged_info['total'] = old_paged_info['total']
    paged_info['total']['schedule_time'] = schedule_time * class_count
    try:
        total_percent = paged_info['total']['finished_time'] * 100.0 / paged_info['total']['schedule_time']
    except:
        total_percent = 0.0
    paged_info['total']['finished_rate'] = '%.2f%%' % total_percent

    for i, lst in enumerate(lt_pk):
        if i == 0:
            cond = Q(parent__parent__parent__parent__key=lst[0], key=lst[1])
        else:
            cond |= Q(parent__parent__parent__parent__key=lst[0], key=lst[1])
    if cond:
        paged_objs = all_objs.filter(cond)
    else:
        paged_objs = all_objs.none()

    pk_lst = list(paged_objs.values_list('pk', flat=True))
    all_objs = all_objs.filter(pk__in=pk_lst)
    record_objs = all_objs.values(  # 街道 学校 教师
        'parent__parent__parent__parent__parent__name',
        'parent__parent__parent__parent__name',
        'name',
    ).annotate(teach_count_sum=Sum('teach_count')).distinct()
    records = map(lambda i: {
        'town_name': i['parent__parent__parent__parent__parent__name'],
        'school_name': i['parent__parent__parent__parent__name'],
        'teacher_name': i['name'],
        'finished_time': i['teach_count_sum'],
        'schedule_time': schedule_time,
        'finished_rate': _divmod(i['teach_count_sum'], schedule_time),

    }, record_objs)
    if export:
        return records, paged_info['total']
    else:
        paged_info['records'] = records
    return create_success_dict(data=paged_info)


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
                sheet.write(row, i, record[k])
            row += 1

        sheet.write(row, dict_keys.index('finished_time') - 1, '合计')
        for k in total:
            if k.startswith('#') or not k in dict_keys:
                continue
            sheet.write(row, dict_keys.index(k), total[k])

    xls.save(tmp_file)
    d = {
        'town': u'乡镇街道',
        'school': u'学校',
        'grade': u'年级',
        'class': u'班级'
    }
    filename = u'教师授课次数比例统计_按%s导出.xls' % d[node_type]
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
        u'班级平均授课数',
        u'实际授课总数',
        u'计划达标授课数/班级',
        u'计划达标授课总数（学期）',
        u'授课达标占比（%）',
        u'学校达标率（%）',
        u'班级达标率（%）'
    )
    dict_keys = (
        'town_name',
        'class_total',
        'class_average',
        'finished_time',
        'class_schedule_time',
        'schedule_time',
        'finished_rate',
        'finished_rate_school',
        'finished_rate_class'
    )
    return _export(excel_header, dict_keys, records, total, 'town')


def by_school_export(request):
    records, total = by_school(request, True)
    excel_header = (
        u'街道乡镇',
        u'学校',
        u'班级总数',
        u'班级平均授课数',
        u'实际授课总数',
        u'计划达标授课数/班级',
        u'计划达标授课总数（学期）',
        u'授课达标占比（%）',
        u'班级达标率（%）'
    )
    dict_keys = (
        'town_name',
        'school_name',
        'class_total',
        'class_average',
        'finished_time',
        'class_schedule_time',
        'schedule_time',
        'finished_rate',
        'finished_rate_class'
    )
    return _export(excel_header, dict_keys, records, total, 'school')


def by_grade_export(request):
    records, total = by_grade(request, True)
    excel_header = (
        u'街道乡镇',
        u'学校',
        u'年级',
        u'班级总数',
        u'班级平均授课数',
        u'实际授课总数',
        u'计划达标授课数/班级',
        u'计划达标授课总数（学期）',
        u'授课达标占比（%）',
        u'班级达标率（%）'
    )
    dict_keys = (
        'town_name',
        'school_name',
        'grade_name',
        'class_total',
        'class_average',
        'finished_time',
        'class_schedule_time',
        'schedule_time',
        'finished_rate',
        'finished_rate_class'
    )
    return _export(excel_header, dict_keys, records, total, 'grade')


def by_class_export(request):
    records, total = by_class(request, True)
    excel_header = (
        '街道乡镇',
        '学校',
        '年级',
        '班级',
        '实际授课总数',
        '计划达标授课总数（学期）',
        '授课达标占比（%）'
    )
    dict_keys = (
        'town_name',
        'school_name',
        'grade_name',
        'class_name',
        'finished_time',
        'schedule_time',
        'finished_rate',
    )
    return _export(excel_header, dict_keys, records, total, 'class')


def by_teacher_export(request):
    records, total = by_teacher(request, True)
    excel_header = (
        '街道乡镇',
        '学校',
        '教师',
        '实际授课总数',
        '计划达标授课总数（学期）',
        '授课达标占比（%）'
    )
    dict_keys = (
        'town_name',
        'school_name',
        'teacher_name',
        'finished_time',
        'schedule_time',
        'finished_rate',
    )
    return _export(excel_header, dict_keys, records, total, 'class')


def by_lessonteacher_export(request):
    records, total = by_lessonteacher(request, True)
    excel_header = (
        '街道乡镇',
        '学校',
        '年级',
        '班级',
        '教师',
        '课程',
        '实际授课总数',
        '计划达标授课总数（学期）',
        '授课达标占比（%）'
    )
    dict_keys = (
        'town_name',
        'school_name',
        'grade_name',
        'class_name',
        'teacher_name',
        'lesson_name',
        'finished_time',
        'schedule_time',
        'finished_rate',
    )
    return _export(excel_header, dict_keys, records, total, 'class')
