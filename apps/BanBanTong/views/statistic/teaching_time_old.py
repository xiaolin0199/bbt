# coding=utf-8
import os
import uuid
import datetime
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.db.models import Sum
from django.utils.dateparse import parse_date

from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import format_record
from BanBanTong.utils import get_page_info
import xlwt


def _format_no_lessonteacher_class(querysets, node_type, **kwargs):
    """该函数用于处理没有分配过授课教师的班级在授课次数统计中被漏掉的问题"""
    server_type = models.Setting.getvalue('server_type')
    if server_type == 'school':
        return []
    querysets = querysets.order_by('grade__number', 'number')
    if not querysets.exists():
        return []
    if node_type in ['country', 'town', 'school']:
        return []

    if node_type == 'schoolgrade':
        records = kwargs.get('records', None)
        if records:
            excludes = map(lambda i: i['grade_name'], records)
            querysets = querysets.exclude(grade__name__in=excludes)
        grades = list(set(querysets.values_list('grade__name', flat=True)))
        ret = []
        for grade in grades:
            c = querysets.filter(grade__name=grade)
            if not c.exists():
                continue
            d = {}
            d['country_name'] = c[0].grade.term.school.parent.parent.name
            d['town_name'] = c[0].grade.term.school.parent.name
            d['school_name'] = c[0].grade.term.school.name
            d['grade_name'] = grade
            d['class_total'] = c.distinct().count()
            d['schedule_time'] = c.aggregate(x=Sum('grade__term__schedule_time'))['x']
            if not d['schedule_time']:
                d['schedule_time'] = 0
            d['class_schedule_time'] = c[0].grade.term.schedule_time
            d['finished_time'] = '0'
            d['finished_rate'] = '%0.2f' % (d['finished_time'] * 1.0 / d['schedule_time'])
            d['class_average'] = '0.00'
            ret.append(d)
        return ret

    if node_type == 'class':
        return map(lambda c: {
            "finished_rate": '0.00%%',
            "finished_time": 0,
            "class_name": c.name,
            "school_name": c.grade.term.school.name,
            "town_name": c.grade.term.school.parent.name,
            "schedule_time": c.grade.term.schedule_time,
            "grade_name": c.grade.name,
        }, querysets)

    if node_type in ['teacher', 'lessonteacher']:
        # 按照教师或班级授课教师统计的时候不统计没有分配教师的班级
        return []


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def _query(request, node_type):
    """
        教师授课次数统计:
        计划授课次数计算方法:
            1 从LessonTeacher中计算已经分配过教师的年级班级
            2 从Class中计算没有分配过教师的年级班级

        实际授课次数:
            1 从TeacherLoginLog中计算

    """
    country_name = request.REQUEST.get('country_name')
    town_name = request.REQUEST.get('town_name')
    school_name = request.REQUEST.get('school_name')
    grade_name = request.REQUEST.get('grade_name')
    class_name = request.REQUEST.get('class_name')
    lesson_name = request.REQUEST.get('lesson_name')
    teacher_name = request.REQUEST.get('teacher_name', '').strip()
    school_year = request.REQUEST.get('school_year')
    term_type = request.REQUEST.get('term_type')
    start_date = request.REQUEST.get('start_date')
    end_date = request.REQUEST.get('end_date')

    q = models.LessonTeacher.objects.filter(teacher__deleted=False)
    l = models.TeacherLoginLog.objects.filter(
        teacher__deleted=False,
        # lesson_teacher__isnull=False
    )
    klass = models.Class.objects.all().exclude(grade__number=13)  # 不统计电脑教室
    uuids = q.values_list('class_uuid', flat=True)
    c = klass.exclude(uuid__in=uuids)  # 尚未分配过授课教师的所有班级

    if country_name:
        q = q.filter(class_uuid__grade__term__school__parent__parent__name=country_name)
        c = c.filter(grade__term__school__parent__parent__name=country_name)
        l = l.filter(country_name=country_name)
    if town_name:
        q = q.filter(class_uuid__grade__term__school__parent__name=town_name)
        c = c.filter(grade__term__school__parent__name=town_name)
        l = l.filter(town_name=town_name)
    if school_name:
        q = q.filter(class_uuid__grade__term__school__name=school_name)
        c = c.filter(grade__term__school__name=school_name)
        l = l.filter(school_name=school_name)
    if grade_name:
        q = q.filter(class_uuid__grade__name=grade_name)
        c = c.filter(grade__name=grade_name)
        l = l.filter(grade_name=grade_name)
    if class_name:
        q = q.filter(class_uuid__name=class_name)
        c = c.filter(name=class_name)
        l = l.filter(class_name=class_name)

    # 这里班级的筛选只能通过LessonTeacher表和TeacherLoginLog表
    # lesson_name 和teacher_name 只是在按授课教师和课程统计中会用到
    if lesson_name:
        q = q.filter(lesson_name__name=lesson_name)
        l = l.filter(lesson_name=lesson_name)
    if teacher_name:
        q = q.filter(teacher__name__icontains=teacher_name)
        l = l.filter(teacher_name__icontains=teacher_name)

    if start_date and end_date:
        # 按自然日期查询
        s = parse_date(start_date)
        e = parse_date(end_date)
        s = datetime.datetime.combine(s, datetime.time.min)
        e = datetime.datetime.combine(e, datetime.time.max)
        # 按自然日期查询的话，计划授课总次数取整到学期
        cond = Q(class_uuid__grade__term__start_date__lte=s,
                 class_uuid__grade__term__end_date__gte=s)
        cond |= Q(class_uuid__grade__term__start_date__gte=s,
                  class_uuid__grade__term__end_date__lte=e)
        cond |= Q(class_uuid__grade__term__start_date__lte=e,
                  class_uuid__grade__term__end_date__gte=e)
        q = q.filter(cond)

        cond = Q(grade__term__start_date__lte=s,
                 grade__term__end_date__gte=s)
        cond |= Q(grade__term__start_date__gte=s,
                  grade__term__end_date__lte=e)
        cond |= Q(grade__term__start_date__lte=e,
                  grade__term__end_date__gte=e)
        c = c.filter(cond)
        l = l.filter(created_at__range=(s, e))
    else:
        if not school_year and not term_type:
            t = models.NewTerm.get_nearest_term()
            if t:
                school_year = t.school_year
                term_type = t.term_type

        if school_year:
            q = q.filter(class_uuid__grade__term__school_year=school_year)
            c = c.filter(grade__term__school_year=school_year)
            l = l.filter(term_school_year=school_year)
        if term_type:
            q = q.filter(class_uuid__grade__term__term_type=term_type)
            c = c.filter(grade__term__term_type=term_type)
            l = l.filter(term_type=term_type)
            if school_year:
                term = models.Term.objects.filter(school_year=school_year,
                                                  term_type=term_type)
                if term.exists():
                    term = term[0]

    total_schedule = q.aggregate(x=Sum('schedule_time'))['x']
    total_schedule = total_schedule and total_schedule or 0
    total_finish = l.count()

    total = {
        'schedule_time': total_schedule,
        'finished_time': total_finish,
        "finished_rate": '%.2f%%' % (total_finish * 100.0 / (total_schedule and total_schedule or 1)),
        'finished_rate_class': 'Tomorrow will be ok',
        'finished_rate_school': 'Tomorrow will be ok',
    }

    return q, c, total


