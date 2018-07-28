# coding=utf-8
from django.db.models import Sum
from BanBanTong.db.models import Setting, Group, GroupTB, NewTerm
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import paginatoooor

from edu_point import models


@decorator.authorized_user_with_redirect
def get_node_trees(request, *args, **kwargs):
    """系统设置>教学点>节点树,用于条件联动"""
    __f = lambda name: Setting.getvalue(name)
    node_type = request.GET.get('node_type', None)
    province_name = request.GET.get('province_name', __f('province'))
    city_name = request.GET.get('city_name', __f('city'))
    country_name = request.GET.get('country_name', __f('country'))
    town_name = request.GET.get('town_name', None)
    point_name = request.GET.get('point_name', None)
    school_year = request.GET.get('school_year', None)
    term_type = request.GET.get('term_type', None)
    status = request.GET.get('status', None)
    ori = request.GET.get('ori', None)  # 数据源: GroupTB or 实际存在的数据

    type_index = ('province', 'city', 'country', 'town', 'unit', 'room')

    # 下面的用于限定父级参数不完整的时候不返回子级的信息
    for i in type_index[3:]:
        if node_type == i:
            break
        name = request.GET.get('%s_name' % (i != 'unit' and i or 'point'), None)
        if not name:
            return create_success_dict(data={'records': []})

    o = models.EduPoint.objects.all()
    if province_name and type_index.index(node_type) > 0:
        o = o.filter(province_name=province_name)
    if city_name and type_index.index(node_type) > 1:
        o = o.filter(city_name=city_name)
    if country_name and type_index.index(node_type) > 2:
        o = o.filter(country_name=country_name)
    if town_name and type_index.index(node_type) > 3:
        o = o.filter(town_name=town_name)
    if point_name and type_index.index(node_type) > 4:
        o = o.filter(point_name=point_name)

    if status == u'已申报':
        o = o.exclude(edupointdetail__cpuID='')
    elif status == u'未申报':
        o = o.filter(edupointdetail__cpuID='')

    if school_year or term_type:
        if school_year:
            o = o.filter(school_year=school_year)
        if term_type:
            o = o.filter(term_type=term_type)
    else:
        # if not school_year and not term_type: # by default
        term = NewTerm.get_current_or_next_term()
        if not term:
            return create_failure_dict(msg=u'无可用学年学期')
        o = o.filter(school_year=term.school_year)
        o = o.filter(term_type=term.term_type)

    o = o.order_by('province_name', 'city_name', 'country_name',
                   'town_name', 'point_name', 'create_time')
    lst = []
    # We have 7 level:
    # province, city, country, town, school/unit, grade, class/room
    # Part I: province city country town -- form GroupTB
    # Part II: school grade class -- from Group Grade and Class
    # Part III: unit room -- from EduPoint and EduPointDetail

    # node_type will be asigned to server_type if it is null
    if not node_type:
        server_type = Setting.getvalue('server_type')
        if server_type == 'country':
            node_type = 'town'
        elif server_type == 'school':
            node_type = 'school'
        else:
            return create_failure_dict()

    index_lst_1 = ('province', 'city', 'country', 'town')

    # Part I
    if node_type in index_lst_1:
        if ori == 'unit':
            lst = list(set(o.values_list('%s_name' % node_type, flat=True)))
        else:
            g = GroupTB.objects.all()
            if index_lst_1.index(node_type) > 0:  # city
                g = g.get(name=province_name)
            if index_lst_1.index(node_type) > 1:  # country
                g = g.child_set.get(name=city_name)
            if index_lst_1.index(node_type) > 2:  # town
                g = g.child_set.get(name=country_name)
            # if index_lst_1.index(node_type) > 3: # school
            #     g = g.child_set.get(name=town_name)
            # if index_lst_1.index(node_type) > 4: # grade
            #     g = g.child_set.get(name=school_name)
            # if index_lst_1.index(node_type) > 5: # class
            #     g = g.child_set.get(name=grade_name)

            if node_type == 'province':  # province
                lst = g.filter(parent__isnull=True).values_list('name', flat=True)
            else:
                lst = g.child_set.values_list('name', flat=True)

    # Part II
    elif node_type == 'school':
        g2 = Group.objects.all().filter(group_type=node_type)
        lst = list(set(g2.values_list('name', flat=True)))

    # Part III
    elif node_type == 'unit':
        # if not (school_year and term_type):
        #     return create_failure_dict(msg='#both school_year and term_type \
        #         needed in this node_type')
        lst = o.values_list('point_name', flat=True)
    elif node_type == 'room':
        # if not (school_year and term_type and town_name and point_name):
        #     return create_failure_dict(msg='#school_year and term_type and \
        #         town_name and point_name are needed in this node_type')
        if o.exists():
            room = o[0].edupointdetail_set.filter(type='room')
            lst = list(set(room.values_list('name', flat=True)))
        else:
            lst = []
    else:
        lst = ['node_type should in province city country \
                town school unit and room']
    return create_success_dict(data={'records': map(lambda i: {'key': i}, lst)})


