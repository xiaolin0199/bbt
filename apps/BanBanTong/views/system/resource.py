# coding=utf-8
from BanBanTong.db import models
from BanBanTong.forms import resource
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import paginatoooor


@decorator.authorized_user_with_redirect
#@decorator.authorized_privilege('system_resource')
def resource_from(request):
    q = models.ResourceFrom.objects.all()
    if models.Setting.getvalue('server_type') == 'school':
        q = q.values()
    else:
        q = q.values('uuid', 'value', 'remark').distinct()
    return paginatoooor(request, q)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_resource')
def resource_from_add(request):
    if request.method == 'POST':
        f = resource.ResourceFromForm(request.POST)
        if f.is_valid():
            f.save()
            return create_success_dict(msg='添加资源来源成功')
        return create_failure_dict(msg='添加资源来源失败', errors=f.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_resource')
def resource_from_delete(request):
    if request.method == 'POST':
        uu = request.POST.get('uuid')
        if uu:
            try:
                obj = models.ResourceFrom.objects.get(uuid=uu)
                obj.delete()
                return create_success_dict(msg='删除资源来源成功')
            except:
                return create_failure_dict(msg='错误的uuid')
        return create_failure_dict(msg='uuid不能为空')


@decorator.authorized_user_with_redirect
#@decorator.authorized_privilege('system_resource')
def resource_type(request):
    q = models.ResourceType.objects.all()
    if models.Setting.getvalue('server_type') == 'school':
        q = q.values()
    else:
        q = q.values('uuid', 'value', 'remark').distinct()
    return paginatoooor(request, q)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_resource')
def resource_type_add(request):
    if request.method == 'POST':
        f = resource.ResourceTypeForm(request.POST)
        if f.is_valid():
            f.save()
            return create_success_dict(msg='添加资源类型成功')
        return create_failure_dict(msg='添加资源类型失败', errors=f.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_resource')
def resource_type_delete(request):
    if request.method == 'POST':
        uu = request.POST.get('uuid')
        if uu:
            try:
                obj = models.ResourceType.objects.get(uuid=uu)
                obj.delete()
                return create_success_dict(msg='删除资源类型成功')
            except:
                return create_failure_dict(msg='错误的uuid')
        return create_failure_dict(msg='uuid不能为空')
