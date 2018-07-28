# coding=utf-8
import logging
from django.core.cache import cache
from edu_point import models
from BanBanTong.db.models import Setting, NewTerm
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import paginatoooor
from BanBanTong.utils.str_util import generate_node_key as _generate_key


logger = logging.getLogger(__name__)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_node')
def _query(request):
    school_year = request.GET.get('school_year', None)
    term_type = request.GET.get('term_type', None)
    town_name = request.GET.get('town_name', None)
    point_name = request.GET.get('point_name', None)
    key = request.GET.get('key', None)
    status = request.GET.get('status', None)
    type = 'receiver' in request.path and 'moon' or 'room'

    o = models.EduPointDetail.objects.filter(type=type)
    if school_year or term_type:
        if school_year:
            o = o.filter(edupoint__school_year=school_year)
        if term_type:
            o = o.filter(edupoint__term_type=term_type)
    else:
        term = NewTerm.get_current_or_next_term()
        if term:
            o = o.filter(
                edupoint__school_year=term.school_year,
                edupoint__term_type=term.term_type
            )
        else:
            o = models.EduPointDetail.objects.none()
    if town_name:
        o = o.filter(edupoint__town_name=town_name)
    if point_name:
        o = o.filter(edupoint__point_name=point_name)

    if key:
        o = o.filter(communicate_key__contains=key.upper())
    if status == u'已申报':
        o = o.exclude(cpuID='')
    elif status == u'未申报':
        o = o.filter(cpuID='')
    o = o.order_by('edupoint__town_name', 'edupoint__point_name', 'pk')

    o = o.values('edupoint__school_year', 'edupoint__term_type',
                 'edupoint__town_name', 'communicate_key', 'edupoint__point_name',

                 'pk', 'cpuID', 'last_active_time', 'last_upload_time', 'name')

    return o

# 系统设置>服务器汇聚管理>教学点


def leest(request, *args, **kwargs):
    """系统设置>服务器管理>教学点教室终端管理>列表显示"""
    server_type = Setting.getvalue('server_type')
    if server_type != 'country':
        return create_failure_dict(msg='错误的服务器级别')

    o = list(_query(request))
    ret = map(lambda i: {
        'uuid': i['pk'],
        'school_year': i['edupoint__school_year'],
        'term_type': i['edupoint__term_type'],
        'town_name': i['edupoint__town_name'],
        'point_name': i['edupoint__point_name'],
        'key': i['communicate_key'],
        'status': i['cpuID'] and i['cpuID'] and '已申报' or '未申报',
        'number': i['name'],
        'last_active_time': i['last_active_time'],
        'last_upload_time': i['last_upload_time'],
    }, o)
    return paginatoooor(request, ret)


def unbind(request, *args, **kwargs):
    """系统设置>服务器管理>教学点教室终端管理>清除绑定"""
    server_type = Setting.getvalue('server_type')
    if server_type != 'country':
        return create_failure_dict(msg=u'错误的服务器级别')
    uuid = request.POST.get('uuid', None)
    if not uuid:
        return create_failure_dict(msg=u'获取节点失败')
    if not cache.get('sudo'):
        return create_failure_dict(msg=u'请输入正确的超级管理员admin密码！')
    try:
        o = models.EduPointDetail.objects.get(id=uuid)
        o.cpuID = ''
        o.communicate_key = _generate_key()
        o.save()
        return create_success_dict(msg=u'清除绑定成功')
    except:
        return create_failure_dict(msg=u'错误的UUID')


def inherit_items(request, *args, **kwargs):
    school_year = request.GET.get('school_year')
    term_type = request.GET.get('term_type')
    pre_school_year = request.GET.get('pre_school_year')
    pre_term_type = request.GET.get('pre_term_type')

    server_type = Setting.getvalue('server_type')
    if server_type != 'country':
        # print 'Wrong server_type'
        return create_failure_dict(msg=u'错误的服务器级别', debug=server_type)

    if school_year and term_type:
        try:
            term = NewTerm.objects.get(
                school_year=school_year,
                term_type=term_type
            )
        except Exception as e:
            return create_failure_dict(msg=u'无可用学年学期', debug=str(e))
    else:
        term = NewTerm.get_current_or_next_term()

    if not term:
        print 'There is no term available in the database'
        return create_failure_dict(msg=u'当前时间/未来时间不存在可用学年学期')
    print 'current term', term.school_year, term.term_type

    if school_year and term_type:
        try:
            pre_term = NewTerm.objects.get(
                school_year=pre_school_year,
                term_type=pre_term_type
            )
        except Exception as e:
            return create_failure_dict(msg=u'无可用历史学年学期', debug=str(e))
    else:
        pre_term = NewTerm.get_previous_term(term=term)

    if not pre_term:
        print 'There is no pre_term'
        return create_failure_dict(msg='无可用历史学年学期')
    print 'pre_term', pre_term.school_year, pre_term.term_type

    objs1 = models.EduPoint.objects.filter(
        school_year=pre_term.school_year,
        term_type=pre_term.term_type
    )

    for o in objs1:
        point, is_new = models.EduPoint.objects.get_or_create(
            school_year=term.school_year,
            term_type=term.term_type,
            province_name=o.province_name,
            city_name=o.city_name,
            country_name=o.country_name,
            town_name=o.town_name,
            point_name=o.point_name,
            number=o.number,
            remark=o.remark
        )
        if is_new:
            print 'create one edupoint item:', point.point_name

        objs = o.edupointdetail_set.all()
        if is_new:
            print 'child_set count:', objs.count()
        for oo in objs:
            models.EduPointDetail.objects.get_or_create(
                edupoint=point,
                type=oo.type,
                name=oo.name,
                communicate_key=_generate_key()
            )

        return create_success_dict(msg=u'操作成功')
