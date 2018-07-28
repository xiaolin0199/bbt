# coding=utf-8
import os
import uuid
import json
import datetime

from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.db.models import Q
from django.db.models import Sum, Count
from django.db.models.query import QuerySet
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date

from BanBanTong import constants
from BanBanTong.db.models import Setting, Term, NewTerm
import xlwt
from BanBanTong.utils import decorator
from BanBanTong.utils import paginatoooor
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import get_page_info
from BanBanTong.utils.str_util import format_byte

from edu_point import models


def _query(request):
    f = Setting.getvalue
    province_name = request.REQUEST.get('province_name', f('province'))
    city_name = request.REQUEST.get('city_name', f('city'))
    country_name = request.REQUEST.get('country_name', f('country'))
    town_name = request.REQUEST.get('town_name', None)
    point_name = request.REQUEST.get('point_name', None)
    start_date = request.REQUEST.get('start_date', None)
    end_date = request.REQUEST.get('end_date', None)
    school_year = request.REQUEST.get('school_year', None)
    term_type = request.REQUEST.get('term_type', None)
    title = u'导出'

    o = models.EduPoint.objects.all()
    m = models.EduPointMachineTimeUsed.objects.all()
    o = o.filter(province_name=province_name)
    o = o.filter(city_name=city_name)
    o = o.filter(country_name=country_name)
    m = m.filter(province_name=province_name)
    m = m.filter(city_name=city_name)
    m = m.filter(country_name=country_name)

    if town_name:
        o = o.filter(town_name=town_name)
        m = m.filter(town_name=town_name)

    if point_name:
        o = o.filter(point_name=point_name)
        m = m.filter(point_name=point_name)

    days = 1.0
    now = datetime.datetime.today().date()
    if school_year or term_type:
        if school_year:
            o = o.filter(school_year=school_year)
            m = m.filter(school_year=school_year)
            title = school_year
        if term_type:
            o = o.filter(term_type=term_type)
            m = m.filter(term_type=term_type)
            if school_year:
                term = NewTerm.objects.filter(school_year=school_year,
                                              term_type=term_type)
                if term.exists():
                    term = term[0]
                    title = '%s-%s' % (str(term.start_date).replace('-', ''),
                                       str(term.end_date).replace('-', ''))
                    days = (now - term.start_date).days
    elif start_date and end_date:
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)
        s = datetime.datetime.combine(start_date, datetime.time.min)
        e = datetime.datetime.combine(end_date, datetime.time.max)

        cond = Q(start_date__lte=s, end_date__gte=s)
        cond |= Q(start_date__gte=s, end_date__lte=e)
        cond |= Q(start_date__lte=e, end_date__gte=e)
        terms = list(NewTerm.objects.filter(cond))
        for t in terms:
            if terms.index(t) == 0:
                cond = Q(school_year=t.school_year, term_type=t.term_type)
            else:
                cond |= Q(school_year=t.school_year, term_type=t.term_type)

        o = o.filter(cond)
        m = m.filter(create_time__range=(start_date, end_date))
        days = (now - start_date).days
        days = days and days or 1.0

    else:
        term = NewTerm.get_nearest_term()
        if term:
            o = o.filter(
                school_year=term.school_year,
                term_type=term.term_type
            )
            m = m.filter(
                school_year=term.school_year,
                term_type=term.term_type
            )
            title = '%s-%s' % (str(term.start_date).replace('-', ''),
                               str(term.end_date).replace('-', ''))
            days = (now - term.start_date).days

    o = o.order_by('school_year', 'term_type', 'country_name',
                   'town_name', 'point_name', '-create_time', )
    return o, m, title, abs(days)


