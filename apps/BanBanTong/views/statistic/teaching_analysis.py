# coding=utf-8
import logging
import cPickle
from django.core.cache import cache
from django.db.models import Sum
from django.conf import settings
from BanBanTong.db import models
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import model_list_to_dict
from BanBanTong.utils.get_cache_timeout import get_timeout as _t
from .utils import common_query_for_statistic


logger = logging.getLogger(__name__)


def remain_to_finish(request, *args, **kwargs):
    return create_failure_dict(data=u'需求尚未完善或后台尚未实现')


def url_has_been_abandoned(request, *args, **kwargs):
    return create_failure_dict(msg=u'该API已经废弃,注意对应更新一下下代码.')


def lesson_count(request, *args, **kwargs):
    """班班通授课综合分析>课程授课次数分析"""
    _lst = (
        u'语文', u'数学', u'英语', u'音乐',
        u'美术', u'信息技术', u'品德与生活',
        u'品德与社会', u'思想品德', u'物理',
        u'化学', u'生物', u'历史', u'地理',
    )
    objs, conditions = common_query_for_statistic(request, 'lesson')
    term = ''
    ret, childs, others = [], [], []
    if objs.exists():
        childs = objs.filter(name__in=_lst).values('name').distinct()
        others = objs.exclude(name__in=_lst)
        others_count = others.aggregate(x=Sum('teach_count'))['x']
        others_count = others_count and others_count or 0
        childs = childs.annotate(x=Sum('teach_count')).order_by('-x').values('name', 'x')
        ret = [{'name': i['name'], 'lesson_count': i['x']} for i in childs]
        ret.append({'name': u'其他', 'lesson_count': others_count})

    return create_success_dict(
        data=ret,
        term=term,
        debug={
            '#node-len': len(objs),
            '#total-len': len(childs),
            '#remains-len': len(ret),
            '#others-len': len(others),
            '#total': sum([i['lesson_count'] for i in ret])
        }
    )


def grade_count(request, *args, **kwargs):
    """年级授课次数分析"""
    def _divmod(x, y):
        try:
            y = int(y)
            if y <= 0:
                y = 1.0
        except:
            y = 1.0
        ans = '%.2f' % (x * 1.0 / y)
        return float(ans)

    _index = (
        u'一', u'二', u'三', u'四',
        u'五', u'六', u'七', u'八',
        u'九', u'十', u'十一', u'十二',
        u'电脑教室',
        '一', '二', '三', '四',
        '五', '六', '七', '八',
        '九', '十', '十一', '十二',
        '电脑教室',
    )
    objs, conditions = common_query_for_statistic(request, 'grade')
    objs = objs.values('name').distinct().annotate(x=Sum('teach_count'), y=Sum('class_count'))
    ret = {i: {'grade_name': _index[i - 1], 'sum': 0, 'average': 0, 'class_count': 0}
           for i in range(1, 13)}
    for i in objs:
        ret[_index.index(i['name']) % 12 + 1].update({
            'grade_name': i['name'],
            'sum': i['x'],
            'average': _divmod(i['x'], i['y']),
            'class_count': i['y']
        })
    ret = [ret[i] for i in ret]
    ret.sort(key=lambda d: _index.index(d['grade_name']))
    return create_success_dict(
        data=ret,
        debug={
            '#grade_count': len(objs),
            '#items_count': len(ret),
        }
    )


def _query(request, terms):
    conditions = {}
    for key in ('town_name', 'school_name', 'grade_name', 'class_name'):
        value = request.GET.get(key, None)
        if value:
            conditions[key] = value

    objs = models.TeacherLoginCountWeekly.objects.filter(term__in=terms)
    objs = objs.filter(**conditions)
    objs = objs.values('week').annotate(lesson_count=Sum('lesson_count')).order_by('week')
    if objs:
        d = dict(objs.values_list('week', 'lesson_count', flat=False))
        max_week = max(d.keys())
        range_week = max_week + 1 if max_week > 20 else 21
        objs = [{'week': i, 'week_count': 0} for i in range(1, range_week)][:max_week]
        for i in objs:
            i['week_count'] = d.get(i['week'], 0)
    return objs


