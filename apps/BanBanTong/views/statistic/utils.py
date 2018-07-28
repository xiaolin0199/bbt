# coding=utf-8
import logging
from BanBanTong.db import models
from django.utils.dateparse import parse_date
from django.db.models import Case, When

logger = logging.getLogger(__name__)


def check_if_query_by_date(old_view):
    """
        授课次数和授课时长统计中,按自然时间查询的时候,只能通过旧的方法进行查询和
        导出,这里定义一个装饰器,检测到是通过自然时间查询的时候,直接使用旧方法
    """
    def _func(func):
        def _inner(request, *args, **kwargs):
            start_date = request.REQUEST.get('start_date')
            end_date = request.REQUEST.get('end_date')
            if start_date and end_date:
                logger.debug('use old views export')
                return old_view(request, *args, **kwargs)
            else:
                return func(request, *args, **kwargs)
        return _inner
    return _func


def sort_statistic(base_objs, node_type):
    grade_lst = [
        u'一', u'二', u'三', u'四', u'五',
        u'六', u'七', u'八', u'九', u'十',
        u'十一', u'十二', u'电脑教室',
        '一', '二', '三', '四', '五',
        '六', '七', '八', '九', '十',
        '十一', '十二', '电脑教室'
    ]
    class_lst = [str(i) for i in range(1, 30)]

    sorted_objs = []
    if node_type == 'town':
        sorted_objs = base_objs.order_by('name')
    elif node_type == 'school':
        sorted_objs = base_objs.order_by('parent__name', 'name')
    elif node_type == 'grade':
        order_grade = Case(*[When(name=name, then=i) for i, name in enumerate(grade_lst)])
        sorted_objs = base_objs.order_by('parent__parent__name', 'parent__name', order_grade)
    elif node_type == 'class':
        order_grade = Case(*[When(parent__name=name, then=i) for i, name in enumerate(grade_lst)])
        order_class = Case(*[When(name=name, then=i) for i, name in enumerate(class_lst)])
        sorted_objs = base_objs.order_by('parent__parent__parent__name', 'parent__parent__name', order_grade, order_class)
    elif node_type == 'lesson':
        # order_grade = Case(*[When(parent__parent__name=name, then=i) for i, name in enumerate(grade_lst)])
        sorted_objs = base_objs.order_by(
            'parent__parent__parent__parent__name', 'parent__parent__parent__name',
            # order_grade, 'parent__name', # 年级班级
            'name'
        )
    elif node_type == 'lessonteacher':
        order_grade = Case(*[When(parent__parent__parent__name=name, then=i) for i, name in enumerate(grade_lst)])
        order_class = Case(*[When(parent__parent__name=name, then=i) for i, name in enumerate(class_lst)])
        sorted_objs = base_objs.order_by(
            'parent__parent__parent__parent__parent__name', 'parent__parent__parent__parent__name',
            order_grade, order_class,  # 'parent__parent__name',
            # 'parent__name', # 课程
            'name'
        )
    elif node_type == 'teacher':
        # order_grade = Case(*[When(parent__parent__parent__name=name, then=i) for i, name in enumerate(grade_lst)])
        # order_class = Case(*[When(parent__parent__name=name, then=i) for i, name in enumerate(class_lst)])
        sorted_objs = base_objs.order_by(
            'parent__parent__parent__parent__parent__name', 'parent__parent__parent__parent__name',
            # order_grade, order_class,  # 'parent__parent__name',
            # 'parent__name', # 课程
            'name'
        )
    else:
        return base_objs
    return sorted_objs


def get_schedule_time(school_year, term_type):
    server_type = models.Setting.getvalue('server_type')
    if server_type != 'school':
        try:
            term = models.NewTerm.objects.get(
                school_year=school_year,
                term_type=term_type
            )
            return term.schedule_time
        except:
            return 0
    try:
        term = models.Term.objects.get(
            school_year=school_year,
            term_type=term_type
        )
        return term.schedule_time
    except models.Term.MultipleObjectsReturned:
        logger.exception('')
        terms = models.Term.objects.filter(
            school_year=school_year,
            term_type=term_type
        )
        return terms[0].schedule_time
    except:
        return 0


def get_term_from_date_range(request):
    start_date = request.REQUEST.get('start_date')
    end_date = request.REQUEST.get('end_date')
    school_year = request.REQUEST.get('school_year')
    term_type = request.REQUEST.get('term_type')
    server_type = models.Setting.getvalue('server_type')
    if server_type == 'school':
        model_base = models.Term
    else:
        model_base = models.NewTerm

    if start_date and end_date:
        s = parse_date(start_date)
        e = parse_date(end_date)
        try:
            t1 = model_base.objects.get(start_date__lte=s, end_date__gte=s)
        except:
            furture_terms = model_base.objects.filter(start_date__gte=s)
            furture_terms = furture_terms.order_by('start_date')
            if furture_terms.exists():
                t1 = furture_terms[0]
            else:
                return None
        try:
            t2 = model_base.objects.get(start_date__lte=e, end_date__gte=e)
        except:
            past_terms = model_base.objects.filter(end_date__lte=e)
            past_terms = past_terms.order_by('start_date')
            if past_terms.exists():
                t2 = past_terms[past_terms.count() - 1]
            else:
                return None

        if t1 == t2:
            return t1

    elif school_year and term_type:
        try:
            t = model_base.objects.get(school_year=school_year, term_type=term_type)
            return t
        except:
            return None

    return None


def common_query_for_statistic(request, node_type):
    """单独把该查询摘出来,提供给其他views复用代码"""
    school_year = request.REQUEST.get('school_year')
    term_type = request.REQUEST.get('term_type')
    start_date = request.REQUEST.get('start_date')
    end_date = request.REQUEST.get('end_date')

    # country_name = request.REQUEST.get('country_name')
    # town_name = request.REQUEST.get('town_name')
    # school_name = request.REQUEST.get('school_name')
    # grade_name = request.REQUEST.get('grade_name')
    # class_name = request.REQUEST.get('class_name')

    cond = models.Statistic.get_filter_condition(request.REQUEST, node_type)
    objs = models.Statistic.objects.filter(**cond)

    if node_type == 'lesson':
        town_name = cond.get('town_name')
        school_name = cond.get('school_name')
        if not town_name and school_name:
            # 子级条件是以父级条件的存在为前提
            return models.Statistic.objects.none(), {'pk': -1}
    if school_year or term_type:
        return objs, cond

    else:
        if start_date and end_date:
            # 这个分支提供给按自然时间查询的时候获取父级的达标率用
            term = get_term_from_date_range(request)
            term = isinstance(term, (models.Term, models.NewTerm)) and term or None
        else:
            server_type = models.Setting.getvalue('server_type')
            if server_type != 'school':
                term = models.NewTerm.get_current_term()
                if not term:
                    term = models.NewTerm.get_previous_term()
            else:
                term = models.Term.get_current_term_list()
                if not term:
                    term = models.Term.get_previous_terms()
                term = term and term[0] or None
        if term:
            objs = objs.filter(
                school_year=term.school_year,
                term_type=term.term_type
            )
            cond['school_year'] = term.school_year
            cond['term_type'] = term.term_type
            return objs, cond
        else:
            logger.debug('There is no available term in the database.')
            return models.Statistic.objects.none(), {'pk': -1}