def _export(request, ret, total, title, header, dict_keys):
    def __format_minutes(min):
        return u'%s天%s小时%s分' % (min / 1440, min % 1440 / 60, min % 60)

    cached_id = str(uuid.uuid1())
    tmp_file = os.path.join(constants.CACHE_TMP_ROOT, cached_id)
    xls = xlwt.Workbook(encoding='utf8')
    sheet = xls.add_sheet(title)

    for i, v in enumerate(header):
        sheet.write(0, i, v)
    if 'boot_time_average' in dict_keys:
        filename = u'教学点终端开机统计%s.xls' % title
    else:
        filename = u'教学点教室使用统计%s.xls' % title
    row = 1
    if ret:
        for record in ret:
            for i, key in enumerate(dict_keys):
                if key == 'boot_time_total':
                    sheet.write(row, i, __format_minutes(record[key]))
                else:
                    sheet.write(row, i, record[key])
            row += 1
        try:
            if 'boot_time_average' in dict_keys:
                sheet.write(row, dict_keys.index('boot_time_total') - 1, u'合计')
                sheet.write(row, dict_keys.index('boot_time_total'), __format_minutes(total['boot_time_total']))
                sheet.write(row, dict_keys.index('boot_count_total'), total['boot_count_total'])

            else:
                sheet.write(row, dict_keys.index('use_time') - 1, u'合计')
                sheet.write(row, dict_keys.index('use_time'), total['use_time'])
                sheet.write(row, dict_keys.index('to_class_time'), total['to_class_time'])
                sheet.write(row, dict_keys.index('boot_time'), total['boot_time'])
                sheet.write(row, dict_keys.index('percent'), total['percent'])
        except:
            import traceback
            traceback.print_exc()
    xls.save(tmp_file)
    return create_success_dict(url=reverse('base:xls_download',
                                           kwargs={'cached_id': cached_id,
                                                   'name': filename}))


def _aggregate(objs, machine_time_objs, count_room=False):
    """获取统计数据：获取终端开机数据、终端使用数据、教室总数"""
    room = None
    if isinstance(objs, QuerySet):
        base = objs.values_list('pk', flat=True)
    elif isinstance(objs, models.EduPointDetail):
        room = objs
        base = [objs.edupoint.pk, ]
        objs = objs.edupoint
    else:
        base = [objs.pk, ]

    # 1.获取终端开机数据、终端使用数据
    o = machine_time_objs
    o = o.filter(edupoint__in=base)
    if room:
        o = o.filter(edupointdetail=room)
    boot_time_total = o.aggregate(x=Sum('boot_time'))['x']
    boot_count_total = o.aggregate(x=Sum('boot_count'))['x']
    use_time_total = o.aggregate(x=Sum('use_time'))['x']
    # use_count_total = o.aggregate(x=Sum('xxxxx'))['x']

    if not boot_time_total:
        boot_time_total = 0
    if not boot_count_total:
        boot_count_total = 0
    if not use_time_total:
        use_time_total = 0
    # if not use_count_total:
    #    use_count_total = 0

    d = {}
    d['use_time'] = use_time_total
    # d['use_count'] = use_count_total
    d['boot_time'] = boot_time_total
    d['boot_count'] = boot_count_total
    d['to_class_time'] = '{0:.2f}'.format(d['use_time'] / 45.0)
    d['percent'] = '{0:.2f}%'.format(use_time_total * 1.0 /
                                     (boot_time_total and boot_time_total or 1) * 100
                                     )

    # 2.获取教室总数
    if count_room:
        d['room_count'] = objs.aggregate(n=Sum('number'))['n']

    return d


# 教学点教室使用统计(使用时长,开机时长)
@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('edu_unit_classroom_statistic')
def classroom_use_by_town(request, export=False, *args, **kwargs):
    """教学点教室使用统计>按乡镇街道"""
    edu_objs, timeused_objs, title, days = _query(request)
    total = _aggregate(edu_objs, timeused_objs)
    ret = []
    if edu_objs.exists():
        towns = list(set(edu_objs.values_list('town_name', flat=True)))
        for town in towns:
            p = edu_objs.filter(town_name=town)
            if not p.exists():
                continue
            d = _aggregate(p, timeused_objs, True)
            d['town_name'] = town
            ret.append(d)
    if export:
        return ret, total, title
    return paginatoooor(request, ret, total=total)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('edu_unit_classroom_statistic')