def week_count(request, term=None, get_average=False, get_total=False):
    """班班通授课综合分析>周授课次数分析"""
    school_year = request.GET.get('school_year', None)
    term_type = request.GET.get('term_type', None)
    if not term:
        terms = models.Term.objects.all()
        if school_year and term_type:
            terms = terms.filter(school_year=school_year, term_type=term_type)
            term = terms.exists() and terms[0] or terms

    if not (school_year or term_type) and not term:
        # term = models.NewTerm.get_current_term()
        term = models.NewTerm.get_nearest_term()

    cached_value = None
    key = None
    if term:
        _cache_key_prefix = 'teaching-analysis-week-count'
        town_name = request.GET.get('town_name')
        school_name = request.GET.get('school_name')
        grade_name = request.GET.get('grade_name')
        class_name = request.GET.get('class_name')
        key = '%s:%s-%s-%s-%s-%s-%s' % (
            _cache_key_prefix,
            term.school_year,
            term.term_type,
            town_name,
            school_name,
            grade_name,
            class_name
        )
        if not settings.DEBUG:
            cached_value = cache.get(key)

    if cached_value:
        records = cPickle.loads(cached_value)
    else:
        if term:
            # 查询指定的学年学期的数据
            terms = models.Term.objects.filter(
                school_year=term.school_year,
                term_type=term.term_type
            )
        else:
            terms = models.Term.get_current_term_list()
        objs = _query(request, terms)
        records = model_list_to_dict(objs)
        if key:
            cache.set(key, cPickle.dumps(records, cPickle.HIGHEST_PROTOCOL), _t(key, 60 * 60 * 4))

    # 下面两种情况是用于其他函数调用
    # 返回未格式化的原始数据
    if get_average:
        # 如果是求平均的话,就需要计算班级总数
        # 返回数据格式: {1: 1.2222, 2: 2.344}
        if not term and terms:
            term = terms[0]
        cond = models.Statistic.get_filter_condition(request.REQUEST, 'class', term)
        # cond = models.Statistic.get_filter_condition({'school_year': term.school_year, 'term_type': term.term_type}, 'class', term)
        class_count = models.Statistic.objects.filter(**cond).count()
        class_count = class_count > 0 and class_count or 1

        for i in records:
            i['week_count'] = i['week_count'] * 1.0 / (class_count)
        records = {i['week']: i['week_count'] for i in records}
    elif get_total:
        # 如果是求累积的话
        # 返回数据格式: {1: 2, 2: 4, 3: 6}
        records = {i['week']: i['week_count'] for i in records}
        records = records and records or {1: 0}
        for i in range(1, max(records.keys()) + 1):
            records[i] = records[i] + records.get(i - 1, 0)

    return create_success_dict(data=records)


def week_count_average(request, *args, **kwargs):
    """周授课次数分析>平均"""
    school_year = request.GET.get('school_year', None)
    term_type = request.GET.get('term_type', None)
    if school_year and term_type:
        try:
            current_term = models.NewTerm.objects.get(
                school_year=school_year,
                term_type=term_type
            )
        except Exception as e:
            return create_failure_dict(msg=u'学年学期获取失败', debug=str(e))
    else:
        current_term = models.NewTerm.get_current_term()
    term_previous = request.GET.get('count_previous', False)
    term_lastyear = request.GET.get('count_lastyear', False)
    d0 = week_count(request, current_term, True)['data']
    if not d0:
        d0 = {1: 0}
    d1 = {1: 0}
    if term_previous == 'true':
        term = models.NewTerm.get_previous_term(current_term)
        d1 = term and week_count(request, term, True)['data'] or {1: 0}

    d2 = {1: 0}
    if term_lastyear == 'true':
        term = models.NewTerm.get_lastyear_term(current_term)
        d2 = term and week_count(request, term, True)['data'] or {1: 0}

    max_week = max([max(d0.keys()), max(d1.keys()), max(d2.keys())])
    data = []
    for i in range(1, max_week + 1):
        d = {'week': i, 'count_current': float('%.2f' % d0.get(i, 0))}
        if term_previous == 'true':
            d['count_previous'] = float('%.2f' % d1.get(i, 0))
        if term_lastyear == 'true':
            d['count_lastyear'] = float('%.2f' % d2.get(i, 0))
        data.append(d)
    return create_success_dict(data=data)


