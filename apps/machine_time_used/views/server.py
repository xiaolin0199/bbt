# coding=utf-8
import csv
import os
import uuid
import xlwt
import datetime
import traceback
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Sum, Count
from django.http.response import HttpResponse
from django.utils.dateparse import parse_date

from BanBanTong.db import models as db_models
from BanBanTong import constants
from BanBanTong.utils import decorator
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import paginatoooor
from machine_time_used import models


def _query(request, *args, **fields):
    # 前端参数传递的时候,查询的时候使用的是GET,导出的时候又使用的是POST
    # 这里使用request.REQUEST
    school_year = request.REQUEST.get('school_year', None)
    term_type = request.REQUEST.get('term_type', None)
    start_date = request.REQUEST.get('start_date', None)
    end_date = request.REQUEST.get('end_date', None)

    town_name = request.REQUEST.get('town_name', None)
    school_name = request.REQUEST.get('school_name', None)
    grade_name = request.REQUEST.get('grade_name', None)
    class_name = request.REQUEST.get('class_name', None)

    o = models.MachineTimeUsed.objects.all()
    o = o.filter(**fields)
    title = u'导出'

    if start_date and end_date:
        title = '%s-%s' % (start_date.replace('-', ''), end_date.replace('-', ''))
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)
        s = datetime.datetime.combine(start_date, datetime.time.min)
        e = datetime.datetime.combine(end_date, datetime.time.max)
        o = o.filter(create_time__range=(s, e))

    else:
        # 按学年学期查询
        if not school_year and not term_type:
            # 自然时间和学年学期都未提供时候,默认查询当前学年学期或最近的一个
            t = db_models.NewTerm.get_nearest_term()
            if t:
                school_year = t.school_year
                term_type = t.term_type
        if school_year:
            o = o.filter(term_school_year=school_year)
            title = school_year
        if term_type:
            o = o.filter(term_type=term_type)
            if school_year:
                term = db_models.Term.objects.filter(school_year=school_year,
                                                     term_type=term_type)
                if term.exists():
                    term = term[0]
                    title = '%s-%s' % (str(term.start_date).replace('-', ''),
                                       str(term.end_date).replace('-', ''))

    if town_name:
        o = o.filter(town_name=town_name)
    if school_name:
        o = o.filter(school_name=school_name)
    if grade_name:
        o = o.filter(grade_name=grade_name)
    if class_name:
        o = o.filter(class_name=class_name)

    o = o.order_by('town_name', 'school_name', 'grade_name')

    return o, title


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('machine_time_used_statistic')
def by_town(request, export=False, *args, **kwargs):
    o, title = _query(request)

    total = {'use_time_total': 0,
             'use_count_total': 0}
    if o.exists():
        total['use_time_total'] = o.aggregate(total=Sum('use_time'))['total']
        total['use_count_total'] = o.aggregate(total=Sum('use_count'))['total']

        ret = o.values('town_name').annotate(use_time_total=Sum('use_time'), use_count_total=Sum('use_count'), use_days=Count('uuid'))

        for i in ret:
            i['use_time_average'] = '{0:.2f}'.format(i['use_time_total'] * 1.0 / i['use_days'])
            i['use_count_average'] = '{0:.2f}'.format(i['use_count_total'] * 1.0 / i['use_days'])

            i['class_count'] = o.filter(town_name=i['town_name']).values('school_name', 'grade_name', 'class_name').distinct().count()

        #towns = list(set(o.values_list('town_name', flat=True)))
        # for town in towns:
        #    q = o.filter(town_name=town)
        #    if not q.exists():
        #        continue
        #    # 学校-年级-班级
        #    class_names = set(map(lambda i: '%s%s%s' % (i[0], i[1], i[2]), #去重
        #        q.values_list('school_name', 'grade_name', 'class_name', flat=False)))
        #    ret.append({
        #        'town_name': town,
        #        'class_count': len(class_names),
        #        'use_time_average': '{0:.2f}'.format(q.aggregate(avg=Avg('use_time'))['avg']),
        #        'use_time_total': q.aggregate(total=Sum('use_time'))['total'],
        #        'use_count_average': '{0:.2f}'.format(q.aggregate(avg=Avg('use_count'))['avg']),
        #        'use_count_total': q.aggregate(total=Sum('use_count'))['total'],
        #    })
        if export:
            return ret, total, title
        return paginatoooor(request, ret, total=total)
    if export:
        return None, total, title
    # return create_failure_dict(msg='该时间段内无机器使用记录')
    return paginatoooor(request, [], total=total)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('machine_time_used_statistic')