def classroom_use_by_unit(request, export=False, *args, **kwargs):
    """教学点教室使用统计>按教学点"""
    edu_objs, timeused_objs, title, days = _query(request)
    total = _aggregate(edu_objs, timeused_objs)
    ret = []
    if edu_objs.exists():
        towns = list(set(edu_objs.values_list('town_name', flat=True)))
        for town in towns:
            p = edu_objs.filter(town_name=town)
            if not p.exists():
                continue
            points = list(set(p.values_list('point_name', flat=True)))
            for point in points:
                q = p.filter(point_name=point)
                if not q.exists():
                    continue
                d = _aggregate(q, timeused_objs, True)
                d['town_name'] = town
                d['point_name'] = point
                ret.append(d)
    if export:
        return ret, total, title
    return paginatoooor(request, ret, total=total)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('edu_unit_classroom_statistic')
def classroom_use_by_unit_class(request, export=False, *args, **kwargs):
    """教学点教室使用统计>按教学点教室"""
    edu_objs, timeused_objs, title, days = _query(request)
    total = _aggregate(edu_objs, timeused_objs)
    ret = []
    if edu_objs.exists():
        rooms = models.EduPointDetail.objects.none()
        for i in edu_objs:
            rooms |= i.edupointdetail_set.filter(type='room')
        for i in rooms:
            d = _aggregate(i, timeused_objs)
            d['town_name'] = i.edupoint.town_name
            d['point_name'] = i.edupoint.point_name
            d['name'] = i.name
            ret.append(d)

    if export:
        return ret, total, title
    return paginatoooor(request, ret, total=total)


def classroom_use_by_town_export(request, *args, **kwargs):
    ret, total, title = classroom_use_by_town(request, export=True)
    header = [u'乡镇街道', u'教室总数', u'使用时长(分钟)', u'折合课时（45分钟/节）',
              u'开机时长(分钟)', u'使用占比(%)']
    dict_keys = ['town_name', 'room_count', 'use_time', 'to_class_time',
                 'boot_time', 'percent']
    return _export(request, ret, total, title, header, dict_keys)


def classroom_use_by_unit_export(request, *args, **kwargs):
    ret, total, title = classroom_use_by_unit(request, export=True)
    header = [u'乡镇街道', u'教学点', u'教室总数', u'使用时长(分钟)', u'折合课时（45分钟/节）',
              u'开机时长(分钟)', u'使用占比(%)']
    dict_keys = ['town_name', 'point_name', 'room_count', 'use_time', 'to_class_time', 'boot_time', 'percent']
    return _export(request, ret, total, title, header, dict_keys)


def classroom_use_by_unit_class_export(request, *args, **kwargs):
    ret, total, title = classroom_use_by_unit_class(request, export=True)
    header = [u'乡镇街道', u'教学点', u'教室编号', u'使用时长(分钟)', u'折合课时（45分钟/节）',
              u'开机时长(分钟)', u'使用占比(%)']
    dict_keys = ['town_name', 'point_name', 'name', 'use_time', 'to_class_time', 'boot_time', 'percent']
    return _export(request, ret, total, title, header, dict_keys)


# 教学点终端开机统计
@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('edu_unit_machine_time_used_statistic')
def terminal_boot_by_town(request, export=False, *args, **kwargs):
    """教学点终端开机统计>按乡镇街道"""
    o, m, title, days = _query(request)
    total = {
        'boot_time_total': _aggregate(o, m)['boot_time'],
        'boot_count_total': _aggregate(o, m)['boot_count']
    }
    ret = []
    if o.exists():
        towns = list(set(o.values_list('town_name', flat=True)))
        for town in towns:
            p = o.filter(town_name=town)
            if not p.exists():
                continue
            d = _aggregate(p, m, True)
            ret.append({
                'town_name': town,
                'room_count': d['room_count'],

                'boot_time_total': d['boot_time'],
                'boot_count_total': d['boot_count'],
                'boot_time_average': '%.2f' % (d['boot_time'] * 1.0 / days),
                'boot_count_average': '%.2f' % (d['boot_count'] * 1.0 / days),
            })
    if export:
        return ret, total, title
    return paginatoooor(request, ret, total=total, days=days)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('edu_unit_machine_time_used_statistic')
