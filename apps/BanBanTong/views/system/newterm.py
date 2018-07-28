# coding=utf-8
import datetime
from django.core.cache import cache
from BanBanTong.db import models
from BanBanTong.db import utils as db_utils
from BanBanTong.forms.newterm import NewTermForm
from BanBanTong.forms.newterm import NewTermUploadForm
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import get_page_info
from BanBanTong.utils import model_list_to_dict
from BanBanTong.utils import model_to_dict
from activation.decorator import activation_required


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_newterm')
@activation_required
def add(request, *args, **kwargs):
    if request.method == 'POST':
        record = NewTermForm(request.POST)
        if record.is_valid():
            term = record.save(commit=False)
            country = models.Group.objects.get(group_type='country')
            term.country = country
            term.save()
            return create_success_dict(msg='添加学期成功！',
                                       data=model_to_dict(term))

        return create_failure_dict(msg='添加学期失败！',
                                   errors=record.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_newterm')
def delete(request, *args, **kwargs):
    if request.method == 'POST':
        uuid = request.POST.get('uuid')
        if uuid:
            term = models.NewTerm.objects.get(uuid=uuid)
            term.deleted = True
            term.save()
            return create_success_dict(msg='删除学期成功！')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_newterm')
def edit(request, *args, **kwargs):
    if request.method == 'POST':
        try:
            uu = request.POST.get('uuid')
            obj = models.NewTerm.objects.get(uuid=uu)
            record_form = NewTermForm(request.POST, instance=obj)
            if record_form.is_valid():
                term = record_form.save()
                return create_success_dict(msg='编辑学期成功！',
                                           data=model_to_dict(term))

            return create_failure_dict(msg='编辑学期失败！',
                                       errors=record_form.errors)
        except:
            return create_failure_dict(msg='错误的uuid！')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_newterm')
def import_from(request, *args, **kwargs):
    if request.method == 'POST':
        f = NewTermUploadForm(request.POST, request.FILES)
        if f.is_valid():
            terms = f.save()
            return create_success_dict(data=model_list_to_dict(terms))

        return create_failure_dict(msg='导入学年学期失败！',
                                   errors=f.errors)


@decorator.authorized_user_with_redirect
#@decorator.authorized_privilege('system_newterm')
def list_current(request, *args, **kwargs):
    page_info = get_page_info(request)
    q = models.NewTerm.objects.all()
    q = q.order_by('-end_date')
    q = q.values()
    page_data = db_utils.pagination(q, **page_info)

    return create_success_dict(data={
        'records': model_list_to_dict(page_data['records']),
        'page': page_data['page_num'],
        'page_size': page_data['page_size'],
        'record_count': page_data['record_count'],
        'page_count': page_data['page_count']
    })


@decorator.authorized_user_with_redirect
def list_current_or_next(request, *args, **kwargs):
    o = models.NewTerm.get_current_or_next_term()
    if not o:
        o = {}
    return create_success_dict(data=model_to_dict(o))


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_newterm')
def finish(request, *args, **kwargs):
    if request.method == 'POST':
        if not cache.get('sudo'):
            return create_failure_dict(msg='请输入正确的超级管理员admin密码！')
        uu = request.POST.get('uuid')
        try:
            term = models.NewTerm.objects.get(uuid=uu)
        except:
            return create_failure_dict(msg='错误的uuid！')
        if term.deleted:
            return create_success_dict(msg='此学期已经结转过！')
        now = datetime.datetime.now()
        if term.end_date >= now.date():
            return create_failure_dict(msg='该学期还未结束，不能执行结转操作！')
        term.deleted = True
        term.save()
        return create_success_dict(msg='学期结转成功！')


@decorator.authorized_user_with_redirect
def list_school_year(request, *args, **kwargs):
    q = models.NewTerm.objects.order_by().values('school_year').distinct()
    return create_success_dict(data={'records': model_list_to_dict(q)})


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_newterm')
def verify(request, *args, **kwargs):
    if request.method == 'POST':
        f = NewTermUploadForm(request.POST, request.FILES)
        if f.is_valid():
            ret = f.verify()
            return create_success_dict(data={'records': ret})
        return create_failure_dict(msg='校验学年学期失败！',
                                   errors=f.errors)
