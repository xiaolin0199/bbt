# coding=utf-8
import datetime
import json
import os
import uuid
import csv
from django.http import HttpResponse
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.db.models import Q
from django.utils.dateparse import parse_date
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import format_record
from BanBanTong.utils import get_page_info
import xlwt


def _query(conditions, m):
    '''根据查询条件进行过滤。分为两种情况：
    1. 按自然日期查询，找出教师在该时段内是否有TeacherLoginLog
    2. 按学年学期查询
    算出登记教师总数。

    至于授课教师总数交给format_record去算。
    '''
    start_date = conditions.get('start_date')
    end_date = conditions.get('end_date')
    school_year = conditions.get('school_year')
    term_type = conditions.get('term_type')

    country_name = conditions.get('country_name')
    town_name = conditions.get('town_name')
    school_name = conditions.get('school_name')
    grade_name = conditions.get('grade_name')
    lesson_name = conditions.get('lesson_name')

    q = m.objects.all()
    #lt = models.LessonTeacher.objects.filter(teacher__deleted=False)
    lt = models.LessonTeacher.objects.all()
    #a = models.ActiveTeachers.objects.filter(teacher__deleted=False)
    a = models.ActiveTeachers.objects.all()
    title = ''
    if country_name:
        q = q.filter(country_name=country_name)
        lt = lt.filter(class_uuid__grade__term__school__parent__parent__name=country_name)
        a = a.filter(country_name=country_name)
    if town_name:
        q = q.filter(town_name=town_name)
        lt = lt.filter(class_uuid__grade__term__school__parent__name=town_name)
        a = a.filter(town_name=town_name)
    if school_name:
        q = q.filter(school_name=school_name)
        lt = lt.filter(class_uuid__grade__term__school__name=school_name)
        a = a.filter(school_name=school_name)
    if grade_name:
        q = q.filter(grade_name=grade_name)
        lt = lt.filter(class_uuid__grade__name=grade_name)
        a = a.filter(grade_name=grade_name)
    if lesson_name:
        q = q.filter(lesson_name=lesson_name)
        lt = lt.filter(lesson_name__name=lesson_name)
        a = a.filter(lesson_name=lesson_name)
    if start_date and end_date:
        s = parse_date(start_date)
        e = parse_date(end_date)
        s = datetime.datetime.combine(s, datetime.time.min)
        e = datetime.datetime.combine(e, datetime.time.max)
        cond = Q(term__start_date__lte=s, term__end_date__gte=s)
        cond |= Q(term__start_date__gte=s, term__end_date__lte=e)
        cond |= Q(term__start_date__lte=e, term__end_date__gte=e)
        q = q.filter(cond)

        # 按照自然时间查询的时候,查询时间段内的登录授课教师
        cond = Q(class_uuid__grade__term__start_date__lte=s,
                 class_uuid__grade__term__end_date__gte=s)
        cond |= Q(class_uuid__grade__term__start_date__gte=s,
                  class_uuid__grade__term__end_date__lte=e)
        cond |= Q(class_uuid__grade__term__start_date__lte=e,
                  class_uuid__grade__term__end_date__gte=e)
        lt = lt.filter(cond)

        a = a.filter(active_date__range=(s, e))
        title = '%s-%s' % (start_date.replace('-', ''),
                           end_date.replace('-', ''))
    else:
        # 按学年学期查询
        if not school_year and not term_type:
            # 自然时间和学年学期都未提供时候,默认查询当前学年学期或最近的一个
            t = models.NewTerm.get_nearest_term()
            if t:
                school_year = t.school_year
                term_type = t.term_type

        if school_year:
            lt = lt.filter(class_uuid__grade__term__school_year=school_year)
            q = q.filter(term__school_year=school_year)
            a = a.filter(school_year=school_year)
            title = school_year
        if term_type:
            lt = lt.filter(class_uuid__grade__term__term_type=term_type)
            q = q.filter(term__term_type=term_type)
            a = a.filter(term_type=term_type)
            term = models.Term.objects.filter(school_year=school_year,
                                              term_type=term_type)
            if term.exists():
                term = term[0]
                title = '%s-%s' % (str(term.start_date).replace('-', ''),
                                   str(term.end_date).replace('-', ''))

    total_teachers = lt.values('teacher').distinct().count()  # 登记教师总数
    active_teachers = a.values('teacher').distinct().count()  # 授课教师总数
    return q, total_teachers, active_teachers, title


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def _new_result(request, cache_key, m, fields, order_by_fields):
    page_info = get_page_info(request)
    cache.set(cache_key, json.dumps(request.GET), None)
    q, total_teachers, active_teachers, title = _query(request.GET, m)
    q = q.order_by(*order_by_fields)
    q = q.values(*fields).distinct()

    if q:
        if cache_key == u'teacher-active-by-country':
            temp_country_dict = {}
            temp_q_list = []
            for one in q:
                if temp_country_dict.has_key(one['country_name']):
                    temp_country_dict[one['country_name']] += one['total']
                else:
                    temp_country_dict[one['country_name']] = one['total']
            for country_name, total in temp_country_dict.iteritems():
                temp_q_list.append({'country_name': country_name, 'total': total})
            q = temp_q_list

        elif cache_key == u'teacher-active-by-town':
            temp_town_dict = {}
            temp_q_list = []
            for one in q:
                if temp_town_dict.has_key(one['town_name']):
                    temp_town_dict[one['town_name']] = {'total': one['total'] + temp_town_dict[one['town_name']]['total']}
                else:
                    temp_town_dict[one['town_name']] = {'total': one['total']}
            for town_name, value_dict in temp_town_dict.iteritems():
                temp_q_list.append({'town_name': town_name, 'total': value_dict['total']})
            q = temp_q_list

        elif cache_key == u'teacher-active-by-school':
            temp_school_dict = {}
            temp_q_list = []
            for one in q:
                key = (one['town_name'], one['school_name'])
                if temp_school_dict.has_key(key):
                    temp_school_dict[key]['total'] += one['total']
                else:
                    temp_school_dict[key] = {'total': one['total']}
            for (town_name, school_name), value_dict in temp_school_dict.iteritems():
                temp_q_list.append({
                    'town_name': town_name,
                    'school_name': school_name,
                    'total': value_dict['total']
                })
            q = temp_q_list

        elif cache_key == u'teacher-active-by-grade':
            temp_school_dict = {}
            temp_q_list = []
            for one in q:
                key = (one['town_name'], one['school_name'], one['grade_name'])
                if temp_school_dict.has_key(key):
                    temp_school_dict[key]['total'] += one['total']
                else:
                    temp_school_dict[key] = {'total': one['total']}
            for (town_name, school_name, grade_name), value_dict in temp_school_dict.iteritems():
                temp_q_list.append({
                    'town_name': town_name,
                    'school_name': school_name,
                    'grade_name': grade_name,
                    'total': value_dict['total']
                })
            q = temp_q_list

        elif cache_key == u'teacher-active-by-lesson':
            temp_school_dict = {}
            temp_q_list = []
            for one in q:
                key = (one['town_name'], one['school_name'], one['lesson_name'])
                if temp_school_dict.has_key(key):
                    temp_school_dict[key]['total'] += one['total']
                else:
                    temp_school_dict[key] = {'total': one['total']}
            for (town_name, school_name, lesson_name), value_dict in temp_school_dict.iteritems():
                temp_q_list.append({
                    'town_name': town_name,
                    'school_name': school_name,
                    'lesson_name': lesson_name,
                    'total': value_dict['total']
                })
            q = temp_q_list

        elif cache_key == u'teacher-active-by-lessongrade':
            temp_school_dict = {}
            temp_q_list = []
            for one in q:
                key = (one['town_name'], one['school_name'], one['lesson_name'], one['grade_name'])
                if temp_school_dict.has_key(key):
                    temp_school_dict[key]['total'] += one['total']
                else:
                    temp_school_dict[key] = {'total': one['total']}
            for (town_name, school_name, lesson_name, grade_name), value_dict in temp_school_dict.iteritems():
                temp_q_list.append({
                    'town_name': town_name,
                    'school_name': school_name,
                    'lesson_name': lesson_name,
                    'grade_name': grade_name,
                    'total': value_dict['total']
                })
            q = temp_q_list

    paginator = Paginator(q, page_info['page_size'])
    records = list(paginator.page(page_info['page_num']).object_list)
    records = format_record.new_teacher_active(records, request.GET)
    ret = create_success_dict(data={
        'page': page_info['page_num'],
        'page_count': paginator.num_pages,
        'page_size': page_info['page_size'],
        'record_count': paginator.count,
        'records': records,
        'total': {'total_teachers': total_teachers,
                  'active_teachers': active_teachers},
    })
    return ret


