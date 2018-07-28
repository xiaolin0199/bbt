# coding=utf-8
from django.core.cache import cache
from django.db import transaction
from BanBanTong.db import models
from BanBanTong.db import utils as db_utils
from BanBanTong.forms.lesson_name import LessonNameForm
from BanBanTong.forms.lesson_name import LessonNameUploadForm
from BanBanTong.forms.lesson_name import LessonNameUploadVerifyForm
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import get_page_info
from BanBanTong.utils import model_list_to_dict
from BanBanTong.utils import model_to_dict


def list_current(request, *args, **kwargs):
    school_uuid = request.GET.get('school_uuid')
    donot_pagination = request.GET.get('donot_pagination', False)
    q = models.LessonName.objects.filter(deleted=False)
    if school_uuid:
        q = q.filter(school__uuid=school_uuid)
    if models.Setting.getvalue('server_type') == 'school':
        q = q.values('uuid', 'name', 'types')
    else:
        q = q.order_by().values('name').distinct()

    order_lst = [
        u'',
        u'小学',
        u'小学,初中',
        u'小学,高中',
        u'小学,初中,高中',
        u'初中',
        u'初中,高中',
        u'高中',
    ]
    if len(q):
        q = list(q)
        q.sort(key=lambda d: len(d['name']))
        q.sort(key=lambda d: d.has_key('types') and d['types'] in order_lst and order_lst.index(d['types']) or -1)

    if donot_pagination == 'true':
        return create_success_dict(data={
            'records': model_list_to_dict(q),
            'page': 1,
            'page_size': len(q),
            'record_count': len(q),
            'page_count': 1,
        })

    page_info = get_page_info(request)
    page_data = db_utils.pagination(q, **page_info)

    return create_success_dict(data={
        'records': model_list_to_dict(page_data['records']),
        'page': page_data['page_num'],
        'page_size': page_data['page_size'],
        'record_count': page_data['record_count'],
        'page_count': page_data['page_count'],
    })


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_lesson_name')
@transaction.atomic
def add(request, *args, **kwargs):
    if request.method == 'POST':
        lesson_name_form = LessonNameForm(request.POST)
        if lesson_name_form.is_valid():
            obj = lesson_name_form.save()
            return create_success_dict(msg='添加课程成功！',
                                       data=model_to_dict(obj))

        return create_failure_dict(msg='添加课程失败！',
                                   errors=lesson_name_form.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_lesson_name')
def delete(request, *args, **kwargs):
    if request.method == 'POST':
        if not cache.get('sudo'):
            return create_failure_dict(msg='请输入正确的超级管理员admin密码！')
        uuid = request.POST.get('uuid')
        if uuid:
            try:
                l = models.LessonName.objects.get(uuid=uuid)
            except:
                return create_failure_dict(msg='错误的uuid！')
            if l.lessonschedule_set.count() > 0:
                return create_failure_dict(msg='课程表安排了该课程，无法删除')
            if l.lessonteacher_set.count() > 0:
                return create_failure_dict(msg='该课程有上课老师，无法删除')
            l.deleted = True
            l.save()
            return create_success_dict(msg='删除课程成功！')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_lesson_name')
def import_from(request, *args, **kwargs):
    if request.method == 'POST':
        f = LessonNameUploadForm(request.POST, request.FILES)
        if f.is_valid():
            lesson_names = f.save()
            return create_success_dict(data=model_list_to_dict(lesson_names))

        return create_failure_dict(msg='导入学校开课课程失败！',
                                   errors=f.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_lesson_name')
def verify(request, *args, **kwargs):
    if request.method == 'POST':
        f = LessonNameUploadVerifyForm(request.POST, request.FILES)
        if f.is_valid():
            objs = f.save()
            return create_success_dict(data=model_list_to_dict(objs))

        return create_failure_dict(msg='验证学校开课课程失败！',
                                   errors=f.errors)

# MH:return current_school_class list


def list_current_class(request, *args, **kwargs):
    page_info = get_page_info(request)
    school_uuid = request.GET.get('school_uuid')

    q = models.LessonName.objects.filter(deleted=False)
    if school_uuid:
        q = q.filter(school__uuid=school_uuid)
    # MH:filter if class is selected
    # MH:return q.filter if lesson_name is exist
    try:
        class_uuid = request.GET.get('class_uuid')
        if class_uuid:
            c = models.LessonSchedule.objects.filter(deleted=False)
            lesson_name = c.filter(class_uuid=class_uuid).values('lesson_name_uuid')
            if lesson_name:
                q = q.filter(lesson_name__uuid__in=lesson_name)
    except:
        pass
    if models.Setting.getvalue('server_type') == 'school':
        #q = q.values('uuid', 'name')
        q = q.values('uuid', 'name', 'types')
    else:
        q = q.order_by().values('name').distinct()
    page_data = db_utils.pagination(q, **page_info)

    return create_success_dict(data={
        'records': model_list_to_dict(page_data['records']),
        'page': page_data['page_num'],
        'page_size': page_data['page_size'],
        'record_count': page_data['record_count'],
        'page_count': page_data['page_count'],
    })
