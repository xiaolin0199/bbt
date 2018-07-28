# coding=utf-8

import datetime
import json
import os
import uuid
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.utils.dateparse import parse_date
from BanBanTong import constants
from BanBanTong.db.models import TeacherLoginLog, Term, NewTerm
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import get_page_info
import xlwt


def query(cond, excludes):
    school_year = cond.get('school_year')
    term_type = cond.get('term_type')
    start_date = cond.get('start_date')
    end_date = cond.get('end_date')
    country_name = cond.get('country_name')
    town_name = cond.get('town_name')
    school_name = cond.get('school_name')
    grade_name = cond.get('grade_name')
    class_name = cond.get('class_name')
    lesson_name = cond.get('lesson_name')
    #resource_from = cond.get('resource_from')
    resource_type = cond.get('resource_type')
    teacher_name = cond.get('teacher_name')
    q = TeacherLoginLog.objects.exclude(**excludes)
    title = ''
    if start_date and end_date:
        s = parse_date(start_date)
        e = parse_date(end_date)
        s = datetime.datetime.combine(s, datetime.time.min)
        e = datetime.datetime.combine(e, datetime.time.max)
        q = q.filter(created_at__range=(s, e))
        title = '%s-%s' % (start_date.replace('-', ''),
                           end_date.replace('-', ''))
    elif school_year and term_type:
        q = q.filter(
            term_school_year=school_year,
            term_type=term_type
        )
        term = Term.objects.filter(school_year=school_year,
                                   term_type=term_type)

        title = '%s-%s' % (str(start_date).replace('-', ''),
                           str(end_date).replace('-', ''))
    else:
        term = NewTerm.get_nearest_term()
        if term:
            q = q.filter(term_school_year=term.school_year)
            q = q.filter(term_type=term.term_type)
            title = '%s-%s' % (str(term.start_date).replace('-', ''),
                               str(term.end_date).replace('-', ''))
    if country_name:
        q = q.filter(country_name=country_name)
    if town_name:
        q = q.filter(town_name=town_name)
    if school_name:
        q = q.filter(school_name=school_name)
    if grade_name:
        q = q.filter(grade_name=grade_name)
    if class_name:
        q = q.filter(class_name=class_name)
    if lesson_name:
        q = q.filter(lesson_name=lesson_name)
    # if resource_from:
    #    q = q.filter(resource_from=resource_from)
    if resource_type:
        q = q.filter(resource_type=resource_type)
    if teacher_name:
        q = q.filter(teacher_name__contains=teacher_name)

    total = q.count()
    #q = q.order_by('country_name', 'school_name', 'grade_name', 'class_name', 'teacher_name')
    return q, total, title


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('resource_type_statistic')
def _result(request, cache_key, fields, excludes):
    page_info = get_page_info(request)

    cache.set(cache_key, json.dumps(request.GET), None)
    q, total, title = query(request.GET, excludes)
    q = q.values(*fields).annotate(visit_count=Count('pk')).order_by(*fields)
    paginator = Paginator(q, page_info['page_size'])
    records = list(paginator.page(page_info['page_num']).object_list)
    return create_success_dict(data={
        'page': page_info['page_num'],
        'page_count': paginator.num_pages,
        'page_size': page_info['page_size'],
        'record_count': paginator.count,
        'records': records,
        'total': {
            'visit_count': total
        }
    })


def by_town(request):
    cache_key = 'resource-type-by-town'
    fields = ('town_name', 'resource_type',)
    excludes = {'resource_type': ''}
    ret = _result(request, cache_key, fields, excludes)
    return ret


def by_school(request):
    cache_key = 'resource-type-by-school'
    fields = ('town_name', 'school_name', 'resource_type',)
    excludes = {'resource_type': ''}
    ret = _result(request, cache_key, fields, excludes)
    return ret


def by_class(request):
    cache_key = 'resource-type-by-class'
    fields = ('town_name', 'school_name', 'grade_name', 'class_name', 'resource_type',)
    excludes = {'resource_type': ''}
    ret = _result(request, cache_key, fields, excludes)
    return ret


def by_lesson(request):
    cache_key = 'resource-type-by-lesson'
    fields = ('town_name', 'school_name', 'lesson_name', 'resource_type',)
    excludes = {'resource_type': ''}
    ret = _result(request, cache_key, fields, excludes)
    return ret


def by_teacher(request):
    cache_key = 'resource-type-by-teacher'
    fields = ('town_name', 'school_name', 'teacher_name', 'resource_type',)
    excludes = {'resource_type': ''}
    ret = _result(request, cache_key, fields, excludes)
    return ret


