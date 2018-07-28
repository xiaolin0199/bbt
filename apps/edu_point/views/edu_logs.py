# coding=utf-8
import datetime

from django.db.models import Sum
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date

from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import paginatoooor
from BanBanTong.utils import get_page_info
from BanBanTong.utils import model_list_to_dict

from edu_point import models
from edu_point.views.index import screenshot_node_info


# 教学点桌面使用日志
@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('activity_edu_unit_preview')
def screenshot_node(request, *args, **kwargs):
    """教师授课>教学点桌面使用日志>节点信息"""
    return screenshot_node_info(request, *args, **kwargs)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('activity_edu_unit_preview')
def screenshot_timeline(request, *args, **kwargs):
    """教师授课>教学点桌面使用日志>时间线"""
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)
    point_id = request.GET.get('point_id', None)
    room_id = request.GET.get('room_id', None)

    pic = models.EduPointDetailDesktopViewLog.objects.all()
    if start_date and end_date and point_id and room_id:
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)
        ret = {}
        n = (end_date - start_date).days + 1
        for t in range(n):
            created_at = start_date + datetime.timedelta(t)
            s = datetime.datetime.combine(created_at, datetime.time.min)
            e = datetime.datetime.combine(created_at, datetime.time.max)
            p = pic.filter(edupoint=point_id,
                           edupointdetail=room_id,
                           create_time__range=(s, e))
            ret[str(created_at)] = p.count()

        return create_success_dict(data=ret)

    return create_failure_dict(msg='获取参数失败！', tips='These args are needed: start_date, end_date, point_id and room_id')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('activity_edu_unit_preview')
def screenshot_data(request, *args, **kwargs):
    """教师授课>教学点桌面使用日志>数据"""
    point_id = request.GET.get('point_id', None)
    room_id = request.GET.get('room_id', None)
    date = request.GET.get('date', None)
    if date and point_id and room_id:
        date = parse_date(date)
        s = datetime.datetime.combine(date, datetime.time.min)
        e = datetime.datetime.combine(date, datetime.time.max)
        pic = models.EduPointDetailDesktopViewLog.objects
        pic = pic.filter(edupoint=point_id, edupointdetail=room_id)
        pic = pic.filter(create_time__range=(s, e)).order_by('date')
        ret = []
        if pic.exists():
            ret = map(lambda i: {
                'point_name': i.point_name,
                'number': i.number,
                'created_at': i.create_time,
                'host': i.host,
                'url': i.pic,
            }, pic)
        return create_success_dict(data={'records': ret})
    return create_failure_dict(msg='获取参数失败')


# 教学点终端使用日志
def _query(request, *args, **kwargs):
    town_name = request.GET.get('town_name', None)
    point_name = request.GET.get('point_name', None)
    number = request.GET.get('number', None)
    school_year = request.GET.get('school_year', None)
    term_type = request.GET.get('term_type', None)
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)

    o = models.EduPointMachineTimeUsed.objects.all()
    if town_name:
        o = o.filter(town_name=town_name)
    if point_name:
        o = o.filter(point_name=point_name)
    if number:
        o = o.filter(number=number)
    if start_date and end_date:
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)
        s = datetime.datetime.combine(start_date, datetime.time.min)
        e = datetime.datetime.combine(end_date, datetime.time.max)
        o = o.filter(create_time__range=(s, e))
    else:
        if school_year:
            o = o.filter(school_year=school_year)
        if term_type:
            o = o.filter(term_type=term_type)

    use_time_total = o.aggregate(total=Sum('use_time'))['total']
    boot_time_total = o.aggregate(total=Sum('boot_time'))['total']

    if not use_time_total:
        use_time_total = 0
    if not boot_time_total:
        boot_time_total = 0

    total = {
        'use_time': use_time_total,
        'boot_time': boot_time_total,
        'to_class_time': '{0:.2f}'.format(use_time_total / 45.0)
    }
    o = o.order_by('-create_time', 'school_year', 'term_type',
                   'country_name', 'town_name', 'point_name', 'number')
    return o, total


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('edu_unit_logged_in')
def terminal_use(request, *args, **kwargs):
    """教师授课>教学点终端使用日志"""
    o, total = _query(request)
    ret = []
    if o.exists():
        ret = map(lambda i: {
            'town_name': i.town_name,
            'point_name': i.point_name,
            'number': i.number,
            'use_time': i.use_time,
            'boot_time': i.boot_time,
            'date': i.create_time,
            'to_class_time': '{0:.2f}'.format(i.use_time / 45.0),
        }, o)
    return paginatoooor(request, ret, total=total)


