# coding=utf-8
from django.core.cache import cache
from django.db import transaction
from BanBanTong.db import models
from BanBanTong.db import utils as db_utils
from BanBanTong.forms.new_lesson_name import NewLessonNameForm
from BanBanTong.forms.new_lesson_name import NewLessonNameUploadForm
from BanBanTong.forms.new_lesson_name import NewLessonNameUploadVerifyForm
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import get_page_info
from BanBanTong.utils import model_list_to_dict
from BanBanTong.utils import model_to_dict


def list_current(request, *args, **kwargs):
    page_info = get_page_info(request)
    q = models.NewLessonName.objects.filter(deleted=False)
    order_lst = [
        [],
        [u'小学'],
        [u'小学', u'初中'],
        [u'小学', u'高中'],
        [u'小学', u'初中', u'高中'],
        [u'初中'],
        [u'初中', u'高中'],
        [u'高中'],
    ]

    q = [{'uuid': b.uuid, 'name': b.name, 'types': [a.name for a in b.lesson_type.all()]} for b in q]
    q.sort(key=lambda i: len(i['name']))
    q.sort(key=lambda i: i['types'] in order_lst and order_lst.index(i['types']) or -1)

    page_data = db_utils.pagination(q, **page_info)

    return create_success_dict(data={
        'page': page_data['page_num'],
        'page_size': page_data['page_size'],
        'record_count': page_data['record_count'],
        'page_count': page_data['page_count'],
        'records': model_list_to_dict(page_data['records']),
    })


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_new_lesson_name')  # settings中已经更新
@transaction.atomic
def add(request, *args, **kwargs):
    if request.method == 'POST':
        try:
            models.NewLessonName.objects.get(name=request.POST['name'], deleted=False)
            return create_failure_dict(msg='已存在该课程')
        except:
            pass

        new_lesson_name_form = NewLessonNameForm(request.POST)
        if new_lesson_name_form.is_valid():
            obj = new_lesson_name_form.save()
            types = request.POST.getlist('types')
            for type in types:
                # obj.lesson_type.add(models.NewLessonType.objects.get(name=type))
                m = models.NewLessonNameType(newlessonname=obj, newlessontype=models.NewLessonType.objects.get(name=type))
                m.save()

            return create_success_dict(msg='添加课程成功！',
                                       data=model_to_dict(obj))

        return create_failure_dict(msg='添加课程失败！',
                                   errors=new_lesson_name_form.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_new_lesson_name')
@transaction.atomic
def edit(request, *args, **kwargs):
    if request.method == 'POST':
        uuid = request.POST.get('uuid')
        try:
            obj = models.NewLessonName.objects.get(uuid=uuid)
        except:
            return create_failure_dict(msg='错误的uuid')
        new_lesson_name_form = NewLessonNameForm(request.POST)
        if new_lesson_name_form.is_valid():
            obj = new_lesson_name_form.save(obj=obj)
            types = request.POST.getlist('types')
            # 清除原先的数据
            models.NewLessonNameType.objects.filter(newlessonname=obj).delete()
            for type in types:
                m = models.NewLessonNameType(newlessonname=obj, newlessontype=models.NewLessonType.objects.get(name=type))
                m.save()

            return create_success_dict(msg='编辑课程成功！',
                                       data=model_to_dict(obj))

        return create_failure_dict(msg='编辑课程失败！',
                                   errors=new_lesson_name_form.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_new_lesson_name')
def delete(request, *args, **kwargs):
    if request.method == 'POST':
        if not cache.get('sudo'):
            return create_failure_dict(msg='请输入正确的超级管理员admin密码！')
        uuid = request.POST.get('uuid')
        if uuid:
            try:
                l = models.NewLessonName.objects.get(uuid=uuid)
            except:
                return create_failure_dict(msg='错误的uuid！')
            # if l.lessonschedule_set.count() > 0:
            #    return create_failure_dict(msg='课程表安排了该课程，无法删除')
            # if l.lessonteacher_set.count() > 0:
            #    return create_failure_dict(msg='该课程有上课老师，无法删除')
            l.deleted = True
            l.save()
            return create_success_dict(msg='删除课程成功！')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_new_lesson_name')
def import_from(request, *args, **kwargs):
    if request.method == 'POST':
        f = NewLessonNameUploadForm(request.POST, request.FILES)
        if f.is_valid():
            lesson_names = f.save()
            return create_success_dict(data=model_list_to_dict(lesson_names))

        return create_failure_dict(msg='导入学校开课课程失败！',
                                   errors=f.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_new_lesson_name')
def verify(request, *args, **kwargs):
    if request.method == 'POST':
        f = NewLessonNameUploadVerifyForm(request.POST, request.FILES)
        if f.is_valid():
            objs = f.save()
            return create_success_dict(data=model_list_to_dict(objs))

        return create_failure_dict(msg='验证学校开课课程失败！',
                                   errors=f.errors)