def by_country(request):
    cache_key = 'teacher-active-by-country'
    m = models.TotalTeachersCountry
    fields = ('country_name', 'total')
    order_by_fields = ('country_name', )
    ret = _new_result(request, cache_key, m, fields, order_by_fields)
    return ret


def by_town(request):
    cache_key = 'teacher-active-by-town'
    m = models.TotalTeachersTown
    fields = ('town_name', 'total')
    order_by_fields = ('town_name',)
    ret = _new_result(request, cache_key, m, fields, order_by_fields)
    return ret


def by_school(request):
    cache_key = 'teacher-active-by-school'
    m = models.TotalTeachersSchool
    fields = ('town_name', 'school_name', 'total')
    order_by_fields = ('town_name', 'school_name')
    ret = _new_result(request, cache_key, m, fields, order_by_fields)
    return ret


def by_grade(request):
    cache_key = 'teacher-active-by-grade'
    m = models.TotalTeachersGrade
    fields = ('town_name', 'school_name', 'grade_name', 'total',
              'term__school_year', 'term__term_type', 'term')
    order_by_fields = ('town_name', 'school_name', 'grade_name')
    ret = _new_result(request, cache_key, m, fields, order_by_fields)
    return ret


def by_lesson(request):
    cache_key = 'teacher-active-by-lesson'
    m = models.TotalTeachersLesson
    fields = ('town_name', 'school_name', 'lesson_name',
              'term__school_year', 'term__term_type', 'total')
    order_by_fields = ('town_name', 'school_name')
    ret = _new_result(request, cache_key, m, fields, order_by_fields)
    return ret