def _query(request, node_type):
    lst = ('province', 'city', 'country', 'town', 'school', 'unit', 'room')
    f = lambda x, y: lst.index(x) <= lst.index(y) and Setting.getvalue(x) or None
    d = {  # 前端将后台返回的 conditions 解析了,这里重组一下
        'province_name': request.GET.get('province_name', f('province', node_type)),
        'city_name': request.GET.get('city_name', f('city', node_type)),
        'country_name': request.GET.get('country_name', f('country', node_type)),
        'town_name': request.GET.get('town_name', None),
        'point_name': request.GET.get('point_name', None),
        'room_name': request.GET.get('room_name', None),
        'parent_key': request.GET.get('parent_key', '_init')
    }
    school_year = request.GET.get('school_year', None)
    term_type = request.GET.get('term_type', None)
    parent = request.GET.get('parent', None)
    d[d['parent_key']] = parent
    if d['parent_key'] != '_init' and d.has_key('_init'):
        del d['_init']
    o = models.EduPoint.objects.all()
    pic = models.EduPointDetailDesktopViewLog.objects.all()

    if d['province_name'] and lst.index(node_type) > 0:
        o = o.filter(province_name=d['province_name'])
        pic = pic.filter(province_name=d['province_name'])
    if d['city_name'] and lst.index(node_type) > 1:
        o = o.filter(city_name=d['city_name'])
        pic = pic.filter(city_name=d['city_name'])
    if d['country_name'] and lst.index(node_type) > 2:
        o = o.filter(country_name=d['country_name'])
        pic = pic.filter(country_name=d['country_name'])
    if d['town_name'] and lst.index(node_type) > 3:
        o = o.filter(town_name=d['town_name'])
        pic = pic.filter(town_name=d['town_name'])
    if d['point_name'] and lst.index(node_type) > 4:
        o = o.filter(point_name=d['point_name'])
        pic = pic.filter(point_name=d['point_name'])
    if d['room_name'] and lst.index(node_type) > 5:
        o = o.filter(number=d['room_name'])
        pic = pic.filter(number=d['room_name'])

    if school_year or term_type:
        if school_year:
            o = o.filter(school_year=school_year)
            pic = pic.filter(school_year=school_year)
        if term_type:
            o = o.filter(term_type=term_type)
            pic = pic.filter(term_type=term_type)
    else:
        # if not school_year and not term_type:
        t = NewTerm.get_current_term()
        if not t:
            return create_failure_dict(msg='学年学期获取失败')
        o = o.filter(school_year=t.school_year, term_type=t.term_type)
        pic = pic.filter(school_year=t.school_year, term_type=t.term_type)
    o = o.order_by('province_name', 'city_name', 'town_name', 'point_name')
    return o, pic, d