def terminal_boot_by_unit(request, export=False, *args, **kwargs):
    """教学点终端开机统计>按教学点"""
    o, m, title, days = _query(request)
    total = {
        'boot_time_total': _aggregate(o, m)['boot_time'],
        'boot_count_total': _aggregate(o, m)['boot_count']
    }
    ret = []
    if o.exists():
        towns = list(set(o.values_list('town_name', flat=True)))
        for town in towns:
            p = o.filter(town_name=town)
            if not p.exists():
                continue
            points = list(set(p.values_list('point_name', flat=True)))
            for point in points:
                q = p.filter(point_name=point)
                if not q.exists():
                    continue
                d = _aggregate(q, m, True)
                ret.append({
                    'town_name': town,
                    'point_name': point,
                    'room_count': d['room_count'],

                    'boot_time_total': d['boot_time'],
                    'boot_count_total': d['boot_count'],

                    'boot_time_average': '%.2f' % (d['boot_time'] * 1.0 / days),
                    'boot_count_average': '%.2f' % (d['boot_count'] * 1.0 / days),
                })
    if export:
        return ret, total, title
    return paginatoooor(request, ret, total=total, days=days)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('edu_unit_machine_time_used_statistic')
def terminal_boot_by_unit_class(request, export=False, *args, **kwargs):
    """教学点终端开机统计>按教学点教室"""
    o, m, title, days = _query(request)
    total = {
        'boot_time_total': _aggregate(o, m)['boot_time'],
        'boot_count_total': _aggregate(o, m)['boot_count']
    }
    ret = []
    if o.exists():
        towns = list(set(o.values_list('town_name', flat=True)))
        for town in towns:
            p = o.filter(town_name=town)
            if not p.exists():
                continue
            points = list(set(p.values_list('point_name', flat=True)))
            for point in points:
                q = p.filter(point_name=point)
                if not q.exists():
                    continue
                # d = _aggregate(q, m)
                lst = map(lambda i: {
                    'town_name': town,
                    'point_name': point,
                    'number': i.number,

                    'boot_time_total': _aggregate(i, m)['boot_time'],
                    'boot_count_total': _aggregate(i, m)['boot_count'],
                    'boot_time_average': '%.2f' % (_aggregate(i, m)['boot_time'] * 1.0 / days),
                    'boot_count_average': '%.2f' % (_aggregate(i, m)['boot_count'] * 1.0 / days),
                }, q)
                ret.extend(lst)

    if export:
        return ret, total, title
    return paginatoooor(request, ret, total=total)


def terminal_boot_by_town_export(request, *args, **kwargs):
    ret, total, title = terminal_boot_by_town(request, export=True)
    header = [u'乡镇街道', u'教室终端总数', u'日平均开机时长(分钟)', u'日平均开机次数', u'开机总时长', u'开机总次数']
    dict_keys = ['town_name', 'room_count', 'boot_time_average', 'boot_count_average', 'boot_time_total', 'boot_count_total']
    return _export(request, ret, total, title, header, dict_keys)


def terminal_boot_by_unit_export(request, *args, **kwargs):
    ret, total, title = terminal_boot_by_unit(request, export=True)
    header = [u'乡镇街道', u'教学点', u'教室终端总数', u'日平均开机时长(分钟)', u'日平均开机次数', u'开机总时长', u'开机总次数']
    dict_keys = ['town_name', 'point_name', 'room_count', 'boot_time_average', 'boot_count_average', 'boot_time_total', 'boot_count_total']
    return _export(request, ret, total, title, header, dict_keys)


