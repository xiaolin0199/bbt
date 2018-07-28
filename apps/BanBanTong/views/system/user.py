# coding=utf-8
import logging
import traceback
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import transaction
from BanBanTong.db import models
from BanBanTong.forms.user import UserForm
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import get_page_info
from BanBanTong.utils import is_admin
from BanBanTong.utils import model_list_to_dict
from BanBanTong.utils import model_to_dict

logger = logging.getLogger(__name__)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_user')
@transaction.atomic
def add(request, *args, **kwargs):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        permitted_groups = request.POST.get('permitted_groups').split(',')
        if user_form.is_valid():
            user = user_form.save()

            for group_uuid in permitted_groups:
                try:
                    group = models.Group.objects.get(uuid=group_uuid)
                    record = models.UserPermittedGroup(user=user, group=group)
                    record.save()
                except:
                    pass
            data = model_to_dict(user)
            if 'role' in data:
                if 'name' in data['role']:
                    data['role__name'] = data['role']['name']
            return create_success_dict(msg='添加用户成功！',
                                       data=data)

        return create_failure_dict(msg='添加用户失败！',
                                   errors=user_form.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_user')
def delete(request, *args, **kwargs):
    if request.method == 'POST':
        uu = request.POST.get('uuid')
        record = models.User.objects.get(uuid=uu)
        if not is_admin(record):
            if request.current_user.username == record.username:
                return create_failure_dict(msg='当前登录用户无法删除！')
            models.UserPermittedGroup.objects.filter(user=record).delete()
            record.delete()
            return create_success_dict(msg='删除用户成功！')

        else:
            return create_failure_dict(msg='超级管理员不允许删除！')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_user')
def detail(request):
    if request.method == 'GET':
        try:
            uu = request.GET.get('uuid')
            u = models.User.objects.filter(uuid=uu)[0]
            p = models.UserPermittedGroup.objects.filter(user=u)
            p = p.values('uuid', 'group__uuid', 'group__name')
            data = {'user': model_to_dict(u),
                    'permitted_groups': model_list_to_dict(p)}
            return create_success_dict(data=data)
        except:
            return create_failure_dict(msg='错误的uuid！')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_user')
@transaction.atomic
def edit(request, *args, **kwargs):
    if request.method == 'POST':
        try:
            uu = request.POST.get('uuid')
            user = models.User.objects.get(uuid=uu)
            if is_admin(user):
                role = request.POST.get('role', None)
                status = request.POST.get('status', None)
                if role:
                    return create_failure_dict(msg='不允许修改超级管理员用户的角色')

                if status == 'suspended':
                    return create_failure_dict(msg='超级管理员用户不可停用')
            user_form = UserForm(request.POST, instance=user)
            groups = request.POST.get('permitted_groups').split(',')

            if user_form.is_valid():
                u = user_form.save()
                u.userpermittedgroup_set.all().delete()
                for i in groups:
                    try:
                        g = models.Group.objects.get(uuid=i)
                        user = models.UserPermittedGroup(user=u, group=g)
                        user.save()
                    except:
                        pass
                k = 'permitted-groups-%s' % uu
                cache.delete(k)
                k = 'group-%s' % uu
                cache.delete(k)
                data = model_to_dict(u)
                if data['role']:
                    data['role__name'] = u.role.name
                return create_success_dict(msg='编辑用户成功！', data=data)

            return create_failure_dict(msg='编辑用户失败！', errors=user_form.errors)
        except:
            traceback.print_exc()
            return create_failure_dict(msg='错误的uuid！')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_user')
def list_current(request, *args, **kwargs):
    page_info = get_page_info(request)
    user = request.current_user

    q = models.User.objects.all()
    if user.username != 'oseasy':
        q = q.exclude(username='oseasy')
    q = q.order_by('username')
    q = q.values('uuid', 'username', 'role__name', 'realname', 'sex',
                 'qq', 'mobile', 'email', 'status', 'remark')
    paginator = Paginator(q, page_info['page_size'])
    records = list(paginator.page(page_info['page_num']).object_list)

    return create_success_dict(data={
        'page': page_info['page_num'],
        'page_count': paginator.num_pages,
        'page_size': page_info['page_size'],
        'record_count': paginator.count,
        'records': records,
    })