@decorator.authorized_user_with_redirect
def screenshot_node_info(request, *args, **kwargs):
    """教师授课>教学点桌面使用日志>节点信息获取"""
    f = lambda x: x == 'country' and 'town' or x
    server_type = Setting.getvalue('server_type')
    root_name = Setting.getvalue(server_type)
    if server_type == 'school':
        return create_failure_dict(msg=u'错误的服务器级别.')
    node_type = request.GET.get('node_type', f(server_type))

    o, pic, conditions = _query(request, node_type)
    q = models.EduPointDetail.objects.none()
    for i in o:
        q |= i.edupointdetail_set.filter(type='room')

    for i in ('province', 'city', 'country', 'town', 'unit', 'room'):
        if node_type == i:
            break
        name = '%s_name' % (i != 'unit' and i or 'point')
        if not conditions[name]:
            return create_failure_dict(msg=u'父级参数不完整(%s)' % name)
    for i in conditions.keys():
        if not conditions[i]:
            del conditions[i]

    ret = []
    if node_type == 'province':
        provinces = list(set(o.values_list('province_name', flat=True)))
        for province_name in provinces:
            oo = o.filter(province_name=province_name)
            # qq = q.filter(edupoint__province_name=province_name)
            pp = pic.filter(edupoint__province_name=province_name)
            ret.append({
                'parent_name': province_name,
                'node_type': 'province',
                'child_type': 'city',
                'unit_count': oo.count(),
                'room_count': oo.aggregate(n=Sum('number'))['n'],
                'pic_count': pp.count(),
            })
        conditions['parent_key'] = 'province_name'
    elif node_type == 'city':
        citys = list(set(o.values_list('city_name', flat=True)))
        for city_name in citys:
            oo = o.filter(city_name=city_name)
            # qq = q.filter(edupoint__city_name=city_name)
            pp = pic.filter(edupoint__city_name=city_name)
            ret.append({
                'parent_name': city_name,
                'node_type': 'city',
                'child_type': 'country',
                'unit_count': oo.count(),
                'room_count': oo.aggregate(n=Sum('number'))['n'],
                'pic_count': pp.count(),
            })
        conditions['parent_key'] = 'city_name'
    elif node_type == 'country':
        countrys = list(set(o.values_list('country_name', flat=True)))
        for country_name in countrys:
            oo = o.filter(country_name=country_name)
            # qq = q.filter(edupoint__country_name=country_name)
            pp = pic.filter(edupoint__country_name=country_name)
            ret.append({
                'parent_name': country_name,
                'node_type': 'country',
                'child_type': 'town',
                'unit_count': oo.count(),
                'room_count': oo.aggregate(n=Sum('number'))['n'],
                'pic_count': pp.count(),
            })
        conditions['parent_key'] = 'country_name'
    elif node_type == 'town':
        towns = list(set(o.values_list('town_name', flat=True)))
        for town_name in towns:
            oo = o.filter(town_name=town_name)
            # qq = q.filter(edupoint__town_name=town_name)
            pp = pic.filter(edupoint__town_name=town_name)
            ret.append({
                'parent_name': town_name,
                'node_type': 'town',
                'child_type': 'unit',
                'unit_count': oo.count(),
                'room_count': oo.aggregate(n=Sum('number'))['n'],
                'pic_count': pp.count(),
            })
        conditions['parent_key'] = 'town_name'
    elif node_type == 'unit':
        points = list(set(o.values_list('point_name', flat=True)))
        for point_name in points:
            oo = o.filter(point_name=point_name)
            # qq = q.filter(edupoint__point_name=point_name)
            pp = pic.filter(edupoint__point_name=point_name)
            ret.append({
                'parent_name': point_name,
                'node_type': 'unit',
                'child_type': 'room',
                'unit_count': oo.count(),
                'room_count': oo.aggregate(n=Sum('number'))['n'],
                'pic_count': pp.count(),
            })
        conditions['parent_key'] = 'point_name'
    elif node_type == 'room':
        ret = map(lambda i: {
            'parent_name': i.name,
            'node_type': 'room',
            'child_type': 'none',
            'unit_count': 1,
            'room_count': 1,
            'point_id': i.edupoint.pk,
            'room_id': i.pk,
            'pic_count': pic.filter(edupointdetail=i).count(),
        }, q)
        conditions['parent_key'] = 'room_name'
    return paginatoooor(request, ret, conditions=conditions, root_name=root_name)