# 卫星资源接收统计
def _resource_store_query(cond):
    school_year = cond.get('school_year')
    term_type = cond.get('term_type')
    start_date = cond.get('start_date')
    end_date = cond.get('end_date')
    town_name = cond.get('town_name')
    point_name = cond.get('point_name')

    title = u''
    q = models.EduPointResourceReceLog.objects.all()
    e = models.EduPoint.objects.all()
    if school_year or term_type:
        if school_year:
            q = q.filter(school_year=school_year)
            e = e.filter(school_year=school_year)
            title = school_year
        if term_type:
            q = q.filter(term_type=term_type)
            e = e.filter(term_type=term_type)
            if school_year:
                term = Term.objects.filter(school_year=school_year,
                                           term_type=term_type)
                if term.exists():
                    term = term[0]
                    title = u'%s-%s' % (str(term.start_date).replace('-', ''),
                                        str(term.end_date).replace('-', ''))
    elif start_date and end_date:
        start = parse_date(start_date)
        end = parse_date(end_date)
        start = datetime.datetime.combine(start, datetime.time.min)
        end = datetime.datetime.combine(end, datetime.time.max)
        q = q.filter(rece_time__range=(start, end))
        e = e.filter(create_time__range=(start, end))
        title = u'%s-%s' % (start_date.replace('-', ''),
                            end_date.replace('-', ''))
    else:
        term = NewTerm.get_nearest_term()
        if term:
            q = q.filter(
                school_year=term.school_year,
                term_type=term.term_type
            )
            e = e.filter(
                school_year=term.school_year,
                term_type=term.term_type
            )
            title = u'%s-%s' % (str(term.start_date).replace('-', ''),
                                str(term.end_date).replace('-', ''))

    if town_name:
        q = q.filter(town_name=town_name)
        e = e.filter(town_name=town_name)
    if point_name:
        q = q.filter(point_name=point_name)
        e = e.filter(point_name=point_name)

    # 资源接收总大小
    total_resource_size = q.aggregate(total=Sum('rece_size'))['total']
    if not total_resource_size:
        total_resource_size = 0

    # 资源接收总个数
    total_resource_count = q.aggregate(total=Sum('rece_count'))['total']
    if not total_resource_count:
        total_resource_count = 0

    q = q.order_by('town_name', 'point_name')

    return q, total_resource_size, total_resource_count, title, e


def _format_resource_store_result_by_town(records, cache_key):
    ret = []
    for d in records:
        d_new = {}
        # 街道乡镇名称
        d_new['town_name'] = d['town_name']
        # 教学点个数
        d_new['total_unit'] = d['total_unit']

        # 文件总大小
        d_new['total_size'] = format_byte(d['total_size'])
        # 每个教学点文件平均大小
        d_new['avg_size'] = format_byte(round(float(d['total_size']) / d['total_unit'], 2))

        # 文件总个数
        d_new['total_count'] = d['total_count']
        # 每个教学点文件平均个数
        d_new['avg_count'] = round(float(d['total_count']) / d['total_unit'], 2)

        # 文件的各类数量
        d_new['total_type'] = d['total_type']

        ret.append(d_new)

    return ret


def _resource_store_result_by_town(request, cache_key, fields):
    page_info = get_page_info(request)

    cache.set(cache_key, json.dumps(request.GET), None)
    q, total_resource_size, total_resource_count, title, e = _resource_store_query(request.GET)

    q = q.values(*fields)

    q = q.annotate(total_unit=Count('point_name', distinct=True), total_count=Sum('rece_count'), total_size=Sum('rece_size'), total_type=Sum('rece_type'))

    # 显示所有的街道，以及下面的教学点数量
    e = e.values(*fields).annotate(total_unit=Count(*fields))
    for i in e:
        i['total_count'] = 0
        i['total_size'] = 0
        i['total_type'] = 0
        for j in q:
            if i['town_name'] == j['town_name']:
                i['total_count'] = j['total_count']
                i['total_size'] = j['total_size']
                i['total_type'] = j['total_type']
                break

    paginator = Paginator(e, page_info['page_size'])
    records = list(paginator.page(page_info['page_num']).object_list)

    records = _format_resource_store_result_by_town(records, cache_key)

    ret = create_success_dict(data={
        'page': page_info['page_num'],
        'page_count': paginator.num_pages,
        'page_size': page_info['page_size'],
        'record_count': paginator.count,
        'records': records,
        'total_resource_size': format_byte(total_resource_size),
        'total_resource_count': total_resource_count
    })

    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('resource_satellite_statistic')
