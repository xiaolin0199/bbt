# coding=utf-8
import datetime
from django.core.paginator import Paginator, EmptyPage
from django.utils.dateparse import parse_date
from BanBanTong.db import models
from BanBanTong.utils import decorator
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import paginatoooor
from BanBanTong.utils import get_page_info


def _get_school_class_count(city_country, school_year, term_type, cc=False):
    """选中地市州或区县市时，显示该辖区的总学校数和班级数"""
    towns = models.Group.objects.filter(parent=city_country)
    ret = []
    for t in towns:
        school_base = models.Group.objects.filter(group_type='school')
        if city_country.group_type == 'city':
            schools = school_base.filter(parent__parent=t)
        else:  # group_type == 'country'
            schools = school_base.filter(parent=t)

        classes = models.Class.objects.filter(grade__term__school__in=schools,
                                              grade__term__school_year=school_year,
                                              grade__term__term_type=term_type,
                                              grade__number__lt=13)

        if cc:
            classes = classes.filter(grade__number=13)
        ret.append({'name': t.name,
                    'uuid': t.uuid,
                    'group_type': t.group_type,
                    'school_count': schools.count(),
                    'class_count': classes.count()})

    return ret


def _get_class_count(town, school_year, term_type, cc=False):
    """选中乡镇街道时，显示该辖区的学校信息,班级数目"""
    schools = models.Group.objects.filter(parent=town)
    ret = []
    for s in schools:
        classes = models.Class.objects.filter(grade__term__school=s,
                                              grade__term__school_year=school_year,
                                              grade__term__term_type=term_type,
                                              grade__number__lt=13)
        if cc:
            classes = classes.filter(grade__number=13)
        ret.append({'name': s.name,
                    'uuid': s.uuid,
                    'group_type': 'school',
                    'class_count': classes.count()})

    return ret


def _get_pic_count(school, school_year, term_type, cc=False):
    """选中学校时，显示每个班级以及该班级的桌面预览数"""
    # 由于云端存储以及流量等的限制,需要设定一个存储服务提供的期限,默认为150天
    # 考虑到跨学年学期情况的存在,这里通过对学年学期的时间段与距离当前日期最近
    # 150天取交集,返回的时间段即为实际提供的桌面预览
    #
    # 2014-11-05
    # 加入电脑教室桌面使用日志的相关代码,直接在这里过滤class
    try:
        timedelta = int(models.Setting.getvalue('desktop-preview-days-to-keep'))
    except Exception as e:
        timedelta = 150
    timedelta = datetime.timedelta(timedelta + 1)
    today = datetime.datetime.now().date()
    try:
        term = models.Term.objects.get(school=school,
                                       school_year=school_year,
                                       term_type=term_type)
    except Exception as e:
        return []
    start_date1 = today - timedelta
    start_date2 = term.start_date
    start_date = max(start_date1, start_date2)
    end_date = term.end_date

    # print '\n\ndebuginfo--begin:'
    # print 'timedelta:',timedelta
    # print 'start_date:', '150start:', start_date1,'term_start:', start_date2,
    # print '-->', start_date
    # print 'end_date:', end_date
    # print 'debuginfo--end\n\n'
    s = datetime.datetime.combine(start_date, datetime.time.min)
    e = datetime.datetime.combine(end_date, datetime.time.max)
    classes = models.Class.objects.filter(grade__term__school=school,
                                          grade__term__school_year=school_year,
                                          grade__term__term_type=term_type)
    if cc:
        classes = classes.filter(grade__number=13)
    else:
        classes = classes.exclude(grade__number=13)
    classes = classes.values('uuid', 'name', 'grade__name')
    classes = classes.order_by('grade__number', 'number').distinct()

    return classes, s, e


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('activity_desktop_preview')
def get_pics_count_by_date(request, *args, **kwargs):
    """班班通桌面使用日志，用于返回请求的日期时间轴的每日桌面预览信息"""
    # ValidateDateRangeMiddleware 中简单忽略掉了对时间跨学年学期的判断
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)
    class_uuid = request.GET.get('class_uuid', None)
    lesson_period_sequence = request.GET.get('lesson_period_sequence', None)

    if start_date and end_date and class_uuid:
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)
        ret = {}
        n = (end_date - start_date).days + 1
        for t in range(n):
            created_at = start_date + datetime.timedelta(t)
            s = datetime.datetime.combine(created_at, datetime.time.min)
            e = datetime.datetime.combine(created_at, datetime.time.max)
            pic = models.DesktopPicInfo.objects.filter(class_uuid=class_uuid,
                                                       created_at__range=(s, e))
            if lesson_period_sequence:
                pic = pic.filter(lesson_period_sequence=lesson_period_sequence)
            ret[str(created_at)] = pic.count()

        return create_success_dict(data=ret)

    return create_failure_dict(msg='获取参数失败！')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('activity_desktop_preview')
