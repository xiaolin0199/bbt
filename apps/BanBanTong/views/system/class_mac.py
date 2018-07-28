# coding=utf-8
import logging
from django.conf import settings
from django.core.cache import cache
from BanBanTong.db import models
from BanBanTong.db import utils as db_utils
from BanBanTong.forms.class_mac import ClassForm, BatchClassForm
from BanBanTong.forms.class_mac import ClassUploadForm
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import get_page_info
from BanBanTong.utils import model_list_to_dict
from activation.decorator import activation_required
from BanBanTong.utils import str_util

logger = logging.getLogger(__name__)


@decorator.authorized_user_with_redirect
def get_choices(request):
    """添加班级的时候获取可选的班号"""
    grade_name = request.GET.get('grade_name', None)
    grade_number = str_util.grade_name_to_number(grade_name)
    custom_grade_name = settings.CONF.server.grade_map.get(grade_name) or settings.CONF.server.grade_map.get(str(grade_name)) or grade_name
    terms = models.Term.get_current_term_list()
    if not terms:
        return create_success_dict(data=[], debug='no term')
    if not grade_name:
        return create_success_dict(data=[], debug='grade_name needed')
    try:
        g = models.Grade.objects.get(term=terms[0], name=custom_grade_name, number=grade_number)
        lst = g.class_set.values_list('number', flat=True)
        lst = set(range(1, max(lst and lst or [1]) + 2)) - set(lst)
        numbers = list(lst)
        return create_success_dict(
            data=[{'text': i} for i in numbers],
            debug='some one'
        )
    except models.Grade.DoesNotExist:
        return create_success_dict(data=[{'text': 1}, ], debug='first one')
    except Exception as e:
        return create_success_dict(data=[], debug=str(e))


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_grade_class')
@activation_required
def batch_add(request, *args, **kwargs):
    if request.method == 'POST':
        batch_class_record = BatchClassForm(request.POST)
        if batch_class_record.is_valid():
            batch_class_record.save()
            return create_success_dict(msg='批量添加班级成功！')

        return create_failure_dict(msg='批量添加班级失败！',
                                       errors=batch_class_record.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_grade_class')
# @activation_required
def add(request, *args, **kwargs):
    if request.method == 'POST':
        f = ClassForm(request.POST)
        if f.is_valid():
            f.save()
            return create_success_dict(msg='添加班级成功！')
        return create_failure_dict(msg='添加班级失败！', errors=f.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_grade_class')
def edit(request, *args, **kwargs):
    if request.method == 'POST':
        uuid = request.POST.get('uuid')
        try:
            obj = models.Class.objects.get(uuid=uuid)
        except Exception as e:
            logger.exception(e)
            return create_failure_dict(msg='错误的班级UUID')
        f = ClassForm(request.POST, instance=obj)
        if f.is_valid():
            f.save()
            return create_success_dict(msg='编辑班级成功！')

        return create_failure_dict(msg='编辑班级失败！', errors=f.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_grade_class')
def clear_mac(request, *args, **kwargs):
    if request.method == 'POST':
        uuid = request.POST.get('uuid')
        if uuid:
            models.ClassMacV2.objects.filter(class_uuid=uuid).delete()
            return create_success_dict(msg='清除绑定成功！')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_grade_class')
def delete(request, *args, **kwargs):
    '''班级有MAC地址绑定时，不能删除
       删除班级同时删除课程表和班级课程老师记录
       如果删除班级之后年级为空，就删除该年级'''
    if request.method == 'POST':
        if not cache.get('sudo'):
            return create_failure_dict(msg='请输入正确的超级管理员admin密码！')
        uu = request.POST.get('uuid')
        if uu:
            try:
                c = models.Class.objects.get(uuid=uu)
            except:
                return create_failure_dict(msg='错误的uuid！')
            if c.classmacv2_set.count() > 0:
                return create_failure_dict(msg='请先清除MAC地址绑定')
            # 如果该班级对应的学年学期已转结或是已过期则不能删除
            try:
                term = c.grade.term
                if not term.allow_import_lesson():
                    return create_failure_dict(msg=u'该班级信息对应的学年学期已过期,不能删除')
            except:
                return create_failure_dict(msg=u'该班级无对应的学年学期,删除失败')
            if c.class_teacherloginlog_set.all().exists() or \
                    c.teacherloginlogtag_set.all().exists():  # 电脑教室
                if c.grade.number == 13:
                    msg = u'不能删除已经产生登录日志的教室终端.'
                else:
                    msg = u'不能删除已经产生登录日志的班级.'
                return create_failure_dict(msg=msg)

            g = c.grade
            c.delete()
            if g.class_set.count() == 0:
                g.delete()
                q = models.User.objects.all().values_list('uuid', flat=True)
                for uu in q:
                    k = 'group-%s' % uu
                    cache.delete(k)
                cache.delete('group-all')
            return create_success_dict(msg='删除班级成功！')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_grade_class')
def get_unused_classtime(request, *args, **kwargs):
    uu = request.GET.get('uuid')
    try:
        c = models.Class.objects.get(uuid=uu)
    except:
        return create_failure_dict(msg='错误的uuid')
    try:
        classtime = c.classtime
    except:
        return create_failure_dict(msg='尚未设置学期参考计划课时')
    data = {'schedule_time': classtime.schedule_time,
            'assigned_time': classtime.assigned_time,
            'unused_time': classtime.schedule_time - classtime.assigned_time}
    return create_success_dict(data=data)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_grade_class')
def import_from(request, *args, **kwargs):
    if request.method == 'POST':
        f = ClassUploadForm(request.POST, request.FILES)
        if f.is_valid():
            classes = f.save()
            return create_success_dict(data=model_list_to_dict(classes))

        return create_failure_dict(msg='导入学校年级班级失败！',
                                   errors=f.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_grade_class')
def list_current(request, *args, **kwargs):
    page_info = get_page_info(request)
    school_year = request.GET.get('school_year')
    term_type = request.GET.get('term_type')

    terms = models.Term.objects.filter(deleted=False)
    q = models.Class.objects.filter(grade__term__in=terms).exclude(grade__number=13)
    if school_year:
        q = q.filter(grade__term__school_year=school_year)
    if term_type:
        q = q.filter(grade__term__term_type=term_type)

    q = q.values('uuid', 'grade__term__school_year',
                 'grade__term__term_type',
                 'grade__name', 'name', 'teacher',
                 'teacher__name', 'teacher__birthday',
                 'grade__term__schedule_time',
                 'classtime__schedule_time',
                 'classtime__assigned_time',
                 'classmacv2__mac')
    q = q.order_by('grade__number', 'number')

    q = list(q)
    for one in q:
        uuid = one.get('uuid')
        one_class = models.Class.objects.get(uuid=uuid)
        one['assigned_time'] = one_class.cala_assigned_time()

    page_data = db_utils.pagination(q, **page_info)

    return create_success_dict(data={
        'records': model_list_to_dict(page_data['records']),
        'page': page_data['page_num'],
        'page_size': page_data['page_size'],
        'record_count': page_data['record_count'],
        'page_count': page_data['page_count']
    })


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_grade_class')
def verify(request, *args, **kwargs):
    if request.method == 'POST':
        f = ClassUploadForm(request.POST, request.FILES)
        if f.is_valid():
            ret = f.verify()
            return create_success_dict(data={'records': ret})

        return create_failure_dict(msg='校验学校年级班级失败！',
                                   errors=f.errors)
