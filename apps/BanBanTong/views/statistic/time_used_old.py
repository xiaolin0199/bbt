# coding=utf-8
import datetime
import json
import os
import uuid
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db.models import Sum
from django.db.models import Q
from django.utils.dateparse import parse_date
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import format_record
from BanBanTong.utils import get_page_info
import xlwt


def _query(request):
    start_date = request.REQUEST.get('start_date')
    end_date = request.REQUEST.get('end_date')
    school_year = request.REQUEST.get('school_year')
    term_type = request.REQUEST.get('term_type')
    country_name = request.REQUEST.get('country_name')
    town_name = request.REQUEST.get('town_name')
    school_name = request.REQUEST.get('school_name')
    grade_name = request.REQUEST.get('grade_name')
    class_name = request.REQUEST.get('class_name')
    teacher_name = request.REQUEST.get('teacher_name', '').strip()
    lesson_name = request.REQUEST.get('lesson_name')

    o = models.TeacherLoginLog.objects.all()
    q = models.LessonTeacher.objects.filter(teacher__deleted=False)
    l = models.TeacherLoginTimeCache.objects.filter(
        teacherlogintime__teacherloginlog__lesson_teacher__isnull=False
    )
    title = ''
    if country_name:
        q = q.filter(class_uuid__grade__term__school__parent__parent__name=country_name)
        l = l.filter(town__parent__name=country_name)
        o = o.filter(country_name=country_name)
    if town_name:
        q = q.filter(class_uuid__grade__term__school__parent__name=town_name)
        l = l.filter(town__name=town_name)
        o = o.filter(town_name=town_name)
    if school_name:
        q = q.filter(class_uuid__grade__term__school__name=school_name)
        l = l.filter(school__name=school_name)
        o = o.filter(school_name=school_name)
    if grade_name:
        q = q.filter(class_uuid__grade__name=grade_name)
        l = l.filter(grade__name=grade_name)
        o = o.filter(grade_name=grade_name)
    if class_name:
        q = q.filter(class_uuid__name=class_name)
        l = l.filter(class_uuid__name=class_name)
        o = o.filter(class_name=class_name)
    if lesson_name:
        q = q.filter(lesson_name__name=lesson_name)
        l = l.filter(lesson_name=lesson_name)
        o = o.filter(lesson_name=lesson_name)
    if teacher_name:
        q = q.filter(teacher__name__icontains=teacher_name)
        l = l.filter(teacher__name__icontains=teacher_name)
        o = o.filter(teacher_name__icontains=teacher_name)
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
        l = l.filter(teacherlogintime__teacherloginlog__created_at__range=(s, e))
        o = o.filter(created_at__gte=s, created_at__lte=e)
        title = '%s-%s' % (start_date.replace('-', ''),
                           end_date.replace('-', ''))
    else:
        if school_year:
            # 按学年学期查询
            q = q.filter(class_uuid__grade__term__school_year=school_year)
            l = l.filter(class_uuid__grade__term__school_year=school_year)
            o = o.filter(term_school_year=school_year)
            title = school_year
        if term_type:
            q = q.filter(class_uuid__grade__term__term_type=term_type)
            l = l.filter(class_uuid__grade__term__term_type=term_type)
            o = o.filter(term_type=term_type)
            term = models.Term.objects.filter(school_year=school_year,
                                              term_type=term_type)
            if term.exists():
                term = term[0]
                title = '%s-%s' % (str(term.start_date).replace('-', ''),
                                   str(term.end_date).replace('-', ''))

    # 总授课时长
    #total_time_used = l.aggregate(x=Sum('teacherlogintime__login_time'))['x']
    # if start_date and end_date:
    #     teacher = q.values('teacher').distinct()
    #     l = l.filter(teacher__in=teacher)
    #     total_time_used = l.aggregate(x=Sum('teacherlogintime__login_time'))['x']
    # else:
    #    total_time_used = q.aggregate(x=Sum('login_time'))['x']
    #
    # if total_time_used is None:
    #     total_time_used = 0
    x = o.aggregate(x=Sum('teacherlogintime__login_time'))['x']
    y = o.aggregate(x=Sum('teacherlogintimetemp__login_time'))['x']
    x = x and x or 0
    y = y and y or 0
    total_time_used = x + y
    return q, total_time_used, title


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('time_used_statistic')
def _result(request, cache_key, fields):
    page_info = get_page_info(request)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    school_year = request.GET.get('school_year')
    term_type = request.GET.get('term_type')

    cache.set(cache_key, json.dumps(request.GET), None)
    q, total_time_used, title = _query(request)
    q = q.values(*fields)
    q = q.annotate(temp_lesson_count=Sum('finished_time'), temp_total_time_used=Sum('login_time'))

    paginator = Paginator(q, page_info['page_size'])
    records = list(paginator.page(page_info['page_num']).object_list)

    # fix qcbug:557
    if cache_key in ['time-used-by-teacher', 'time-used-by-lessonteacher']:
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

    records = format_record.new_time_used(records, cache_key, start_date, end_date,
                                          school_year, term_type)
    ret = create_success_dict(data={
        'page': page_info['page_num'],
        'page_count': paginator.num_pages,
        'page_size': page_info['page_size'],
        'record_count': paginator.count,
        'records': records,
        'total_time_used': total_time_used,
    })
    return ret