def get_node_info(request, *args, **kwargs):
    """班班通桌面使用日志，用于返回请求的节点辖区的信息"""
    school_year = request.GET.get('school_year', None)
    term_type = request.GET.get('term_type', None)
    lesson_period_sequence = request.GET.get('lesson_period_sequence', None)
    uu = request.GET.get('uuid', None)
    server_type = models.Setting.getvalue('server_type')
    root_name = models.Setting.getvalue(server_type)

    if uu:
        try:
            node = models.Group.objects.get(uuid=uu)
        except:
            return create_failure_dict(msg='错误的UUID')

    else:
        server_type = models.Setting.getvalue('server_type')
        node = models.Group.objects.get(group_type=server_type)

    if school_year and term_type and node:
        if node.group_type in ['city', 'country']:
            info = _get_school_class_count(node, school_year, term_type)

        elif node.group_type == 'town':
            info = _get_class_count(node, school_year, term_type)

        elif node.group_type == 'school':
            # 学校详细时，先分页，一页6个统计
            # q 所有班级(已排序) s开始时间 e结束时间
            q, s, e = _get_pic_count(node, school_year, term_type)
            # 分页处理
            page_info = get_page_info(request)
            paginator = Paginator(q, 6)  # 一页6个
            try:
                records = list(paginator.page(page_info['page_num']).object_list)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                records = list(paginator.page(paginator.num_pages).object_list)
            # 每一个班级的详细数据
            r = []
            for c in records:
                class_uuid = c['uuid']
                class_name = c['grade__name'] + u'年级' + c['name'] + u'班'
                pic = models.DesktopPicInfo.objects.filter(class_uuid=class_uuid)
                pic = pic.filter(created_at__range=(s, e))

                if lesson_period_sequence:
                    pic = pic.filter(lesson_period_sequence=lesson_period_sequence)
                r.append({'uuid': class_uuid,
                          'name': class_name,
                          'group_type': 'class',
                          'pic_count': pic.count()})

            return create_success_dict(data={
                'page': page_info['page_num'],
                'page_count': paginator.num_pages,
                'page_size': page_info['page_size'],
                'record_count': paginator.count,
                'records': r,
            })
        else:
            return create_failure_dict(msg='错误的节点类型')

        return paginatoooor(request, info, root_name=root_name)

    return create_failure_dict(msg='获取参数失败！')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('activity_desktop_preview')
def get_pics_info_by_date(request, *args, **kwargs):
    """班班通桌面使用日志，用于返回请求日期的图片信息"""
    date = request.GET.get('date', None)
    class_uuid = request.GET.get('class_uuid', None)
    lesson_period_sequence = request.GET.get('lesson_period_sequence', None)

    if date and class_uuid:
        date = parse_date(date)
        s = datetime.datetime.combine(date, datetime.time.min)
        e = datetime.datetime.combine(date, datetime.time.max)
        pic = models.DesktopPicInfo.objects.filter(class_uuid__uuid=class_uuid)
        pic = pic.filter(created_at__range=(s, e))
        if lesson_period_sequence:
            pic = pic.filter(lesson_period_sequence=lesson_period_sequence)
        pic = pic.values('grade__name',
                         'class_uuid__name',
                         'lesson_name',
                         'teacher_name',
                         'lesson_period_sequence',
                         'created_at',
                         'host',
                         'url').order_by('created_at')

        q = []
        for i in pic:
            d = {}
            d['grade_name'] = i['grade__name']
            d['class_name'] = i['class_uuid__name']
            d['lesson_name'] = i['lesson_name']
            d['teacher_name'] = i['teacher_name']
            d['lesson_period_sequence'] = i['lesson_period_sequence']
            d['created_at'] = i['created_at']
            d['host'] = i['host']
            d['url'] = i['url']
            q.append(d)
        return create_success_dict(data={'records': q})
    return create_failure_dict(msg='获取参数失败！')