def _export(cache_key, query_fields,
            excludes, excel_header, dict_keys, node_type):
    c = cache.get(cache_key)
    if not c:
        return create_failure_dict(msg='查询超时无法导出，请重新查询！')
    cond = json.loads(c)
    q, total, title = query(cond, excludes)
    q = q.values(*query_fields)
    q = q.annotate(visit_count=Count('pk'))
    xls = xlwt.Workbook(encoding='utf8')
    if not title:
        title = u'资源类型使用统计'
    sheet = xls.add_sheet(title)
    for i in range(len(excel_header)):
        sheet.write(0, i, excel_header[i])
    row = 1
    for record in q:
        for i in range(len(dict_keys)):
            sheet.write(row, i, record[dict_keys[i]])
        try:
            percent = record['visit_count'] * 100.0 / total
        except:
            percent = 0.0
        percent = '%0.2f%%' % percent
        sheet.write(row, len(dict_keys), percent)
        row += 1
    sheet.write(row, dict_keys.index('visit_count') - 1, '合计使用次数')
    sheet.write(row, dict_keys.index('visit_count'), total)

    cached_id = str(uuid.uuid1())
    tmp_file = os.path.join(constants.CACHE_TMP_ROOT, cached_id)
    xls.save(tmp_file)
    d = {
        'town': u'街道乡镇',
        'school': u'学校',
        'grade': u'年级',
        'class': u'班级',
        'lesson': u'课程',
        'teacher': u'教师'
    }
    filename = u'资源类型使用统计_按%s导出.xls' % d[node_type]
    return create_success_dict(url=reverse('base:xls_download',
                                           kwargs={'cached_id': cached_id,
                                                   'name': filename}))


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('resource_type_statistic')
def by_town_export(request, *args, **kwargs):
    cache_key = 'resource-type-by-town'
    fields = ('town_name', 'resource_type',)
    excludes = {'resource_type': ''}

    excel_header = [
        '街道乡镇',
        '资源类型', '使用次数', '使用次数占比（%）']
    dict_keys = (
        'town_name',
        'resource_type', 'visit_count')
    ret = _export(cache_key, fields, excludes, excel_header, dict_keys, 'town')
    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('resource_type_statistic')
def by_school_export(request, *args, **kwargs):
    cache_key = 'resource-type-by-school'
    fields = ('town_name', 'school_name', 'resource_type',)
    excludes = {'resource_type': ''}

    excel_header = [
        '街道乡镇', '学校',
        '资源类型', '使用次数', '使用次数占比（%）']
    dict_keys = (
        'town_name', 'school_name',
        'resource_type', 'visit_count')
    ret = _export(cache_key, fields, excludes, excel_header, dict_keys, 'school')
    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('resource_type_statistic')
def by_class_export(request, *args, **kwargs):
    cache_key = 'resource-type-by-class'
    fields = ('town_name', 'school_name', 'grade_name', 'class_name', 'resource_type',)
    excludes = {'resource_type': ''}

    excel_header = [
        '街道乡镇', '学校', '年级', '班级',
        '资源类型', '使用次数', '使用次数占比（%）']
    dict_keys = (
        'town_name', 'school_name', 'grade_name', 'class_name',
        'resource_type', 'visit_count')
    ret = _export(cache_key, fields, excludes, excel_header, dict_keys, 'class')
    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('resource_type_statistic')
def by_lesson_export(request, *args, **kwargs):
    cache_key = 'resource-type-by-lesson'
    fields = ('town_name', 'school_name', 'lesson_name', 'resource_type',)
    excludes = {'resource_type': ''}

    excel_header = [
        '街道乡镇', '学校', '课程',
        '资源类型', '使用次数', '使用次数占比（%）']
    dict_keys = (
        'town_name', 'school_name', 'lesson_name',
        'resource_type', 'visit_count')
    ret = _export(cache_key, fields, excludes, excel_header, dict_keys, 'lesson')
    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('resource_type_statistic')
def by_teacher_export(request, *args, **kwargs):
    cache_key = 'resource-type-by-teacher'
    fields = ('town_name', 'school_name', 'teacher_name', 'resource_type',)
    excludes = {'resource_type': ''}

    excel_header = [
        '街道乡镇', '学校', '教师',
        '资源类型', '使用次数', '使用次数占比（%）']
    dict_keys = (
        'town_name', 'school_name', 'teacher_name',
        'resource_type', 'visit_count')
    ret = _export(cache_key, fields, excludes, excel_header, dict_keys, 'teacher')
    return ret
