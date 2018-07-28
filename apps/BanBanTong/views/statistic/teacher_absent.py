# coding=utf-8
import datetime
import json
import os
import uuid
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


def teacher_absent_query(conditions):
    '''根据查询条件进行过滤。分为两种情况：
    1. 按自然日期查询，找出教师在该时段内是否有TeacherLoginLog
    2. 按学年学期查询，转化为自然日期
    算出登记教师总数。至于未登录教师总数交给format_record去算。
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

    if not end_date:
        q = models.LessonTeacher.objects.filter(teacher__deleted=False)
    else:
        q = models.LessonTeacher.objects.filter(teacher__deleted=False, teacher__register_at__lte=end_date)
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
    if lesson_name:
        q = q.filter(lesson_name__name=lesson_name)
        l = l.filter(lesson_name=lesson_name)
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
    absent_teachers = total_teachers.count() - active_teachers
    return q, total_teachers, absent_teachers, title


def _query(conditions, m):
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
    lesson_name = conditions.get('lesson_name')

    q = m.objects.all()
    lt = models.LessonTeacher.objects.filter(teacher__deleted=False)
    a = models.ActiveTeachers.objects.filter(teacher__deleted=False)
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
    if school_year:
        q = q.filter(term__school_year=school_year)
        a = a.filter(school_year=school_year)
        title = school_year
    if term_type:
        q = q.filter(term__term_type=term_type)
        a = a.filter(term_type=term_type)
        term = models.Term.objects.filter(school_year=school_year,
                                          term_type=term_type)
        if term.exists():
            term = term[0]
            title = '%s-%s' % (str(term.start_date).replace('-', ''),
                               str(term.end_date).replace('-', ''))
    if start_date and end_date:
        s = parse_date(start_date)
        e = parse_date(end_date)
        s = datetime.datetime.combine(s, datetime.time.min)
        e = datetime.datetime.combine(e, datetime.time.max)
        cond = Q(term__start_date__lte=s, term__end_date__gte=s)
        cond |= Q(term__start_date__gte=s, term__end_date__lte=e)
        cond |= Q(term__start_date__lte=e, term__end_date__gte=e)
        q = q.filter(cond)
        a = a.filter(active_date__range=(s, e))
        title = '%s-%s' % (start_date.replace('-', ''),
                           end_date.replace('-', ''))
    total_teachers = lt.values('teacher').distinct().count()
    absent_teachers = total_teachers - a.values('teacher').distinct().count()
    return q, total_teachers, absent_teachers, title


def _result(request, cache_key, fields):
    page_info = get_page_info(request)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    school_year = request.GET.get('school_year')
    term_type = request.GET.get('term_type')

    cache.set(cache_key, json.dumps(request.GET), None)
    q, total_teachers, absent_teachers, title = teacher_absent_query(request.GET)
    q = q.values(*fields)
    q = q.annotate(total_teachers=Count('teacher', distinct=True))
    paginator = Paginator(q, page_info['page_size'])
    records = list(paginator.page(page_info['page_num']).object_list)
    records = format_record.teacher_absent(records, total_teachers,
                                           start_date, end_date,
                                           school_year, term_type)
    ret = create_success_dict(data={
        'page': page_info['page_num'],
        'page_count': paginator.num_pages,
        'page_size': page_info['page_size'],
        'record_count': paginator.count,
        'records': records,
        'total': {'total_teachers': total_teachers.count(),
                  'absent_teachers': absent_teachers},
    })
    return ret


def _new_result(request, cache_key, m, fields):
    page_info = get_page_info(request)

    cache.set(cache_key, json.dumps(request.GET), None)
    #q, total_teachers, active_teachers, title = _query(request.GET, m)
    q, total_teachers, absent_teachers, title = _query(request.GET, m)
    q = q.values(*fields)
    # TODO
    if q:
        if cache_key == u'teacher-absent-by-town':
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

        elif cache_key == u'teacher-absent-by-country':
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

    paginator = Paginator(q, page_info['page_size'])
    records = list(paginator.page(page_info['page_num']).object_list)
    #records = format_record.new_teacher_active(records, request)
    records = format_record.new_teacher_absent(records, request.GET)
    ret = create_success_dict(data={
        'page': page_info['page_num'],
        'page_count': paginator.num_pages,
        'page_size': page_info['page_size'],
        'record_count': paginator.count,
        'records': records,
        'total': {'total_teachers': total_teachers,
                  #'active_teachers': active_teachers
                  'absent_teachers': absent_teachers
                  },
    })
    return ret


def _export(cache_key, query_fields, excel_header, dict_keys):
    c = cache.get(cache_key)
    if not c:
        return create_failure_dict(msg='查询超时无法导出，请重新查询！')
    cond = json.loads(c)
    q, total_teachers, absent_teachers, title = teacher_absent_query(cond)
    q = q.values(*query_fields)
    q = q.annotate(total_teachers=Count('teacher', distinct=True))
    start_date = cond.get('start_date')
    end_date = cond.get('end_date')
    school_year = cond.get('school_year')
    term_type = cond.get('term_type')
    xls = xlwt.Workbook(encoding='utf8')
    if not title:
        title = u'教师未登录班班通统计'
    sheet = xls.add_sheet(title)
    for i in range(len(excel_header)):
        sheet.write(0, i, excel_header[i])
    row = 1
    l = format_record.teacher_absent(q, total_teachers,
                                     start_date, end_date,
                                     school_year, term_type)
    for record in l:
        for i in range(len(dict_keys)):
            sheet.write(row, i, record[dict_keys[i]])
        try:
            percent = record['absent_teachers'] * 100.0 / record['total_teachers']
        except:
            percent = 0.0
        percent = '%0.2f%%' % percent
        sheet.write(row, len(dict_keys), percent)
        row += 1
    # sheet.write(row, len(dict_keys) - 3, '合计')
    # sheet.write(row, len(dict_keys) - 2, absent_teachers)
    # sheet.write(row, len(dict_keys) - 1, total_teachers.count())

    # 2014-12-25
    sheet.write(row, dict_keys.index('absent_teachers') - 1, '合计')
    sheet.write(row, dict_keys.index('absent_teachers'), absent_teachers)
    sheet.write(row, dict_keys.index('total_teachers'), total_teachers.count())
    try:
        total_percent = absent_teachers * 100.0 / total_teachers.count()
    except:
        total_percent = 0
    total_percent = '%0.2f%%' % total_percent
    sheet.write(row, len(dict_keys), total_percent)
    cached_id = str(uuid.uuid1())
    tmp_file = os.path.join(constants.CACHE_TMP_ROOT, cached_id)
    xls.save(tmp_file)
    filename = u'教师未登录班班通统计_%s.xls' % title
    return create_success_dict(url=reverse('base:xls_download',
                                           kwargs={'cached_id': cached_id,
                                                   'name': filename}))


def _new_export(m, cache_key, query_fields, excel_header, dict_keys):
    c = cache.get(cache_key)
    if not c:
        return create_failure_dict(msg='查询超时无法导出，请重新查询！')
    cond = json.loads(c)
    #q, total_teachers, absent_teachers, title = teacher_absent_query(cond)
    q, total_teachers, absent_teachers, title = _query(cond, m)
    q = q.values(*query_fields)
    # TODO
    if q:
        if cache_key == u'teacher-absent-by-town':
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

        elif cache_key == u'teacher-absent-by-country':
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
    xls = xlwt.Workbook(encoding='utf8')
    if not title:
        title = u'教师未登录班班通统计'
    sheet = xls.add_sheet(title)
    for i in range(len(excel_header)):
        sheet.write(0, i, excel_header[i])
    row = 1
    # l = format_record.teacher_absent(q, total_teachers,
    #                                 start_date, end_date,
    #                                 school_year, term_type)
    l = format_record.new_teacher_absent(q, cond)
    for record in l:
        for i in range(len(dict_keys)):
            sheet.write(row, i, record[dict_keys[i]])
        try:
            percent = record['absent_teachers'] * 100.0 / record['total_teachers']
        except:
            percent = 0.0
        percent = '%0.2f%%' % percent
        sheet.write(row, len(dict_keys), percent)
        row += 1
    # sheet.write(row, len(dict_keys) - 3, '合计')
    # sheet.write(row, len(dict_keys) - 2, absent_teachers)
    # #sheet.write(row, len(dict_keys) - 1, total_teachers.count())
    # sheet.write(row, len(dict_keys) - 1, total_teachers)

    # 2014-12-25
    sheet.write(row, dict_keys.index('absent_teachers') - 1, '合计')
    sheet.write(row, dict_keys.index('absent_teachers'), absent_teachers)
    sheet.write(row, dict_keys.index('total_teachers'), total_teachers)

    try:
        #total_percent = absent_teachers * 100.0 / total_teachers.count()
        total_percent = absent_teachers * 100.0 / total_teachers
    except:
        total_percent = 0
    total_percent = '%0.2f%%' % total_percent
    sheet.write(row, len(dict_keys), total_percent)
    cached_id = str(uuid.uuid1())
    tmp_file = os.path.join(constants.CACHE_TMP_ROOT, cached_id)
    xls.save(tmp_file)
    filename = u'教师未登录班班通统计_%s.xls' % title
    return create_success_dict(url=reverse('base:xls_download',
                                           kwargs={'cached_id': cached_id,
                                                   'name': filename}))


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def by_country(request):
    cache_key = 'teacher-absent-by-country'
    m = models.TotalTeachersCountry
    fields = ('country_name', 'total')
    ret = _new_result(request, cache_key, m, fields)
    return ret
    #fields = ('class_uuid__grade__term__school__parent__parent__name', )
    #ret = _result(request, cache_key, fields)
    # return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def by_country_export(request, *args, **kwargs):
    cache_key = 'teacher-absent-by-country'
    m = models.TotalTeachersCountry
    #fields = ('class_uuid__grade__term__school__parent__parent__name', )
    fields = ('country_name', 'total')
    excel_header = ['区县市',
                    '未登录教师总数', '登记教师总数', '未授课占比（%）']
    dict_keys = ('country_name',
                 'absent_teachers', 'total_teachers')
    ret = _new_export(m, cache_key, fields, excel_header, dict_keys)
    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def by_grade(request):
    cache_key = 'teacher-absent-by-grade'
    m = models.TotalTeachersGrade
    fields = ('town_name', 'school_name', 'grade_name', 'total',
              'term__school_year', 'term__term_type', 'term')
    ret = _new_result(request, cache_key, m, fields)
    return ret
    # fields = ('class_uuid__grade__term__school__parent__name',
    #          'class_uuid__grade__term__school__name',
    #          'class_uuid__grade__name')
    #ret = _result(request, cache_key, fields)
    # return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def by_grade_export(request, *args, **kwargs):
    cache_key = 'teacher-absent-by-grade'
    m = models.TotalTeachersGrade
    fields = ('town_name', 'school_name', 'grade_name', 'total',
              'term__school_year', 'term__term_type', 'term')
    # fields = ('class_uuid__grade__term__school__parent__name',
    #          'class_uuid__grade__term__school__name',
    #          'class_uuid__grade__name')
    excel_header = ['街道乡镇', '学校', '年级',
                    '未登录教师总数', '登记教师总数', '未授课占比（%）']
    dict_keys = ('town_name', 'school_name', 'grade_name',
                 'absent_teachers', 'total_teachers')
    ret = _new_export(m, cache_key, fields, excel_header, dict_keys)
    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def by_lesson(request):
    cache_key = 'teacher-absent-by-lesson'
    m = models.TotalTeachersLesson
    fields = (
        #'country_name',
        'town_name', 'school_name',
        'lesson_name', 'total')
    ret = _new_result(request, cache_key, m, fields)
    return ret
    # fields = ('class_uuid__grade__term__school__parent__parent__name',
    #          'class_uuid__grade__term__school__parent__name',
    #          'class_uuid__grade__term__school__name',
    #          'lesson_name__name')
    #ret = _result(request, cache_key, fields)
    # return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def by_lesson_export(request, *args, **kwargs):
    cache_key = 'teacher-absent-by-lesson'
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
        '未登录教师总数', '登记教师总数', '未授课占比（%）']
    dict_keys = (
        #'country_name',
        'town_name', 'school_name', 'lesson_name',
        'absent_teachers', 'total_teachers')
    ret = _new_export(m, cache_key, fields, excel_header, dict_keys)
    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def by_lessongrade(request):
    cache_key = 'teacher-absent-by-lessongrade'
    m = models.TotalTeachersLessonGrade
    fields = ('town_name', 'school_name', 'lesson_name',
              'grade_name', 'total')
    ret = _new_result(request, cache_key, m, fields)
    return ret
    # fields = ('class_uuid__grade__term__school__parent__name',
    #          'class_uuid__grade__term__school__name',
    #          'class_uuid__grade__name',
    #          'lesson_name__name')
    #ret = _result(request, cache_key, fields)
    # return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def by_lessongrade_export(request, *args, **kwargs):
    cache_key = 'teacher-absent-by-lessongrade'
    m = models.TotalTeachersLessonGrade
    fields = ('town_name', 'school_name', 'lesson_name',
              'grade_name', 'total')
    # fields = ('class_uuid__grade__term__school__parent__name',
    #          'class_uuid__grade__term__school__name',
    #          'class_uuid__grade__name',
    #          'lesson_name__name')
    excel_header = ['街道乡镇', '学校', '年级', '课程',
                    '未登录教师总数', '登记教师总数', '未授课占比（%）']
    dict_keys = ('town_name', 'school_name', 'grade_name', 'lesson_name',
                 'absent_teachers', 'total_teachers')
    ret = _new_export(m, cache_key, fields, excel_header, dict_keys)
    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def by_school(request):
    cache_key = 'teacher-absent-by-school'
    m = models.TotalTeachersSchool
    fields = (
        #'country_name',
        'town_name', 'school_name', 'total')
    ret = _new_result(request, cache_key, m, fields)
    return ret
    # fields = ('class_uuid__grade__term__school__parent__parent__name',
    #          'class_uuid__grade__term__school__parent__name',
    #          'class_uuid__grade__term__school__name')
    #ret = _result(request, cache_key, fields)
    # return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def by_school_export(request, *args, **kwargs):
    cache_key = 'teacher-absent-by-school'
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
        '未登录教师总数', '登记教师总数', '未授课占比（%）']
    dict_keys = (
        #'country_name',
        'town_name', 'school_name',
        'absent_teachers', 'total_teachers')
    ret = _new_export(m, cache_key, fields, excel_header, dict_keys)
    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def by_town(request):
    cache_key = 'teacher-absent-by-town'
    m = models.TotalTeachersTown
    fields = (
        #'country_name',
        'town_name', 'total')
    ret = _new_result(request, cache_key, m, fields)
    return ret
    # fields = ('class_uuid__grade__term__school__parent__parent__name',
    #          'class_uuid__grade__term__school__parent__name', )
    #ret = _result(request, cache_key, fields)
    # return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def by_town_export(request, *args, **kwargs):
    cache_key = 'teacher-absent-by-town'
    m = models.TotalTeachersTown
    fields = (
        #'country_name',
        'town_name', 'total')
    # fields = ('class_uuid__grade__term__school__parent__parent__name',
    #          'class_uuid__grade__term__school__parent__name', )
    excel_header = [
        #'区县市',
        '街道乡镇',
        '未登录教师总数', '登记教师总数', '未授课占比（%）']
    dict_keys = (
        #'country_name',
        'town_name',
        'absent_teachers', 'total_teachers')
    ret = _new_export(m, cache_key, fields, excel_header, dict_keys)
    return ret