def by_lessongrade(request):
    cache_key = 'teacher-active-by-lessongrade'
    m = models.TotalTeachersLessonGrade
    fields = ('town_name', 'school_name', 'lesson_name', 'grade_name', 'total')
    order_by_fields = ('town_name', 'school_name', 'grade_name')
    ret = _new_result(request, cache_key, m, fields, order_by_fields)
    return ret


def teacher_active_query(conditions):
    '''根据查询条件进行过滤。分为两种情况：
    1. 按自然日期查询，找出教师在该时段内是否有TeacherLoginLog
    2. 按学年学期查询，转化为自然日期
    算出登记教师总数。至于授课教师总数交给format_record去算。
    '''
    start_date = conditions.get('start_date')
    end_date = conditions.get('end_date')
    school_year = conditions.get('school_year')
    term_type = conditions.get('term_type')
    country_name = conditions.get('country_name')
    town_name = conditions.get('town_name')
    school_name = conditions.get('school_name')
    grade_name = conditions.get('grade_name')
    class_name = conditions.get('class_name')
    lesson_name = conditions.get('lesson_name')
    teacher_name = conditions.get('teacher_name')
    if not school_year and not term_type:
        t = models.Term.get_current_term_list()
        if t:
            school_year = t[0].school_year
            term_type = t[0].term_type
    q = models.LessonTeacher.objects.filter(teacher__deleted=False)
    teachers = q.values_list('teacher', flat=True)
    l = models.TeacherLoginLog.objects.filter(teacher__in=teachers)
    title = ''
    if country_name:
        q = q.filter(class_uuid__grade__term__school__parent__parent__name=country_name)
        l = l.filter(country_name=country_name)
    if town_name:
        q = q.filter(class_uuid__grade__term__school__parent__name=town_name)
        l = l.filter(town_name=town_name)
    if school_name:
        q = q.filter(class_uuid__grade__term__school__name=school_name)
        l = l.filter(school_name=school_name)
    if grade_name:
        q = q.filter(class_uuid__grade__name=grade_name)
        l = l.filter(grade_name=grade_name)
    if class_name:
        q = q.filter(class_uuid__name=class_name)
        l = l.filter(class_name=class_name)
    if lesson_name:
        q = q.filter(lesson_name__name=lesson_name)
        l = l.filter(lesson_name=lesson_name)
    if teacher_name:
        q = q.filter(teacher__name=teacher_name)
        l = l.filter(teacher_name=teacher_name)
    if school_year:
        l = l.filter(term_school_year=school_year)
    if term_type:
        l = l.filter(term_type=term_type)
    if start_date and end_date:
        s = parse_date(start_date)
        e = parse_date(end_date)
        s = datetime.datetime.combine(s, datetime.time.min)
        e = datetime.datetime.combine(e, datetime.time.max)
        l = l.filter(created_at__range=(s, e))
    total_teachers = q.values('teacher').distinct()
    active_teachers = l.values('teacher').distinct().count()
    return q, total_teachers, active_teachers, title


