# coding=utf-8

from activation.utils import create_success_dict
from activation.decorator import has_activate, get_use_activate, get_none_activate
from activation.decorator import get_use_activate_with_detail


def api_has_activate(request):
    '''
        api接口 has_activate,验证当前的软件是否激活,并返回授权信息
    '''
    is_active, active_status, info = has_activate()
    if info.has_key('end_date') and info['end_date'].startswith('0000-00-00'):
        info['end_date'] = u'无限期'
    return create_success_dict(data={
        'is_active': is_active,
        'active_status': active_status,
        'info': info
    })


def api_get_use_activate(request):
    '''
        api接口 get_use_activate,获取服务端已使用的授权数 (已用)
    '''
    use_number = get_use_activate()
    return create_success_dict(data={'use_number': use_number})


def api_get_use_activate_with_detail(request):
    '''
        api接口 get_use_activate_with_detail,获取服务端已使用的授权数 (已用)
    '''
    use_number_dict = get_use_activate_with_detail()
    return create_success_dict(data={'use_number_dict': use_number_dict})


def api_get_none_activate(request):
    '''
        api接口 get_none_activate,获取服务端未使用的授权数 (未用)
    '''
    none_number = get_none_activate()
    return create_success_dict(data={'none_number': none_number})
