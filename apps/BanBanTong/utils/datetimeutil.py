#!/usr/bin/env python
# coding=utf-8
import datetime
import traceback
from django.utils.dateparse import parse_date
from django.utils.dateparse import parse_time
from BanBanTong.db import models
import xlrd


def excel_cell_to_date(v, datemode=0):
    try:
        if isinstance(v, (str, unicode)):
            return parse_date(v)
        elif isinstance(v, float):
            return datetime.datetime.strptime(str(int(v)), '%Y%m%d').date()
        else:
            return None
    except:
        traceback.print_exc()
        return None


def excel_cell_to_time(v, datemode=0):
    try:
        if isinstance(v, (str, unicode)):
            return parse_time(v)
        elif isinstance(v, float):
            t = xlrd.xldate_as_tuple(v, datemode)
            return datetime.time(t[3], t[4], t[5])
        else:
            return None
    except:
        traceback.print_exc()
        return None


def excel_float_to_date(f, datemode=0):
    if f > 1:
        return datetime.datetime.strptime(str(int(f)), '%Y%m%d').date()
    else:
        t = xlrd.xldate_as_tuple(f, datemode)
        return datetime.time(t[3], t[4], t[5])


def get_week_number(term, s, e):
    '''计算给定时间(s, e)为学期的第几周'''
    weekday = term.start_date.weekday()
    start_monday = term.start_date - datetime.timedelta(days=weekday)
    if term.start_date <= s.date() <= term.end_date:
        days = (s.date() - start_monday).days
        return days / 7 + 1
    elif term.start_date <= e.date() <= term.end_date:
        days = (e.date() - start_monday).days
        return days / 7 + 1
    else:
        return -1


def check_date_range(request):
    '''
        用于middleware，检查时间范围是否在一个学期内
        1. 如果是start_date和end_date：
            1.1 start_date在某个学期内，记为t1
                start_date不在学期内，就查找离它最近的下一个学期t1
                如果没有符合条件的t1，报错退出
            1.2 end_date在某个学期内，记为t2
                end_date不在学期内，就查找离它最近的前一个学期t2
                如果没有符合条件的t2，报错退出
            1.3 如果t1 == t2，return t1
                否则报错退出
        2. 如果是school_year和term_type，直接获取对应的学期，或者报错退出
        3. 如果server_type是区县市级，就从NewTerm检查
        4. TODO 如果server_type是地市州，怎么处理？
    '''
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    school_year = request.GET.get('school_year')
    term_type = request.GET.get('term_type')
    server_type = models.Setting.getvalue('server_type')
    # o = models.Setting.objects.get(name='server_type') # 测试表锁定的问题
    if start_date and end_date:
        s = parse_date(start_date)
        e = parse_date(end_date)
        try:
            if server_type == 'school':
                t1 = models.Term.objects.get(start_date__lte=s, end_date__gte=s)
            elif server_type == 'country':
                t1 = models.NewTerm.objects.get(start_date__lte=s, end_date__gte=s)
            elif not server_type:
                return u'获取服务器参数失败'
        except:
            if server_type == 'school':
                t1 = models.Term.objects.filter(start_date__gte=s)
            elif server_type == 'country':
                t1 = models.NewTerm.objects.filter(start_date__gte=s)
            t1 = t1.order_by('start_date')
            if t1.exists():
                t1 = t1[0]
            else:
                # return u'开始时间(%s)不在任何学期内' % start_date
                return u'开始时间(%s)后没有可用学年学期' % start_date
        try:
            if server_type == 'school':
                t2 = models.Term.objects.get(start_date__lte=e, end_date__gte=e)
            elif server_type == 'country':
                t2 = models.NewTerm.objects.get(start_date__lte=e, end_date__gte=e)
        except:
            if server_type == 'school':
                t2 = models.Term.objects.filter(end_date__lte=e)
            elif server_type == 'country':
                t2 = models.NewTerm.objects.filter(end_date__lte=e)
            t2 = t2.order_by('-end_date')
            if t2.exists():
                t2 = t2[0]
            else:
                # return u'结束时间(%s)不在任何学期内' % end_date
                return u'结束时间(%s)前没有可用学年学期' % end_date
        if t1 == t2:
            return t1
        else:
            if t1.end_date < t2.start_date:
                return u'查询时间范围仅限单个学期时间段内'
            else:
                return u'查询时间范围内无可用学年学期'
    elif school_year and term_type:
        try:
            if server_type == 'school':
                t = models.Term.objects.get(school_year=school_year,
                                            term_type=term_type)
            elif server_type == 'country':
                t = models.NewTerm.objects.get(school_year=school_year,
                                               term_type=term_type)
            return t
        except:
            return u'查询的学年学期(%s%s)不存在' % (school_year, term_type)
    else:
        return u'请选择时间范围或学年学期'


def get_term_from_date_range(request):
    '''
        获取时间范围对应的学期
        1. 如果是start_date和end_date：
            1.1 start_date在某个学期内，记为t1
                start_date不在学期内，就查找离它最近的下一个学期t1
                如果没有符合条件的t1，报错退出
            1.2 end_date在某个学期内，记为t2
                end_date不在学期内，就查找离它最近的前一个学期t2
                如果没有符合条件的t2，报错退出
            1.3 如果t1 == t2，return t1
                否则报错退出
        2. 如果是school_year和term_type，直接获取对应的学期，或者报错退出
        3. 如果server_type不是校级，上述查询条件要加上school_uuid
    '''
    start_date = request.REQUEST.get('start_date')
    end_date = request.REQUEST.get('end_date')
    school_year = request.REQUEST.get('school_year')
    term_type = request.REQUEST.get('term_type')
    current_term = request.REQUEST.get('current_term', 'false')
    server_type = models.Setting.getvalue('server_type')
    if server_type == 'school':
        school = models.Group.objects.get(group_type='school')
    else:
        school_uuid = request.REQUEST.get('uuid')
        school = models.Group.objects.get(uuid=school_uuid)
    if start_date and end_date:
        s = parse_date(start_date)
        e = parse_date(end_date)
        try:
            t1 = models.Term.objects.get(start_date__lte=s, end_date__gte=s,
                                         school=school)
        except:
            t1 = models.Term.objects.filter(start_date__gte=s, school=school)
            t1 = t1.order_by('start_date')
            if t1.exists():
                t1 = t1[0]
            else:
                return u'开始时间(%s)不在任何学期内' % start_date
        try:
            t2 = models.Term.objects.get(start_date__lte=e, end_date__gte=e,
                                         school=school)
        except:
            t2 = models.Term.objects.filter(end_date__lte=e, school=school)
            t2 = t2.order_by('-end_date')
            if t2.exists():
                t2 = t2[0]
            else:
                return u'结束时间(%s)不在任何学期内' % end_date
        if t1 == t2:
            return t1
        else:
            return u'开始时间(%s)(%s%s)与结束时间(%s)(%s%s)不在同一学期内' % (start_date, t1.school_year, t1.term_type, end_date, t2.school_year, t2.term_type)
    elif school_year and term_type:
        try:
            t = models.Term.objects.get(school_year=school_year,
                                        term_type=term_type, school=school)
            return t
        except:
            return u'查询的学年学期(%s%s)不存在' % (school_year, term_type)
    else:
        if current_term == 'true':
            try:
                return models.Term.get_current_term_list(school=school)[0]
            except Exception as e:
                pass

        # return u'请选择时间范围或学年学期'