def _query2(request, terms):
    conditions = {}
    for key in ('town_name', 'school_name', 'grade_name', 'class_name'):
        value = request.GET.get(key, None)
        if value:
            conditions[key] = value

    objs = models.TeacherLoginTimeWeekly.objects.filter(term__in=terms)
    # print conditions
    objs = objs.filter(**conditions)
    objs = objs.values('week').annotate(total_time=Sum('total_time')).order_by('week')
    if objs:
        d = dict(objs.values_list('week', 'total_time', flat=False))
        max_week = max(d.keys())
        range_week = max_week + 1 if max_week > 20 else 21
        objs = [{'week': i, 'week_time': 0} for i in range(1, range_week)][:max_week]
        for i in objs:
            i['week_time'] = d.get(i['week'], 0)
    return objs


def week_time(request, term=None, get_average=False, get_total=False):
    """班班通授课综合分析>周授课时长分析"""
    school_year = request.GET.get('school_year', None)
    term_type = request.GET.get('term_type', None)
    if not term:
        terms = models.Term.objects.all()
        if school_year and term_type:
            terms = terms.filter(school_year=school_year, term_type=term_type)
            term = terms[0]

    if not (school_year or term_type) and not term:
        # term = models.NewTerm.get_current_term()
        term = models.NewTerm.get_nearest_term()

    cached_value = None
    key = None
    if term:
        _cache_key_prefix = 'teaching-analysis-week-time'
        town_name = request.GET.get('town_name')
        school_name = request.GET.get('school_name')
        grade_name = request.GET.get('grade_name')
        class_name = request.GET.get('class_name')
        key = '%s:%s-%s-%s-%s-%s-%s' % (
            _cache_key_prefix,
            term.school_year,
            term.term_type,
            town_name,
            school_name,
            grade_name,
            class_name
        )
        if not settings.DEBUG:
            cached_value = cache.get(key)

    if cached_value:
        records = cPickle.loads(cached_value)
    else:
        if term:
            terms = models.Term.objects.filter(
                school_year=term.school_year,
                term_type=term.term_type
            )
        else:
            terms = models.Term.get_current_term_list()
        objs = _query2(request, terms)
        records = model_list_to_dict(objs)
        if key:
            cache.set(key, cPickle.dumps(records, cPickle.HIGHEST_PROTOCOL), _t(key, 60 * 60 * 4))

    # 下面两种情况是用于其他函数调用
    # 返回未格式化的原始数据
    if get_average:
        # 如果是求平均的话,就需要计算班级总数
        # 返回数据格式: {1: 1.2222, 2: 2.344}
        if not term and terms:
            term = terms[0]
        cond = models.Statistic.get_filter_condition(request.REQUEST, 'class', term)
        # cond = models.Statistic.get_filter_condition({'school_year': term.school_year, 'term_type': term.term_type}, 'class', term)
        class_count = models.Statistic.objects.filter(**cond).count()
        class_count = class_count > 0 and class_count or 1
        for i in records:
            i['week_time'] = i['week_time'] * 1.0 / class_count / 60
        records = {i['week']: i['week_time'] for i in records}

    elif get_total:
        # 如果是求累积的话
        # 返回数据格式: {1: 2, 2: 4, 3: 6}
        records = {i['week']: i['week_time'] * 1.0 / 60 for i in records}
        records = records and records or {1: 0}
        for i in range(1, max(records.keys()) + 1):
            records[i] = records[i] + records.get(i - 1, 0)

    else:
        records = [{
            'week': i['week'],
            'week_time': float('%.0f' % (i['week_time'] * 1.0 / 60))
        } for i in records]

    return create_success_dict(data=records)


