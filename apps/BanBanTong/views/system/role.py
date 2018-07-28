# coding=utf-8
from django.db import transaction

from BanBanTong.db import models
from BanBanTong.utils import decorator
from BanBanTong.utils import model_to_dict
from BanBanTong.utils import model_list_to_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import create_failure_dict
from BanBanTong.forms.role import RoleForm
from BanBanTong.utils import paginatoooor


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_role')
@transaction.atomic
def add(request, *args, **kwargs):
    if request.method == 'POST':
        role_form = RoleForm(request.POST)
        privileges = request.POST.get('privileges').split(',')
        if role_form.is_valid():
            role = role_form.save()

            for p in privileges:
                record = models.RolePrivilege(role=role, privilege=p)
                record.save()

            return create_success_dict(msg='添加角色成功！',
                                       data=model_to_dict(role))

        return create_failure_dict(msg='添加角色失败！',
                                   errors=role_form.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_role')
def delete(request, *args, **kwargs):
    if request.method == 'POST':
        uu = request.POST.get('uuid')
        if uu:
            try:
                role = models.Role.objects.get(uuid=uu)
            except:
                return create_failure_dict(msg='错误的uuid！')
            if role.user_set.exists():
                return create_failure_dict(msg='有用户属于该角色，不能删除！')
            role.roleprivilege_set.all().delete()
            role.delete()
            return create_success_dict(msg='删除角色成功！')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_role')
def detail(request, *args, **kwargs):
    if request.method == 'GET':
        try:
            uu = request.GET.get('uuid')
            obj = models.Role.objects.get(uuid=uu)
            rp = models.RolePrivilege.objects.filter(role=obj)
            rp = rp.values('uuid', 'privilege')
            data = {'role': {'uuid': obj.uuid, 'name': obj.name,
                             'remark': obj.remark},
                    'privilege': model_list_to_dict(rp)}

            return create_success_dict(data=data)
        except:
            return create_failure_dict(msg='错误的uuid！')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_role')
@transaction.atomic
def edit(request, *args, **kwargs):
    if request.method == 'POST':
        uu = request.POST.get('uuid')
        record = models.Role.objects.get(uuid=uu)
        role_form = RoleForm(request.POST, instance=record)
        privileges = request.POST.get('privileges').split(',')

        if role_form.is_valid():
            role = role_form.save()
            role.roleprivilege_set.all().delete()
            for p in privileges:
                record = models.RolePrivilege(role=role, privilege=p)
                record.save()

            return create_success_dict(msg='编辑角色成功！',
                                       data=model_to_dict(role))

        return create_failure_dict(msg='编辑角色失败！',
                                   errors=role_form.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_role')
def list_current(request, *args, **kwargs):
    if request.method == 'GET':
        q = models.Role.objects.all()
        q = q.values('uuid', 'name', 'remark')

        return paginatoooor(request, q)