def _result(request, fields, format_func, node_type, export):
    page_info = get_page_info(request)
    start_date = request.REQUEST.get('start_date')
    end_date = request.REQUEST.get('end_date')
    school_year = request.REQUEST.get('school_year')
    term_type = request.REQUEST.get('term_type')
    q, c, total = _query(request, node_type)
    q = q.values(*fields).distinct()
    q = q.annotate(a=Sum('finished_time'), group_schedule=Sum('schedule_time'))
    paginator = None
    if not export:
        paginator = Paginator(q, page_info['page_size'])
        records = list(paginator.page(page_info['page_num']).object_list)
    else:
        records = q

    # fix qcbug:557
    if node_type in ['lessonteacher', 'teacher']:
        d = {}
        for i, v in enumerate(list(records)):
            if not d.has_key(v['teacher__name']):
                d[v['teacher__name']] = [i]
            else:
                d[v['teacher__name']].append(i)

        for k in d:
            if len(d[k]) > 1:
                lst = []
                for i in d[k]:
                    value = '%s(%s)' % (
                        records[i]['teacher__name'],
                        records[i]['teacher__birthday'].strftime('%m%d')
                    )
                    lst.append(value)
                if len(set(lst)) == 1:
                    continue
                for i in d[k]:
                    value = '%s(%s)' % (
                        records[i]['teacher__name'],
                        records[i]['teacher__birthday'].strftime('%m%d')
                    )
                    records[i]['teacher__name'] = value

    records = format_func(records, start_date, end_date,
                          school_year=school_year, term_type=term_type)

    # records_2 = _format_no_lessonteacher_class(c, node_type, records=records)
    # if records_2:
    #    records = records + records_2
    ret = create_success_dict(data={
        'page': page_info['page_num'],
        'page_count': paginator and paginator.num_pages or 0,
        'page_size': page_info['page_size'],
        'record_count': paginator and paginator.count or 0,
        'records': records,
        'total': total,
    })
    return ret


def by_teacher(request, export=False):
    fields = (
        'class_uuid__grade__term__school__parent__name',
        'class_uuid__grade__term__school__name',
        'teacher__name',
        'teacher__birthday',
        'teacher__pk',
    )
    ret = _result(request, fields, format_record.teaching_time,
                  'teacher', export)
    return ret


def by_lessonteacher(request, export=False):
    fields = (
        'class_uuid__grade__term__school__parent__name',
        'class_uuid__grade__term__school__name',
        'class_uuid__grade__name',
        'class_uuid__name',
        'teacher__name',
        'teacher__birthday',
        'lesson_name__name',
        'schedule_time'
    )
    ret = _result(request, fields, format_record.teaching_time,
                  'lessonteacher', export)
    return ret


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
        'class': u'班级',
        'teacher': u'教师',
        'lessonteacher': u'班级课程教师'
    }
    filename = u'教师授课次数比例统计_按%s导出.xls' % d[node_type]
    xls.save(tmp_file)

    return create_success_dict(
        url=reverse('base:xls_download',
                    kwargs={'cached_id': cached_id, 'name': filename})
    )


def by_teacher_export(request, *args, **kwargs):
    ret = by_teacher(request, True)['data']
    records, total = ret['records'], ret['total']
    excel_header = [
        '街道乡镇',
        '学校',
        '教师',
        '实际授课总数',
        '计划达标授课总数（学期）',
        '授课达标占比（%）'
    ]
    dict_keys = (
        'town_name',
        'school_name',
        'teacher_name',
        'finished_time',
        'schedule_time',
        'finished_rate',
    )
    return _export(excel_header, dict_keys, records, total, 'teacher')


def by_lessonteacher_export(request, *args, **kwargs):
    ret = by_lessonteacher(request, True)['data']
    records, total = ret['records'], ret['total']
    excel_header = [
        '街道乡镇',
        '学校',
        '年级',
        '班级',
        '教师',
        '课程',
        '实际授课总数',
        '计划达标授课总数（学期）',
        '授课达标占比（%）'
    ]
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
    return _export(excel_header, dict_keys, records, total, 'lessonteacher')