def resource_store_by_town(request):
    """资源使用>卫星资源接收统计>按乡镇街道"""
    cache_key = 'resource-store-by-town'
    fields = ('town_name', )
    ret = _resource_store_result_by_town(request, cache_key, fields)

    return ret

# ----------------------------------


def _format_resource_store_result_by_unit(records, cache_key):
    ret = []
    for d in records:
        d_new = {}
        d_new['town_name'] = d['town_name']
        d_new['point_name'] = d['point_name']
        d_new['total_size'] = format_byte(d['total_size'])
        d_new['total_count'] = d['total_count']
        d_new['total_type'] = d['total_type']

        ret.append(d_new)

    return ret


def _resource_store_result_by_unit(request, cache_key, fields):
    page_info = get_page_info(request)

    cache.set(cache_key, json.dumps(request.GET), None)
    q, total_resource_size, total_resource_count, title, e = _resource_store_query(request.GET)

    q = q.values(*fields)

    q = q.annotate(total_count=Sum('rece_count'), total_size=Sum('rece_size'), total_type=Sum('rece_type'))
    # 显示所有的街道，以及下面的教学点数量
    e = e.values(*fields)
    for i in e:
        i['total_count'] = 0
        i['total_size'] = 0
        i['total_type'] = 0
        for j in q:
            if i['town_name'] == j['town_name'] and i['point_name'] == j['point_name']:
                i['total_count'] = j['total_count']
                i['total_size'] = j['total_size']
                i['total_type'] = j['total_type']
                break

    paginator = Paginator(e, page_info['page_size'])
    records = list(paginator.page(page_info['page_num']).object_list)

    records = _format_resource_store_result_by_unit(records, cache_key)

    ret = create_success_dict(data={
        'page': page_info['page_num'],
        'page_count': paginator.num_pages,
        'page_size': page_info['page_size'],
        'record_count': paginator.count,
        'records': records,
        'total_resource_size': format_byte(total_resource_size),
        'total_resource_count': total_resource_count
    })

    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('resource_satellite_statistic')
def resource_store_by_unit(request, *args, **kwargs):
    """资源使用>卫星资源接收统计>按教学点"""
    cache_key = 'resource-store-by-unit'
    fields = ('town_name', 'point_name', )
    ret = _resource_store_result_by_unit(request, cache_key, fields)

    return ret

# -------------------------------------


def _export_by_town(cache_key, fields, excel_header, dict_keys):
    c = cache.get(cache_key)
    if not c:
        return create_failure_dict(msg='查询超时无法导出，请重新查询！')

    cond = json.loads(c)
    q, total_resource_size, total_resource_count, title, e = _resource_store_query(cond)
    q = q.values(*fields)
    q = q.annotate(total_unit=Count('point_name', distinct=True), total_count=Sum('rece_count'), total_size=Sum('rece_size'), total_type=Sum('rece_type'))
    # 显示所有的街道，以及下面的教学点数量
    e = e.values(*fields).annotate(total_unit=Count(*fields))
    for i in e:
        i['total_count'] = 0
        i['total_size'] = 0
        i['total_type'] = 0
        for j in q:
            if i['town_name'] == j['town_name']:
                i['total_count'] = j['total_count']
                i['total_size'] = j['total_size']
                i['total_type'] = j['total_type']
                break

    xls = xlwt.Workbook(encoding='utf8')
    if not title:
        title = u'教学点卫星资源统计_按街道乡镇'
    sheet = xls.add_sheet(title)
    for i in range(len(excel_header)):
        sheet.write(0, i, excel_header[i])
    row = 1

    l = _format_resource_store_result_by_town(e, cache_key)

    for record in l:
        for i in range(len(dict_keys)):
            sheet.write(row, i, record[dict_keys[i]])
        row += 1
    sheet.write(row, len(dict_keys) - 3, '合计')
    sheet.write(row, len(dict_keys) - 2, u'大小: %s' % format_byte(total_resource_size))
    sheet.write(row, len(dict_keys) - 1, u'数量: %s' % total_resource_count)

    cached_id = str(uuid.uuid1())
    tmp_file = os.path.join(constants.CACHE_TMP_ROOT, cached_id)
    xls.save(tmp_file)
    filename = u'教学点卫星资源统计_按街道乡镇_%s.xls' % title

    return create_success_dict(url=reverse('base:xls_download',
                                           kwargs={'cached_id': cached_id,
                                                   'name': filename}))


