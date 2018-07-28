# coding=utf-8
import upyun
from BanBanTong.db import models
from BanBanTong.utils import cloud_service
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import model_list_to_dict


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_desktop_preview')
def get(request, *args, **kwargs):
    if models.Setting.getvalue('server_type') != 'country':
        return create_failure_dict(msg='错误的服务器级别')
    if request.method == 'GET':
        names = ['desktop-preview-interval', 'desktop-preview-days-to-keep',
                 'cloud-service-provider', 'cloud-service-username',
                 'cloud-service-password',
                 'desktop-preview-interval-edu-unit', 'desktop-preview-days-to-keep-edu-unit',
                 'cloud-service-provider-edu-unit', 'cloud-service-username-edu-unit',
                 'cloud-service-password-edu-unit'
                 ]
        q = models.Setting.objects.filter(name__in=names).values()
        return create_success_dict(data={'records': model_list_to_dict(q)})


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_desktop_preview')
def set(request, *args, **kwargs):
    if models.Setting.getvalue('server_type') != 'country':
        return create_failure_dict(msg='错误的服务器级别')
    if request.method == 'POST':
        func = models.Setting.objects.get_or_create

        interval = request.POST.get('desktop-preview-interval', None)
        days = request.POST.get('desktop-preview-days-to-keep', None)
        sp = request.POST.get('cloud-service-provider', None)
        username = request.POST.get('cloud-service-username', None)
        password = request.POST.get('cloud-service-password', None)
        if interval:
            obj, c = func(name='desktop-preview-interval')
            obj.value = interval
            obj.save()
        if days:
            obj, c = func(name='desktop-preview-days-to-keep')
            obj.value = days
            obj.save()
        if sp:
            obj, c = func(name='cloud-service-provider')
            obj.value = sp
            obj.save()
        if username:
            obj, c = func(name='cloud-service-username')
            obj.value = username
            obj.save()
        if password:
            obj, c = func(name='cloud-service-password')
            obj.value = password
            obj.save()

        interval4edu = request.POST.get('desktop-preview-interval-edu-unit', 10)
        days4edu = request.POST.get('desktop-preview-days-to-keep-edu-unit', days)
        sp4edu = request.POST.get('cloud-service-provider-edu-unit', sp)
        username4edu = request.POST.get('cloud-service-username-edu-unit', username)
        password4edu = request.POST.get('cloud-service-password-edu-unit', password)
        if interval4edu:
            obj, c = func(name='desktop-preview-interval-edu-unit')
            obj.value = interval4edu
            obj.save()
        if days4edu:
            obj, c = func(name='desktop-preview-days-to-keep-edu-unit')
            obj.value = days4edu
            obj.save()
        if sp4edu:
            obj, c = func(name='cloud-service-provider-edu-unit')
            obj.value = sp4edu
            obj.save()
        if username4edu:
            obj, c = func(name='cloud-service-username-edu-unit')
            obj.value = username4edu
            obj.save()
        if password4edu:
            obj, c = func(name='cloud-service-password-edu-unit')
            obj.value = password4edu
            obj.save()
        return create_success_dict(msg='桌面预览设置成功')


def _verify_upyun(username, password):
    bucket = cloud_service.generate_bucket_name()
    up = upyun.UpYun(bucket, username, password)
    try:
        up.usage()
    except upyun.UpYunServiceException, e:
        if e.status == 401:
            msg = u'服务器设定的行政区域尚未获得云存储服务授权,请联系服务厂商解决该问题.'
            return create_failure_dict(msg=msg, debug=str(e))
        msg = '验证错误：%s' % str(e)
        # e: (request_id, status, msg, err)
        return create_failure_dict(msg=msg)
    except upyun.UpYunClientException, e:
        msg = '操作错误；%s' % str(e)
        return create_failure_dict(msg=msg)
    except Exception as e:
        msg = '系统错误：%s' % str(e)
        return create_failure_dict(msg=msg)
    return create_success_dict(msg='验证成功')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_desktop_preview')
def verify(request, *args, **kwargs):
    if models.Setting.getvalue('server_type') != 'country':
        return create_failure_dict(msg='错误的服务器级别')
    if request.method == 'POST':
        sp = request.POST.get('cloud-service-provider')
        username = request.POST.get('cloud-service-username')
        password = request.POST.get('cloud-service-password')
        if sp == 'upyun':
            func = _verify_upyun
        else:
            return create_failure_dict(msg='暂不支持云存储服务商%s' % sp)
        return func(username, password)
