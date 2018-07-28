# coding=utf-8
import datetime
from django.db.models import Sum
from django.utils.dateparse import parse_date
from BanBanTong.db import models
from edu_point import models as e_models
from activation.utils import create_failure_dict


def has_activate(*args, **kwargs):
    """验证（县/校）是否激活,并返回授权状态及信息

    para1: is_active (是否激活) True or False
    para2: active_status (授权状态) on(激活) off(未激活) overtime(超出授权时间) waittime(未到授权时间) overnumber(授权点数已全部使用)
    para3: info (授权详细信息) {'quota': xx, 'start_date': xxx, 'end_date': xxx, 'days': xxx}
    """
    d = models.Setting.getval('activation')
    if d and d.has_key('start_date') and d.has_key('end_date'):
        d.update(get_use_activate_with_detail())
        try:
            start_date = parse_date(d['start_date'])
        except Exception as e:
            return False, 'off', {'msg': str(e)}
        try:
            end_date = parse_date(d['end_date'])
        except ValueError:
            pass
        except Exception as e:
            return False, 'off', {'msg': str(e)}
        today = datetime.datetime.now().date()
        quota = d.get('quota', 0)
        if today < start_date:
            return True, 'waittime', d
        elif not d['end_date'].startswith('0000-00-00') and today > end_date:
            return True, 'overtime', d
        else:  # start_date <= today <= end_date
            use = get_use_activate()
            if use > quota:
                return True, 'overnumber', d

        return True, 'on', d

    return False, 'off', {}


def get_use_activate_with_detail(*args, **kwargs):
    """获取（县/校）已使用的授权数 (已用)

    校级:
        班级总数 + 电脑教室总数
    县级:
        学校总数 + 教学点教室总数或卫星接收终端数取最大值
    """
    server_type = models.Setting.getvalue('server_type')
    if server_type == 'school':
        terms = models.Term.get_current_term_list()
        objs = models.Class.objects.filter(grade__term__in=terms)
        c = objs.exclude(grade__number=13).count()
        t = objs.filter(grade__number=13).count()
        return {'class_count': c, 'class_computer_count': t}

    elif server_type == 'country':
        # 学校占用的授权点数，县级的可用就是看所有学校的分配及教学点的教室总和
        s = models.Node.objects.all().aggregate(x=Sum('activation_number'))['x']
        # 教学点占用的授权点数
        term = models.NewTerm.get_current_or_next_term()
        if term:
            e = e_models.EduPoint.objects.filter(
                school_year=term.school_year,
                term_type=term.term_type
            ).aggregate(x=Sum('number'))['x']
        else:
            e = 0
        s = s and s or 0
        e = e and e or 0
        return {'school_count': s, 'edu_point_count': e}

    return {}


def get_use_activate(*args, **kwargs):
    """获取（县/校）已使用的授权数 (已用)"""
    obj = get_use_activate_with_detail()
    if obj:
        return sum(obj.values())

    return 0


def get_none_activate(*args, **kwargs):
    """获取（县/校）的可使用授权数 (可用)"""
    # 授权点数
    is_active, active_status, info = has_activate()
    quota = info.get('quota', 0)
    # 已用点数
    use = get_use_activate()
    return quota - use


def activation_required(func):
    """对于一些简单的需要权限验证的功能,直接用decorator包裹一下

    1. 未激活，无可用
    2. 超过授权日期，无可用
    3. 超过或等于授权数量，无可用
    is_active: True or False 是否激活
    active_status: 0() or 1 or -1
    """
    def _inner(request, *args, **kwargs):
        is_active, active_status, info = has_activate()
        if not is_active:
            return create_failure_dict(
                is_active=is_active,
                active_status=active_status,
                msg=u'未激活，无可用授权数据'
            )
        else:
            if active_status == 'waittime':
                return create_failure_dict(
                    is_active=is_active,
                    active_status=active_status,
                    msg=u'授权时间还未到，请核对您的授权开始时间'
                )
            elif active_status == 'overtime':
                return create_failure_dict(
                    is_active=is_active,
                    active_status=active_status,
                    msg=u'授权时间已过，请重新授权更新后使用'
                )
            elif active_status == 'overnumber':
                return create_failure_dict(
                    is_active=is_active,
                    active_status=active_status,
                    msg=u'授权点数已全部使用, 如有需要，请联系上级服务器管理员'
                )

        # 查看是否刚好全用完
        available_number = get_none_activate()
        if available_number == 0:
            return create_failure_dict(
                is_active=True,
                active_status='zeronumber',
                msg=u'授权点数已全部使用, 如有需要，请联系上级服务器管理员'
            )

        return func(request, *args, **kwargs)

    return _inner