def by_school(request, export=False, *args, **kwargs):
    o, title = _query(request)

    total = {'use_time_total': 0,
             'use_count_total': 0}
    if o.exists():
        total['use_time_total'] = o.aggregate(total=Sum('use_time'))['total']
        total['use_count_total'] = o.aggregate(total=Sum('use_count'))['total']

        ret = o.values('town_name', 'school_name').annotate(use_time_total=Sum('use_time'), use_count_total=Sum('use_count'), use_days=Count('uuid'))

        for i in ret:
            i['use_time_average'] = '{0:.2f}'.format(i['use_time_total'] * 1.0 / i['use_days'])
            i['use_count_average'] = '{0:.2f}'.format(i['use_count_total'] * 1.0 / i['use_days'])

            i['class_count'] = o.filter(town_name=i['town_name'], school_name=i['school_name']).values('grade_name', 'class_name').distinct().count()

        #ret = []
        #towns = list(set(o.values_list('town_name', flat=True)))
        #schools = list(set(o.values_list('school_name', flat=True)))
        # for town in towns:
        #    for school in schools:
        #        q = o.filter(town_name=town,
        #                     school_name=school)
        #        if not q.exists():
        #            continue
        #        # 年级-班级
        #        class_names = set(map(lambda i: '%s%s' % (i[0], i[1]), #去重
        #            q.values_list('grade_name', 'class_name', flat=False)))
        #        ret.append({
        #            'town_name': town,
        #            'school_name': school,
        #
        #            'class_count': len(class_names),
        #            'use_time_average': '{0:.2f}'.format(q.aggregate(avg=Avg('use_time'))['avg']),
        #            'use_time_total': q.aggregate(total=Sum('use_time'))['total'],
        #            'use_count_average': '{0:.2f}'.format(q.aggregate(avg=Avg('use_count'))['avg']),
        #            'use_count_total': q.aggregate(total=Sum('use_count'))['total'],
        #        })
        if export:
            return ret, total, title
        return paginatoooor(request, ret, total=total)
    if export:
        return None, total, title
    # return create_failure_dict(msg='该时间段内无机器使用记录')
    return paginatoooor(request, [], total=total)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('machine_time_used_statistic')
def by_grade(request, export=False, *args, **kwargs):
    o, title = _query(request)

    total = {'use_time_total': 0,
             'use_count_total': 0}
    if o.exists():
        total['use_time_total'] = o.aggregate(total=Sum('use_time'))['total']
        total['use_count_total'] = o.aggregate(total=Sum('use_count'))['total']

        ret = o.values('town_name', 'school_name', 'grade_name').annotate(use_time_total=Sum('use_time'),
                                                                          use_count_total=Sum('use_count'), use_days=Count('uuid'), class_count=Count('class_name', distinct=True))

        for i in ret:
            i['use_time_average'] = '{0:.2f}'.format(i['use_time_total'] * 1.0 / i['use_days'])
            i['use_count_average'] = '{0:.2f}'.format(i['use_count_total'] * 1.0 / i['use_days'])

        #ret = []
        #towns = list(set(o.values_list('town_name', flat=True)))
        #schools = list(set(o.values_list('school_name', flat=True)))
        #grades = list(set(o.values_list('grade_name', flat=True)))
        # for town in towns:
        #    for school in schools:
        #        for grade in grades:
        #            q = o.filter(town_name=town,
        #                         school_name=school,
        #                         grade_name=grade)
        #            if not q.exists():
        #                continue
        #            class_names = set(q.values_list('class_name', flat=True))
        #            ret.append({
        #                'town_name': town,
        #                'school_name': school,
        #                'grade_name': grade,
        #
        #                'class_count': len(class_names),
        #                'use_time_average': '{0:.2f}'.format(q.aggregate(avg=Avg('use_time'))['avg']),
        #                'use_time_total': q.aggregate(total=Sum('use_time'))['total'],
        #                'use_count_average': '{0:.2f}'.format(q.aggregate(avg=Avg('use_count'))['avg']),
        #                'use_count_total': q.aggregate(total=Sum('use_count'))['total'],
        #            })
        if export:
            return ret, total, title
        return paginatoooor(request, ret, total=total)
    if export:
        return None, total, title
    # return create_failure_dict(msg='该时间段内无机器使用记录')
    return paginatoooor(request, [], total=total)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('machine_time_used_statistic')