def week_time_average(request, *args, **kwargs):
    """周授课时长分析>平均"""
    term_previous = request.GET.get('time_previous', False)
    term_lastyear = request.GET.get('time_lastyear', False)
    school_year = request.GET.get('school_year', None)
    term_type = request.GET.get('term_type', None)
    if school_year and term_type:
        try:
            current_term = models.NewTerm.objects.get(
                school_year=school_year,
                term_type=term_type
            )
        except Exception as e:
            return create_failure_dict(msg=u'学年学期获取失败', debug=str(e))
    else:
        current_term = models.NewTerm.get_current_term()

    d0 = week_time(request, current_term, True)['data']
    d0 = d0 and d0 or {1: 0}

    d1 = {1: 0}
    if term_previous == 'true':
        term = models.NewTerm.get_previous_term(current_term)
        d1 = term and week_time(request, term, True)['data'] or {1: 0}

    d2 = {1: 0}
    if term_lastyear == 'true':
        term = models.NewTerm.get_lastyear_term(current_term)
        d2 = term and week_time(request, term, True)['data'] or {1: 0}

    max_week = max([max(d0.keys()), max(d1.keys()), max(d2.keys())])
    data = []
    for i in range(1, max_week + 1):
        d = {'week': i, 'time_current': float('%.2f' % d0.get(i, 0))}
        if term_previous == 'true':
            d['time_previous'] = float('%.2f' % d1.get(i, 0))
        if term_lastyear == 'true':
            d['time_lastyear'] = float('%.2f' % d2.get(i, 0))
        data.append(d)
    return create_success_dict(data=data)


def _total(request, term, func, key, get_average):
    d = func(request, term, False, True)['data']
    records = [{'week': i, key: d[i]} for i in range(1, max(d.keys()) + 1)]

    if get_average:
        if not term:
            # 默认查询当前学年学期的数据
            terms = models.Term.get_current_term_list()
            term = terms and terms[0] or None
        cond = models.Statistic.get_filter_condition(request.REQUEST, 'class', term)
        # cond = models.Statistic.get_filter_condition({'school_year': term.school_year, 'term_type': term.term_type}, 'class', term)
        class_count = models.Statistic.objects.filter(**cond).count()
        class_count = class_count > 0 and class_count or 1

        for i in records:
            i[key] = i[key] * 1.0 / (class_count)
        records = {i['week']: i[key] for i in records}

    # 周授课累积时长分析返回数据精确到小数点后两位.
    elif key == 'total_time':
        for i in records:
            i[key] = float('%.2f' % i[key])
    return records


def _average(request, func, prefix):
    school_year = request.GET.get('school_year', None)
    term_type = request.GET.get('term_type', None)
    if school_year and term_type:
        try:
            current_term = models.NewTerm.objects.get(
                school_year=school_year,
                term_type=term_type
            )
        except Exception as e:
            logger.exception(e)
            current_term = None
            # return create_failure_dict(msg=u'学年学期获取失败', debug=str(e))
    else:
        current_term = models.NewTerm.get_current_term()

    term_previous = request.GET.get('term_previous',
                                    request.GET.get('count_previous',
                                                    request.GET.get('time_previous', False)))
    term_lastyear = request.GET.get('term_lastyear',
                                    request.GET.get('count_lastyear',
                                                    request.GET.get('time_lastyear', False)))
    d0 = func(request, current_term, True)['data']

    d1 = {1: 0}
    if term_previous == 'true':
        term = models.NewTerm.get_previous_term(current_term)
        d1 = term and func(request, term, True)['data'] or {1: 0}

    d2 = {1: 0}
    if term_lastyear == 'true':
        term = models.NewTerm.get_lastyear_term(current_term)
        d2 = term and func(request, term, True)['data'] or {1: 0}

    max_week = max([max(d0.keys()), max(d1.keys()), max(d2.keys())])
    data = []
    for i in range(1, max_week + 1):
        key = '%s_current' % prefix
        d = {'week': i, key: float('%.2f' % d0.get(i, 0))}
        if term_previous == 'true':
            key = '%s_previous' % prefix
            d[key] = float('%.2f' % d1.get(i, 0))
        if term_lastyear == 'true':
            key = '%s_lastyear' % prefix
            d[key] = float('%.2f' % d2.get(i, 0))
        data.append(d)

    return data


def week_count_total(request, term=None, get_average=False):
    """周授课累积次数分析"""
    records = _total(request, term, week_count, 'total_count', get_average)
    return create_success_dict(data=records)


def week_count_total_average(request, *args, **kwargs):
    """周授课累积次数分析>平均"""
    data = _average(request, week_count_total, 'count')
    return create_success_dict(data=data)


def week_time_total(request, term=None, get_average=False):
    """周授课累积时长分析"""
    records = _total(request, term, week_time, 'total_time', get_average)
    return create_success_dict(data=records)


def week_time_total_average(request, *args, **kwargs):
    """周授课时长分析>平均"""
    data = _average(request, week_time_total, 'time')
    return create_success_dict(data=data)
