# coding=utf-8
import copy
import cPickle
import datetime
import json
import logging
from django.core.cache import cache
from django.http.response import HttpResponse
from django.http.response import HttpResponseRedirect
from django.template import loader
from BanBanTong import settings_privileges
from BanBanTong.db import models
from BanBanTong.forms import authority as authority_forms
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import get_all_privilege_keys
from BanBanTong.utils import is_admin
from BanBanTong.utils import model_to_dict
from BanBanTong.utils import model_list_to_dict
from BanBanTong.utils import session
from BanBanTong.utils import simplecache
from BanBanTong.utils.get_cache_timeout import get_timeout
from BanBanTong.utils.datetimeutil import get_term_from_date_range

logger = logging.getLogger(__name__)


def index(request, *args, **kwargs):
    if models.Setting.getvalue('installed') != 'True':
        return HttpResponseRedirect('/install/')
    template = loader.get_template('index.html')
    server_type = models.Setting.getvalue('server_type')
    server_name = models.Setting.getvalue(server_type)
    html_title = models.Setting.getvalue('html_title')
    context = {
        'title': html_title or u'噢易班班通管理分析系统',
        'server_type': server_type,
        'server_name': server_name,
        'query': request.GET
    }
    response = HttpResponse(template.render(context))
    try:
        o = models.Setting.objects.get(name='show_download_btn')
        show_download_btn = str(o.value).lower()
    except Exception:
        show_download_btn = 'true'
    if server_type == 'school':
        show_download_btn = 'true'
    response.set_cookie("show_download_btn", show_download_btn)
    return response


@decorator.authorized_user_with_redirect
def classes(request, *args, **kwargs):
    school_uuid = request.GET.get('school')
    computerclass_need = request.GET.get('computerclass_need', False)
    only_computerclass = request.GET.get('only_computerclass', False)
    school_year = request.GET.get('school_year', None)
    term_type = request.GET.get('term_type', None)
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)

    if school_uuid:
        school = models.Group.objects.get(uuid=school_uuid, group_type='school')
    else:
        school = models.Group.objects.filter(group_type='school')
    if school_year and term_type and school:
        terms = models.Term.objects.filter(
            school_year=school_year,
            term_type=term_type,
            school=school
        )
    elif start_date and end_date:
        t = get_term_from_date_range(request)
        if isinstance(t, (models.Term, models.NewTerm)):
            terms = [t, ]
        else:
            terms = models.Term.objects.none()
    else:
        terms = models.Term.get_current_term_list(school)
    q = models.Class.objects.filter(grade__term__in=terms)
    if only_computerclass == 'true':  # 仅需要电脑教室的联动信息
        q = q.filter(grade__number=13)
    elif computerclass_need != 'true':  # 仅需要普通年级班级的联动信息
        q = q.exclude(grade__number=13)
    q = q.order_by().values('name', 'grade__name').distinct()

    return create_success_dict(data=model_list_to_dict(q))


@decorator.authorized_user_with_redirect
def classes1(request, *args, **kwargs):
    computerclass_need = request.GET.get('computerclass_need', False)
    only_computerclass = request.GET.get('only_computerclass', False)
    school_year = request.GET.get('school_year', None)
    term_type = request.GET.get('term_type', None)
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)
    no_cache = request.GET.get('no_cache', False)
    c = cache.get('classes')
    if c and not no_cache:
        data = json.loads(c)
    elif start_date and end_date:
        t = get_term_from_date_range(request)
        if isinstance(t, (models.Term, models.NewTerm)):
            terms = [t, ]
        else:
            terms = models.Term.objects.none()
    else:
        school_uuid = request.GET.get('school')
        if school_uuid:
            school = models.Group.objects.get(uuid=school_uuid,
                                              group_type='school')
        else:
            school = models.Group.objects.filter(group_type='school')
        if school_year and term_type and school:
            terms = models.Term.objects.filter(
                school_year=school_year,
                term_type=term_type,
                school=school
            )
        else:
            terms = models.Term.get_current_term_list(school)
        q = models.Class.objects.filter(grade__term__in=terms)
        if only_computerclass == 'true':  # 仅需要电脑教室的联动信息
            q = q.filter(grade__number=13)
        elif computerclass_need != 'true':  # 仅需要普通年级班级的联动信息
            q = q.exclude(grade__number=13)
        q = q.order_by().values('name', 'grade__name').distinct()
        data = model_list_to_dict(q)
        cache.set('classes', json.dumps(data), get_timeout('classes', None))

    return create_success_dict(data=data)