def by_class(request, export=False, *args, **kwargs):
    o, title = _query(request)

    total = {'use_time_total': 0,
             'use_count_total': 0}
    if o.exists():
        total['use_time_total'] = o.aggregate(total=Sum('use_time'))['total']
        total['use_count_total'] = o.aggregate(total=Sum('use_count'))['total']

        ret = o.values('town_name', 'school_name', 'grade_name', 'class_name').annotate(use_time_total=Sum('use_time'), use_count_total=Sum('use_count'), use_days=Count('uuid'))

        for i in ret:

            i['use_time_average'] = '{0:.2f}'.format(i['use_time_total'] * 1.0 / i['use_days'])
            i['use_count_average'] = '{0:.2f}'.format(i['use_count_total'] * 1.0 / i['use_days'])

        #ret = []
        #towns = list(set(o.values_list('town_name', flat=True)))
        #schools = list(set(o.values_list('school_name', flat=True)))
        #grades = list(set(o.values_list('grade_name', flat=True)))
        #classes = list(set(o.values_list('class_name', flat=True)))
        #
        # for town in towns:
        #    for school in schools:
        #        for grade in grades:
        #            for cls in classes:
        #                q = o.filter(town_name=town,
        #                             school_name=school,
        #                             grade_name=grade,
        #                             class_name=cls)
        #                if not q.exists():
        #                    continue
        #                ret.append({
        #                    'town_name': town,
        #                    'school_name': school,
        #                    'grade_name': grade,
        #                    'class_name': cls,
        #
        #                    'use_time_average': '{0:.2f}'.format(q.aggregate(avg=Avg('use_time'))['avg']),
        #                    'use_time_total': q.aggregate(total=Sum('use_time'))['total'],
        #                    'use_count_average': '{0:.2f}'.format(q.aggregate(avg=Avg('use_count'))['avg']),
        #                    'use_count_total': q.aggregate(total=Sum('use_count'))['total'],
        #                })
        if export:
            return ret, total, title
        return paginatoooor(request, ret, total=total)
    if export:
        return None, total, title
    # return create_failure_dict(msg='该时间段内无机器使用记录')
    return paginatoooor(request, [], total=total)


def _export(request, ret, total, title, header, dict_keys):
    def __format_minutes(min):
        return u'%s天%s小时%s分' % (min / 1440, min % 1440 / 60, min % 60)

    cached_id = str(uuid.uuid1())
    tmp_file = os.path.join(constants.CACHE_TMP_ROOT, cached_id)

    try:
        export_type = constants.BANBANTONG_DEFAULT_EXPORT_TYPE.upper()
        if export_type not in ['XLS', 'CSV']:
            export_type = 'XLS'
    except Exception:
        export_type = 'XLS'

    if export_type == 'XLS':
        xls = xlwt.Workbook(encoding='utf8')
        sheet = xls.add_sheet(title)

        for i, v in enumerate(header):
            sheet.write(0, i, v)

        row = 1
        if ret:
            for record in ret:
                for i, key in enumerate(dict_keys):
                    if key == 'use_time_total':
                        sheet.write(row, i, __format_minutes(record[key]))
                    else:
                        sheet.write(row, i, record[key])

                row += 1

        sheet.write(row, dict_keys.index('use_time_total') - 1, u'合计')
        sheet.write(row, dict_keys.index('use_time_total'), __format_minutes(total['use_time_total']))
        sheet.write(row, dict_keys.index('use_count_total'), total['use_count_total'])

        xls.save(tmp_file)
        filename = u'学校终端开机使用统计_%s.xls' % title

    elif export_type == 'CSV':
        filename = u'学校终端开机使用统计_%s.csv' % title
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % (filename.encode('utf-8', 'ignore'))
        writer = csv.writer(response)
        # 写CSV头
        writer.writerow(header)
        for record in ret:
            row_data = []
            for key in dict_keys:
                row_data.append(unicode(record[key]).encode('utf-8', 'ignore'))
            writer.writerow(row_data)

        with open(tmp_file, 'wb') as f:
            f.write(response.content)

    return create_success_dict(url=reverse('base:xls_download',
                                           kwargs={'cached_id': cached_id,
                                                   'name': filename}))


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('machine_time_used_statistic')
def by_town_export(request, *args, **kwargs):
    ret, total, title = by_town(request, export=True)
    header = [u'乡镇街道', u'班级总数', u'日平均开机时长(分钟)',
              u'日平均开机次数', u'开机总时长', u'开机总次数']
    dict_keys = ['town_name', 'class_count', 'use_time_average',
                 'use_count_average', 'use_time_total', 'use_count_total']
    return _export(request, ret, total, title, header, dict_keys)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('machine_time_used_statistic')
