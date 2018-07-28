# coding=utf-8
import datetime
from django.core.cache import cache
from BanBanTong.db import models
from BanBanTong.db import utils as db_utils
from BanBanTong.forms.term import TermForm
from BanBanTong.forms.term import TermUploadForm
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import get_page_info
from BanBanTong.utils import model_list_to_dict
from BanBanTong.utils import model_to_dict


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_term')
def add(request, *args, **kwargs):
    if request.method == 'POST':
        record = TermForm(request.POST)
        if record.is_valid():
            term = record.save(commit=False)
            school = models.Group.objects.get(group_type='school')
            term.school = school
            term.save()
            return create_success_dict(msg='添加学期成功！',
                                       data=model_to_dict(term))

        return create_failure_dict(msg='添加学期失败！',
                                   errors=record.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_term')
def delete(request, *args, **kwargs):
    if request.method == 'POST':
        uuid = request.POST.get('uuid')
        if uuid:
            term = models.Term.objects.get(uuid=uuid)
            term.deleted = True
            term.save()
            return create_success_dict(msg='删除学期成功！')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_term')
def edit(request, *args, **kwargs):
    if request.method == 'POST':
        try:
            uu = request.POST.get('uuid')
            obj = models.Term.objects.get(uuid=uu)
            record_form = TermForm(request.POST, instance=obj)
            if record_form.is_valid():
                term = record_form.save()
                return create_success_dict(msg='编辑学期成功！',
                                           data=model_to_dict(term))

            return create_failure_dict(msg='编辑学期失败！',
                                       errors=record_form.errors)
        except:
            return create_failure_dict(msg='错误的uuid！')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_term')
def finish(request, *args, **kwargs):
    if request.method == 'POST':
        if not cache.get('sudo'):
            return create_failure_dict(msg='请输入正确的超级管理员admin密码！')
        uu = request.POST.get('uuid')
        try:
            term = models.Term.objects.get(uuid=uu)
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
#@decorator.authorized_privilege('system_term')
def get_current_term(request):
    server_type = models.Setting.getvalue('server_type')
    if server_type == 'country':
        today = datetime.date.today()
        q = models.NewTerm.objects.filter(start_date__lte=today, end_date__gte=today)
        if q.count() == 0:
            q = models.NewTerm.objects.filter(start_date__gte=today)
    else:
        q = models.Term.get_current_term_list()
    try:
        t = q[0]
        # 当前时间没有落与任何学年学期内的时候,会给出一个提示(middleware触发的)
        # 这里影响到前端给后台的传值没有学年学期和时间范围,然后触发提示
        today = datetime.datetime.now().date()
        if not (t.start_date <= today <= t.end_date):
            return create_failure_dict()
    except:
        return create_failure_dict(msg='没有可用的学期')
    data = {'school_year': t.school_year, 'term_type': t.term_type}
    return create_success_dict(data=data)


def get_current_or_next_term(request):
    server_type = models.Setting.getvalue('server_type')
    if server_type != 'school':
        term = models.NewTerm.get_current_or_next_term()

    else:
        term = models.Term.get_current_term_list()
        if term:
            term = term[0]

    data = {'school_year': '', 'term_type': ''}
    if not term:
        return create_failure_dict(msg='没有可用的学年学期')
    if term:
        data = {'school_year': term.school_year, 'term_type': term.term_type}
    return create_success_dict(data=data)


def get_nearest_term(request):
    term = models.NewTerm.get_nearest_term()
    data = {'school_year': '', 'term_type': ''}
    if not term:
        return create_failure_dict(msg='没有可用的学年学期')
    if term:
        data = {'school_year': term.school_year, 'term_type': term.term_type}
    return create_success_dict(data=data)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_term')
def import_from(request, *args, **kwargs):
    if request.method == 'POST':
        f = TermUploadForm(request.POST, request.FILES)
        if f.is_valid():
            terms = f.save()
            return create_success_dict(data=model_list_to_dict(terms))

        return create_failure_dict(msg='导入学年学期失败！',
                                   errors=f.errors)


@decorator.authorized_user_with_redirect
#@decorator.authorized_privilege('system_term')
def list_current(request, *args, **kwargs):
    page_info = get_page_info(request)
    q = models.Term.objects.all()
    q = q.order_by('-end_date')
    q = q.values('uuid', 'school_year', 'term_type',
                 'start_date', 'end_date', 'deleted')
    page_data = db_utils.pagination(q, **page_info)

    return create_success_dict(data={
        'records': model_list_to_dict(page_data['records']),
        'page': page_data['page_num'],
        'page_size': page_data['page_size'],
        'record_count': page_data['record_count'],
        'page_count': page_data['page_count']
    })


@decorator.authorized_user_with_redirect
def list_school_year(request, *args, **kwargs):
    q = models.Term.objects.order_by().values('school_year').distinct()
    return create_success_dict(data={'records': model_list_to_dict(q)})


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_term')
def verify(request, *args, **kwargs):
    if request.method == 'POST':
        f = TermUploadForm(request.POST, request.FILES)
        if f.is_valid():
            ret = f.verify()
            return create_success_dict(data={'records': ret})
        return create_failure_dict(msg='校验学年学期失败！',
                                   errors=f.errors)