# 终端开机日志>教学点
def _query2(request):
    """根据条件获取出基础数据"""
    # school_year = request.GET.get('school_year', None)
    # term_type = request.GET.get('term_type', None)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    town_name = request.GET.get('town_name')
    point_name = request.GET.get('point_name')
    room_number = request.GET.get('number')

    o = models.EduPointMachineTimeUsed.objects.all()
    #p = models.EduPointDetail.objects.filter(type='room')
    if town_name:
        o = o.filter(edupoint__town_name=town_name)
        #p = p.filter(edupoint__town_name=town_name)
    if point_name:
        o = o.filter(edupoint__point_name=point_name)
        #p = p.filter(edupoint__point_name=point_name)

    if room_number:
        o = o.filter(number=room_number)
        #p = p.filter(name=room_number)

    if start_date and end_date:
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)
        s = datetime.datetime.combine(start_date, datetime.time.min)
        e = datetime.datetime.combine(end_date, datetime.time.max)
        o = o.filter(create_time__range=(s, e))
        #p = p.filter(edupoint__create_time__range=(s, e))
        # days = (e - s).days

    boot_time_total = o.aggregate(total=Sum('boot_time'))['total']
    if not boot_time_total:
        boot_time_total = 0
    boot_count_total = o.aggregate(total=Sum('boot_count'))['total']
    if not boot_count_total:
        boot_count_total = 0
    total = {
        #'use_time_total': boot_time_total,
        #'use_count_total': boot_count_total,
        'boot_time_total': boot_time_total,
        'boot_count_total': boot_count_total
    }
    return o, total


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('machine_time_used_log')
def terminal_boot(request, *args, **kwargs):
    """教师授课>教学点终端开机日志"""
    ret = []
    o, total = _query2(request)
    if o.exists():
        for i in o:
            ret.append({'town_name': i.town_name,
                        'point_name': i.point_name,
                        'number': i.number,
                        'create_time': datetime.datetime.strftime(i.create_time, '%Y-%m-%d'),
                        #'use_time': i.use_time,
                        'boot_time': i.boot_time,
                        #'use_count': i.use_count
                        'boot_count': i.boot_count
                        })
    return paginatoooor(request, ret, total=total)


# 卫星资源接收日志
@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('resource_satellite_log')
def resource_store(request, *args, **kwargs):
    """资源使用>卫星资源接收日志"""
    school_year = request.GET.get('school_year')
    term_type = request.GET.get('term_type')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    town_name = request.GET.get('town_name')
    point_name = request.GET.get('point_name')

    q = models.EduPointResourceReceLog.objects.all().order_by('-rece_time')
    if school_year:
        q = q.filter(school_year=school_year)
    if term_type:
        q = q.filter(term_type=term_type)
    if town_name:
        q = q.filter(town_name=town_name)
    if point_name:
        q = q.filter(point_name=point_name)

    if start_date and end_date:
        # 按自然日期查询
        s = parse_date(start_date)
        e = parse_date(end_date)
        s = datetime.datetime.combine(s, datetime.time.min)
        e = datetime.datetime.combine(e, datetime.time.max)
        q = q.filter(rece_time__range=(s, e))

    page_info = get_page_info(request)

    total_resource_size = q.aggregate(total=Sum('rece_size')).get('total', 0)

    total_resource_count = q.aggregate(total=Sum('rece_count')).get('total', 0)

    q = q.values('id', 'school_year', 'term_type', 'town_name', 'point_name', 'rece_time', 'rece_count', 'rece_size', 'rece_type').distinct()

    # 添加一个uuid,与id是一样的
    map(lambda x: x.setdefault('uuid', x['id']), q)

    paginator = Paginator(q, page_info['page_size'])
    records = paginator.page(page_info['page_num']).object_list

    # 每条卫星接收日志的详细信息是一起返回
    for record in records:
        obj = models.EduPointResourceReceLog.objects.get(id=record['uuid'])
        details = obj.edupointresourcerecelogdetail_set.all()
        d_len = details.count()

        # 资源文件详细
        details = details.values('type', 'size', 'count')
        # 按资源文件最多排序, 相同数量比较大小
        details = sorted(details, key=lambda x: (x['count'], x['size']), reverse=True)

        # 每个种类的详细情况
        if d_len <= 5:
            record['details'] = details
        else:
            record['details'] = details[:5]
            # 余下的全部整个'其他'
            other_type_count = reduce(lambda x, y: x + y, map(lambda x: x['count'], details[5:]))
            other_type_size = reduce(lambda x, y: x + y, map(lambda x: x['size'], details[5:]))

            record['details'].append({'type': u'其他', 'count': other_type_count, 'size': other_type_size})

    ret = create_success_dict(data={
        'page': page_info['page_num'],
        'page_count': paginator.num_pages,
        'page_size': page_info['page_size'],
        'record_count': paginator.count,
        'records': model_list_to_dict(records),
        'total_resource_size': total_resource_size,
        'total_resource_count': total_resource_count,
    })

    return ret