def by_school_export(request, *args, **kwargs):
    ret, total, title = by_school(request, export=True)
    header = [u'乡镇街道', u'学校', u'班级总数', u'日平均开机时长(分钟)',
              u'日平均开机次数', u'开机总时长', u'开机总次数']
    dict_keys = ['town_name', 'school_name', 'class_count', 'use_time_average',
                 'use_count_average', 'use_time_total', 'use_count_total']
    return _export(request, ret, total, title, header, dict_keys)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('machine_time_used_statistic')
def by_grade_export(request, *args, **kwargs):
    ret, total, title = by_grade(request, export=True)
    header = [u'乡镇街道', u'学校', u'年级', u'班级总数', u'日平均开机时长(分钟)',
              u'日平均开机次数', u'开机总时长', u'开机总次数']
    dict_keys = ['town_name', 'school_name', 'grade_name', 'class_count', 'use_time_average',
                 'use_count_average', 'use_time_total', 'use_count_total']
    return _export(request, ret, total, title, header, dict_keys)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('machine_time_used_statistic')
def by_class_export(request, *args, **kwargs):
    ret, total, title = by_class(request, export=True)
    header = [u'乡镇街道', u'学校', u'年级', u'班级', u'日平均开机时长(分钟)',
              u'日平均开机次数', u'开机总时长', u'开机总次数']
    dict_keys = ['town_name', 'school_name', 'grade_name', 'class_name', 'use_time_average',
                 'use_count_average', 'use_time_total', 'use_count_total']
    return _export(request, ret, total, title, header, dict_keys)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('machine_time_used_log')
def terminal_time_used_log(request, export=False, *args, **kwargs):
    try:
        grade_name = request.GET.get('grade_name', None)
        class_name = request.GET.get('class_name', None)
        o, title = _query(request)

        total = {'use_time_total': 0,
                 'use_count_total': 0}
        if o.exists():
            if grade_name:
                o = o.filter(grade_name=grade_name)

            if class_name:
                o = o.filter(class_name=class_name)
            total['use_time_total'] = o.aggregate(total=Sum('use_time'))['total']
            total['use_count_total'] = o.aggregate(total=Sum('use_count'))['total']
            ret = []
            for i in o:
                ret.append({'town_name': i.town_name,
                            'school_name': i.school_name,
                            'grade_name': i.grade_name,
                            'class_name': i.class_name,
                            'mac': i.mac,
                            'create_time': str(i.create_time)[:10],
                            'use_time': i.use_time,
                            'use_count': i.use_count
                            })
            if export:
                return ret, total, title
            return paginatoooor(request, ret, total=total)
        if export:
            return None, total, title
        return paginatoooor(request, [], total=total)
    except:
        if settings.DEBUG:
            traceback.print_exc()
        return paginatoooor(request, [], total=total)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('machine_time_used_log')
def terminal_time_used_log_export(request, *args, **kwargs):
    ret, total, title = terminal_time_used_log(request, export=True)
    header = [u'乡镇街道', u'学校', u'年级', u'班级', u'使用日期',
              u'开机时长(分钟)', u'开机次数']
    dict_keys = ['town_name', 'school_name', 'grade_name', 'class_name', 'create_time',
                 'use_time', 'use_count']
    return _export(request, ret, total, title, header, dict_keys)