def resource_store_by_town_export(request, *args, **kwargs):
    """资源使用>卫星资源接收统计>按乡镇街道"""
    cache_key = 'resource-store-by-town'
    fields = ('town_name',)

    excel_header = ['街道乡镇', '教学点个数', '资源文件个数', '资源文件种类',
                    '资源文件大小', '平均接收大小/教学点']
    dict_keys = ('town_name', 'total_unit', 'total_count',
                 'total_type', 'total_size', 'avg_size')

    ret = _export_by_town(cache_key, fields, excel_header, dict_keys)

    return ret


def _export_by_unit(cache_key, fields, excel_header, dict_keys):
    c = cache.get(cache_key)
    if not c:
        return create_failure_dict(msg='查询超时无法导出，请重新查询！')

    cond = json.loads(c)
    q, total_resource_size, total_resource_count, title, e = _resource_store_query(cond)
    q = q.values(*fields)
    q = q.annotate(total_count=Sum('rece_count'), total_size=Sum('rece_size'), total_type=Sum('rece_type'))
    # 显示所有的街道，以及下面的教学点数量
    e = e.values(*fields)
    for i in e:
        i['total_count'] = 0
        i['total_size'] = 0
        i['total_type'] = 0
        for j in q:
            if i['town_name'] == j['town_name'] and i['point_name'] == j['point_name']:
                i['total_count'] = j['total_count']
                i['total_size'] = j['total_size']
                i['total_type'] = j['total_type']
                break

    xls = xlwt.Workbook(encoding='utf8')
    if not title:
        title = u'教学点卫星资源统计_按教学点'
    sheet = xls.add_sheet(title)
    for i in range(len(excel_header)):
        sheet.write(0, i, excel_header[i])
    row = 1

    l = _format_resource_store_result_by_unit(e, cache_key)

    for record in l:
        for i in range(len(dict_keys)):
            sheet.write(row, i, record[dict_keys[i]])
        row += 1
    sheet.write(row, len(dict_keys) - 3, u'合计')
    sheet.write(row, len(dict_keys) - 2, u'大小: %s' % format_byte(total_resource_size))
    sheet.write(row, len(dict_keys) - 1, u'数量: %s' % total_resource_count)

    cached_id = str(uuid.uuid1())
    tmp_file = os.path.join(constants.CACHE_TMP_ROOT, cached_id)
    xls.save(tmp_file)
    filename = u'教学点卫星资源统计_按教学点_%s.xls' % title

    return create_success_dict(url=reverse('base:xls_download',
                                           kwargs={'cached_id': cached_id,
                                                   'name': filename}))


def resource_store_by_unit_export(request, *args, **kwargs):
    """资源使用>卫星资源接收统计>按教学点"""
    cache_key = 'resource-store-by-unit'
    fields = ('town_name', 'point_name', )

    excel_header = ['街道乡镇', '教学点', '资源文件个数', '资源文件种类', '资源文件大小']
    dict_keys = ('town_name', 'point_name', 'total_count', 'total_type', 'total_size')

    ret = _export_by_unit(cache_key, fields, excel_header, dict_keys)

    return ret