@decorator.authorized_user_with_redirect
def details(request, *args, **kwargs):
    timelog = []
    timelog.append({'start': str(datetime.datetime.now())})
    curruser = model_to_dict(request.current_user)
    timelog.append({'1': str(datetime.datetime.now())})
    k = 'permitted-groups-%s' % curruser['uuid']
    v = cache.get(k)
    if v:
        curruser['permitted_groups'] = cPickle.loads(v)
    else:
        q = models.Group.objects.filter(userpermittedgroup__user=curruser['uuid'])
        curruser['permitted_groups'] = model_list_to_dict(q)
        v = cPickle.dumps(curruser['permitted_groups'], cPickle.HIGHEST_PROTOCOL)
        cache.set(k, v, get_timeout(k, None))
    timelog.append({'3': str(datetime.datetime.now())})
    curruser['role_name'] = ''
    curruser['privileges'] = []
    curruser['superuser'] = False
    timelog.append({'4': str(datetime.datetime.now())})

    if is_admin(request.current_user):
        curruser['role_name'] = '超级管理员'
        curruser['superuser'] = True
        timelog.append({'5-11': str(datetime.datetime.now())})
        server_type = models.Setting.getvalue('server_type')
        timelog.append({'5-12': str(datetime.datetime.now())})

        if server_type not in settings_privileges.PRIVILEGES:
            privileges = copy.deepcopy(settings_privileges.PRIVILEGES['school'])
        else:
            privileges = copy.deepcopy(settings_privileges.PRIVILEGES[server_type])
        timelog.append({'5-13': str(datetime.datetime.now())})
        curruser['privileges'] = get_all_privilege_keys(privileges)
        timelog.append({'5-14': str(datetime.datetime.now())})
    else:
        if request.current_user.role:
            curruser['role_name'] = request.current_user.role.name
            timelog.append({'5-21': str(datetime.datetime.now())})
            rp = request.current_user.role.roleprivilege_set.all()
            timelog.append({'5-22': str(datetime.datetime.now())})
            curruser['privileges'] = [i.privilege for i in rp]
            timelog.append({'5-23': str(datetime.datetime.now())})

    timelog.append({'end': str(datetime.datetime.now())})
    return create_success_dict(data=curruser, timelog=timelog)


@decorator.authorized_user_with_redirect
def group(request, *args, **kwargs):
    data = simplecache.Group.get(request.current_user)
    return create_success_dict(data=data)


def login(request, *args, **kwargs):
    if request.method == 'POST':
        f = authority_forms.UserLoginForm(request.POST)
        f.set_request(request)
        if f.is_valid():
            logged_user = f.save()
            session.save_user(request, logged_user)
            return create_success_dict(msg='用户登录成功！')

        return create_failure_dict(msg='用户登录失败！',
                                   errors=f.errors)


@decorator.authorized_user
def logout(request, *args, **kwargs):
    session.clear_user(request)
    return create_success_dict(msg='用户退出成功！')


@decorator.authorized_user_with_redirect
def privileges(request, *args, **kwargs):
    server_type = models.Setting.getvalue('server_type')
    if server_type not in settings_privileges.PRIVILEGES:
        privileges = settings_privileges.PRIVILEGES['school']
    else:
        privileges = settings_privileges.PRIVILEGES[server_type]

    ret = []
    if is_admin(request.current_user):
        ret = privileges
    else:
        try:
            ps = request.current_user.role.roleprivilege_set.all()
            u = [i.privilege for i in ps]
        except:
            return create_failure_dict(msg='该用户未设置角色！')
        for i in privileges:
            d = {}
            d = {'key': i['key'], 'name': i['name'], 'privileges': []}
            d['privileges'] = [j for j in i['privileges'] if j['key'] in u]
            if len(d['privileges']) > 0:
                ret.append(d)
    return create_success_dict(data=ret)


@decorator.authorized_user_with_redirect
def server_info(request, *args, **kwargs):
    _server_info = {}

    _server_info['asset_statuses'] = []
    for key, text in models.ASSET_STATUS:
        _server_info['asset_statuses'].append({'key': key, 'text': text})

    _server_info['resource_types'] = []
    for key, text in models.RESOURCE_TYPES:
        _server_info['resource_types'].append({'key': key, 'text': text})

    _server_info['user_statuses'] = []
    for key, text in models.USER_STATUS:
        _server_info['user_statuses'].append({'key': key, 'text': text})

    _server_info['user_levels'] = []
    for key, text in models.USER_LEVELS:
        _server_info['user_levels'].append({'key': key, 'text': text})

    return create_success_dict(data=_server_info)


def version(request, *args, **kwargs):
    return create_success_dict(version='704',
                               date='2014050513')