def by_lessonteacher(request):
    cache_key = 'time-used-by-lessonteacher'
    fields = (
        'class_uuid__grade__term__school__parent__name',
        'class_uuid__grade__term__school__name',
        'class_uuid__grade__name',
        'class_uuid__name',
        'lesson_name__name',
        'teacher__name',
        'teacher__birthday',
        'teacher__pk',
    )
    ret = _result(request, cache_key, fields)

    return ret


def by_teacher(request):
    cache_key = 'time-used-by-teacher'
    fields = (
        'class_uuid__grade__term__school__parent__name',
        'class_uuid__grade__term__school__name',
        'teacher__name',
        'teacher__birthday',
        'teacher__pk',
    )
    ret = _result(request, cache_key, fields)
    return ret


def _divmod(x, y):
    try:
        y = y and y or 1
        result = '%.2f' % (x / 60.0 / y)
        return float(result)
    except:
        return 0.00


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('time_used_statistic')
def _export(request, cache_key, fields, excel_header, dict_keys, export_type):
    start_date = request.REQUEST.get('start_date')
    end_date = request.REQUEST.get('end_date')
    school_year = request.REQUEST.get('school_year')
    term_type = request.REQUEST.get('term_type')

    q, total_time_used, title = _query(request)

    q = q.values(*fields)
    q = q.annotate(temp_lesson_count=Sum('finished_time'), temp_total_time_used=Sum('login_time'))

    # fix qcbug:557
    if cache_key in ['time-used-by-teacher', 'time-used-by-lessonteacher']:
        d = {}
        for i, v in enumerate(list(q)):
            if not d.has_key(v['teacher__name']):
                d[v['teacher__name']] = [i]
            else:
                d[v['teacher__name']].append(i)

        for k in d:
            if len(d[k]) > 1:
                lst = []
                for i in d[k]:
                    value = '%s(%s)' % (
                        q[i]['teacher__name'],
                        q[i]['teacher__birthday'].strftime('%m%d')
                    )
                    lst.append(value)
                if len(set(lst)) == 1:
                    continue
                for i in d[k]:
                    value = '%s(%s)' % (
                        q[i]['teacher__name'],
                        q[i]['teacher__birthday'].strftime('%m%d')
                    )
                    q[i]['teacher__name'] = value

    xls = xlwt.Workbook(encoding='utf8')
    if not title:
        title = u'班班通授课时长统计'

    sheet = xls.add_sheet(export_type)
    for i in range(len(excel_header)):
        sheet.write(0, i, excel_header[i])
    row = 1

    l = format_record.new_time_used(q, cache_key, start_date, end_date,
                                    school_year, term_type)
    for record in l:
        for i in range(len(dict_keys) - 1):
            sheet.write(row, i, record[dict_keys[i]])

        sheet.write(row, len(dict_keys) - 1, _divmod(record['total_time_used'], record['lesson_count']))
        sheet.write(row, len(dict_keys), _divmod(record[dict_keys[len(dict_keys) - 1]], 1))
        row += 1

    sheet.write(row, dict_keys.index('total_time_used'), '合计')
    sheet.write(row, dict_keys.index('total_time_used') + 1, u'%0.2f' % (total_time_used * 1.0 / 60.0))

    cached_id = str(uuid.uuid1())
    tmp_file = os.path.join(constants.CACHE_TMP_ROOT, cached_id)
    xls.save(tmp_file)
    d = {
        'town': u'乡镇街道',
        'school': u'学校',
        'grade': u'年级',
        'class': u'班级',
        'lessonteacher': u'班级课程教师',
        'teacher': u'教师'
    }
    filename = u'班班通授课时长统计_按%s导出.xls' % d[export_type]

    return create_success_dict(url=reverse('base:xls_download',
                                           kwargs={'cached_id': cached_id,
                                                   'name': filename}))


def by_teacher_export(request, *args, **kwargs):
    cache_key = 'time-used-by-teacher'
    fields = (
        'class_uuid__grade__term__school__parent__name',
        'class_uuid__grade__term__school__name',
        'teacher__name',
        'teacher__birthday',
        'teacher__pk',
    )
    excel_header = (
        '街道乡镇',
        '学校',
        '老师',
        '授课节次总数',
        '平均时长/节次(分钟)',
        '总授课时长(分钟)'
    )
    dict_keys = (
        'town_name',
        'school_name',
        'teacher_name',
        'lesson_count',
        'total_time_used'
    )
    ret = _export(request, cache_key, fields, excel_header, dict_keys, 'teacher')
    return ret


def by_lessonteacher_export(request, *args, **kwargs):
    cache_key = 'time-used-by-lessonteacher'
    fields = (
        'class_uuid__grade__term__school__parent__name',
        'class_uuid__grade__term__school__name',
        'class_uuid__grade__name',
        'class_uuid__name',
        'lesson_name__name',
        'teacher__name',
        'teacher__birthday',
        'teacher__pk',
    )
    excel_header = (
        '街道乡镇',
        '学校',
        '年级',
        '班级',
        '教师',
        '课程',
        '授课节次总数',
        '平均时长/节次',
        '总授课时长'
    )
    dict_keys = (
        'town_name',
        'school_name',
        'grade_name',
        'class_name',
        'teacher_name',
        'lesson_name',
        'lesson_count',
        'total_time_used'
    )
    ret = _export(request, cache_key, fields, excel_header, dict_keys, 'lessonteacher')
    return ret