def _result(request, cache_key, fields):
    page_info = get_page_info(request)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    school_year = request.GET.get('school_year')
    term_type = request.GET.get('term_type')

    cache.set(cache_key, json.dumps(request.GET), None)
    q, total_teachers, active_teachers, title = teacher_active_query(request.GET)
    q = q.values(*fields)
    q = q.annotate(total_teachers=Count('teacher', distinct=True))
    paginator = Paginator(q, page_info['page_size'])
    records = list(paginator.page(page_info['page_num']).object_list)
    records = format_record.teacher_active(records, total_teachers,
                                           start_date, end_date,
                                           school_year, term_type)
    ret = create_success_dict(data={
        'page': page_info['page_num'],
        'page_count': paginator.num_pages,
        'page_size': page_info['page_size'],
        'record_count': paginator.count,
        'records': records,
        'total': {'total_teachers': total_teachers.count(),
                  'active_teachers': active_teachers},
    })
    return ret


def _export(cache_key, query_fields, excel_header, dict_keys):
    c = cache.get(cache_key)
    if not c:
        return create_failure_dict(msg='查询超时无法导出，请重新查询！')
    cond = json.loads(c)
    q, total_teachers, active_teachers, title = teacher_active_query(cond)
    q = q.values(*query_fields)
    q = q.annotate(total_teachers=Count('teacher', distinct=True))
    start_date = cond.get('start_date')
    end_date = cond.get('end_date')
    school_year = cond.get('school_year')
    term_type = cond.get('term_type')
    xls = xlwt.Workbook(encoding='utf8')
    if not title:
        title = u'教师授课人数比例统计'
    sheet = xls.add_sheet(title)
    for i in range(len(excel_header)):
        sheet.write(0, i, excel_header[i])
    row = 1
    l = format_record.teacher_active(q, total_teachers,
                                     start_date, end_date,
                                     school_year, term_type)
    for record in l:
        for i in range(len(dict_keys)):
            sheet.write(row, i, record[dict_keys[i]])
        try:
            percent = record['active_teachers'] * 100.0 / record['total_teachers']
        except:
            percent = 0.0
        percent = '%0.2f%%' % percent
        sheet.write(row, len(dict_keys), percent)
        row += 1
    # sheet.write(row, len(dict_keys) - 3, '合计')
    # sheet.write(row, len(dict_keys) - 2, active_teachers)
    # sheet.write(row, len(dict_keys) - 1, total_teachers.count())

    # 2014-12-25
    sheet.write(row, dict_keys.index('active_teachers') - 1, '合计')
    sheet.write(row, dict_keys.index('active_teachers'), active_teachers)
    sheet.write(row, dict_keys.index('total_teachers'), total_teachers.count())

    try:
        total_percent = active_teachers * 100.0 / total_teachers.count()
    except:
        total_percent = 0
    total_percent = '%0.2f%%' % total_percent
    sheet.write(row, len(dict_keys), total_percent)
    cached_id = str(uuid.uuid1())
    tmp_file = os.path.join(constants.CACHE_TMP_ROOT, cached_id)
    xls.save(tmp_file)
    filename = u'教师授课人数比例统计_%s.xls' % title
    return create_success_dict(url=reverse('base:xls_download',
                                           kwargs={'cached_id': cached_id,
                                                   'name': filename}))


def _new_export(m, cache_key, query_fields, excel_header, dict_keys):
    c = cache.get(cache_key)
    if not c:
        return create_failure_dict(msg='查询超时无法导出，请重新查询！')
    cond = json.loads(c)
    #q, total_teachers, active_teachers, title = teacher_active_query(cond)
    q, total_teachers, active_teachers, title = _query(cond, m)
    q = q.values(*query_fields)
    # TODO
    if q:
        if cache_key == u'teacher-active-by-town':
            temp_town_dict = {}
            temp_q_list = []
            for one in q:
                if temp_town_dict.has_key(one['town_name']):
                    #temp_town_dict[one['town_name']] = {'total':one['total'] + temp_town_dict[one['town_name']]['total'], 'country_name':one['country_name']}
                    temp_town_dict[one['town_name']] = {'total': one['total'] + temp_town_dict[one['town_name']]['total']}
                else:
                    #temp_town_dict[one['town_name']] = {'total':one['total'], 'country_name':one['country_name']}
                    temp_town_dict[one['town_name']] = {'total': one['total']}
            for town_name, value_dict in temp_town_dict.iteritems():
                # temp_q_list.append({'country_name':value_dict['country_name'],'town_name':town_name,'total':value_dict['total']})
                temp_q_list.append({'town_name': town_name, 'total': value_dict['total']})
            q = temp_q_list

        elif cache_key == u'teacher-active-by-country':
            temp_country_dict = {}
            temp_q_list = []
            for one in q:
                if temp_country_dict.has_key(one['country_name']):
                    temp_country_dict[one['country_name']] += one['total']
                else:
                    temp_country_dict[one['country_name']] = one['total']
            for country_name, total in temp_country_dict.iteritems():
                temp_q_list.append({'country_name': country_name, 'total': total})
            q = temp_q_list

    #q = q.annotate(total_teachers=Count('teacher', distinct=True))

    if not title:
        title = u'教师授课人数比例统计'

    cached_id = str(uuid.uuid1())
    tmp_file = os.path.join(constants.CACHE_TMP_ROOT, cached_id)

    l = format_record.new_teacher_active(q, cond)

    try:
        export_type = constants.BANBANTONG_DEFAULT_EXPORT_TYPE.upper()
        if export_type not in ['XLS', 'CSV']:
            export_type = 'XLS'
    except:
        export_type = 'XLS'
    if export_type == 'XLS':
        xls = xlwt.Workbook(encoding='utf8')
        sheet = xls.add_sheet(title)
        for i in range(len(excel_header)):
            sheet.write(0, i, excel_header[i])
        row = 1
        for record in l:
            for i in range(len(dict_keys)):
                sheet.write(row, i, record[dict_keys[i]])
            try:
                percent = record['active_teachers'] * 100.0 / record['total_teachers']
            except:
                percent = 0.0
            percent = '%0.2f%%' % percent
            sheet.write(row, len(dict_keys), percent)
            row += 1
        # sheet.write(row, len(dict_keys) - 3, '合计')
        # sheet.write(row, len(dict_keys) - 2, active_teachers)
        # sheet.write(row, len(dict_keys) - 1, total_teachers)

        # 2014-12-25
        sheet.write(row, dict_keys.index('active_teachers') - 1, '合计')
        sheet.write(row, dict_keys.index('active_teachers'), active_teachers)
        sheet.write(row, dict_keys.index('total_teachers'), total_teachers)

        try:
            total_percent = active_teachers * 100.0 / total_teachers
        except:
            total_percent = 0
        total_percent = '%0.2f%%' % total_percent
        sheet.write(row, len(dict_keys), total_percent)
        xls.save(tmp_file)
        filename = u'教师授课人数比例统计_%s.xls' % title

    elif export_type == 'CSV':
        filename = u'教师授课人数比例统计_%s.csv' % title
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % (filename.encode('utf-8', 'ignore'))
        writer = csv.writer(response)
        # 写CSV头
        writer.writerow(excel_header)
        for record in l:
            row_data = []
            for i in range(len(dict_keys)):
                row_data.append(unicode(record[dict_keys[i]]).encode('utf-8', 'ignore'))

            try:
                percent = record['active_teachers'] * 100.0 / record['total_teachers']
            except:
                percent = 0.0
            percent = '%0.2f%%' % percent
            row_data.append(percent)
            writer.writerow(row_data)
        try:
            total_percent = active_teachers * 100.0 / total_teachers
        except:
            total_percent = 0
        total_percent = '%0.2f%%' % total_percent
        # 最后一行
        last_row = [''] * len(excel_header)
        last_row[-1] = total_percent
        last_row[-2] = total_teachers
        last_row[-3] = active_teachers
        last_row[-4] = u'合计'.encode('utf-8', 'ignore')
        writer.writerow(last_row)

        with open(tmp_file, 'wb') as f:
            f.write(response.content)

    return create_success_dict(url=reverse('base:xls_download',
                                           kwargs={'cached_id': cached_id,
                                                   'name': filename}))


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def by_country_export(request, *args, **kwargs):
    cache_key = 'teacher-active-by-country'
    m = models.TotalTeachersCountry
    fields = ('country_name', 'total')
    #fields = ('class_uuid__grade__term__school__parent__parent__name', )
    excel_header = ['区县市', '授课教师总数', '登记教师总数', '授课占比（%）']
    dict_keys = ('country_name', 'active_teachers', 'total_teachers')
    #ret = _export(cache_key, fields, excel_header, dict_keys)
    ret = _new_export(m, cache_key, fields, excel_header, dict_keys)
    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def by_town_export(request, *args, **kwargs):
    cache_key = 'teacher-active-by-town'
    m = models.TotalTeachersTown
    fields = (
        #'country_name',
        'town_name', 'total')
    # fields = ('class_uuid__grade__term__school__parent__parent__name',
    #          'class_uuid__grade__term__school__parent__name', )
    excel_header = [
        #'区县市',
        '街道乡镇',
        '授课教师总数', '登记教师总数', '授课占比（%）']
    dict_keys = (
        #'country_name',
        'town_name',
        'active_teachers', 'total_teachers')
    #ret = _export(cache_key, fields, excel_header, dict_keys)
    ret = _new_export(m, cache_key, fields, excel_header, dict_keys)
    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def by_school_export(request, *args, **kwargs):
    cache_key = 'teacher-active-by-school'
    m = models.TotalTeachersSchool
    fields = (
        #'country_name',
        'town_name', 'school_name', 'total')
    # fields = ('class_uuid__grade__term__school__parent__parent__name',
    #          'class_uuid__grade__term__school__parent__name',
    #          'class_uuid__grade__term__school__name')
    excel_header = [
        #'区县市',
        '街道乡镇', '学校',
        '授课教师总数', '登记教师总数', '授课占比（%）']
    dict_keys = (
        #'country_name',
        'town_name', 'school_name',
        'active_teachers', 'total_teachers')
    #ret = _export(cache_key, fields, excel_header, dict_keys)
    ret = _new_export(m, cache_key, fields, excel_header, dict_keys)
    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def by_grade_export(request, *args, **kwargs):
    cache_key = 'teacher-active-by-grade'
    m = models.TotalTeachersGrade
    fields = ('town_name', 'school_name', 'grade_name', 'total',
              'term__school_year', 'term__term_type', 'term')
    # fields = ('class_uuid__grade__term__school__parent__name',
    #          'class_uuid__grade__term__school__name',
    #          'class_uuid__grade__name')
    excel_header = ['街道乡镇', '学校', '年级',
                    '授课教师总数', '登记教师总数', '授课占比（%）']
    dict_keys = ('town_name', 'school_name', 'grade_name',
                 'active_teachers', 'total_teachers')
    #ret = _export(cache_key, fields, excel_header, dict_keys)
    ret = _new_export(m, cache_key, fields, excel_header, dict_keys)
    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def by_lesson_export(request, *args, **kwargs):
    cache_key = 'teacher-active-by-lesson'
    m = models.TotalTeachersLesson
    fields = (
        #'country_name',
        'town_name', 'school_name',
        'lesson_name', 'total')
    # fields = ('class_uuid__grade__term__school__parent__parent__name',
    #          'class_uuid__grade__term__school__parent__name',
    #          'class_uuid__grade__term__school__name',
    #          'lesson_name__name')
    excel_header = [
        #'区县市',
        '街道乡镇', '学校', '课程',
        '授课教师总数', '登记教师总数', '授课占比（%）']
    dict_keys = (
        #'country_name',
        'town_name', 'school_name', 'lesson_name',
        'active_teachers', 'total_teachers')
    #ret = _export(cache_key, fields, excel_header, dict_keys)
    ret = _new_export(m, cache_key, fields, excel_header, dict_keys)
    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def by_lessongrade_export(request, *args, **kwargs):
    cache_key = 'teacher-active-by-lessongrade'
    m = models.TotalTeachersLessonGrade
    fields = ('town_name', 'school_name', 'lesson_name',
              'grade_name', 'total')
    # fields = ('class_uuid__grade__term__school__parent__name',
    #          'class_uuid__grade__term__school__name',
    #          'class_uuid__grade__name',
    #          'lesson_name__name')
    excel_header = ['街道乡镇', '学校', '年级', '课程',
                    '授课教师总数', '登记教师总数', '授课占比（%）']
    dict_keys = ('town_name', 'school_name', 'grade_name', 'lesson_name',
                 'active_teachers', 'total_teachers')
    #ret = _export(cache_key, fields, excel_header, dict_keys)
    ret = _new_export(m, cache_key, fields, excel_header, dict_keys)
    return ret
