# coding=utf-8
from django.core.cache import cache
from BanBanTong.db import models
from BanBanTong.forms.computer_class_mac import ComputerClassForm
from BanBanTong.utils import decorator
from BanBanTong.utils import model_list_to_dict
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import paginatoooor
from activation.decorator import activation_required


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_grade_class')
@activation_required
def add(request, *args, **kwargs):
    """年级班级管理>班班通电脑教室>添加教室"""
    term = models.Term.get_current_term_list()[0]
    if not term:
        return create_failure_dict(msg=u'当前时间不在任何学年学期内')
    f = ComputerClassForm(request.POST, request=request)
    if not f.is_valid():
        return create_failure_dict(msg=u'添加失败', errors=f.errors)
    f.save()
    return create_success_dict(msg=u'添加成功')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_grade_class')
def edit(request, *args, **kwargs):
    """年级班级管理>班班通电脑教室>编辑教室"""
    terms = models.Term.get_current_term_list()
    if not terms:
        return create_failure_dict(msg=u'当前时间不在任何学年学期内')
    class_uuid = request.POST.get('uuid')
    # class_name = request.POST.get('name', None)
    # client_number = request.POST.get('client_number', None)
    # lesson_range = request.POST.getlist('lesson_range', None)
    try:
        cls = models.Class.objects.get(uuid=class_uuid)
        cc = cls.computerclass
    except models.Class.DoesNotExist:
        return create_failure_dict(msg=u'错误的UUID')
    except Exception as e:
        return create_failure_dict(msg=u'服务器错误', debug=str(e))

    f = ComputerClassForm(request.POST, request=request, cc=cc, cls=cls)
    if not f.is_valid():
        return create_failure_dict(msg=u'编辑失败', errors=f.errors)
    f.save()
    return create_success_dict(msg=u'编辑成功')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_grade_class')
def clear_mac(request, *args, **kwargs):
    """年级班级管理>班班通电脑教室>清除绑定"""
    class_uuid = request.POST.get('uuid', None)
    if not class_uuid:
        return create_failure_dict(msg='未获取到电脑教室信息')
    try:
        models.ClassMacV2.objects.get(class_uuid=class_uuid).delete()
        return create_success_dict(msg='清除绑定成功')
    except Exception as e:
        return create_failure_dict(msg='清除绑定失败', errors=[[str(e)], ])


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_grade_class')
def delete(request, *args, **kwargs):
    """年级班级管理>班班通电脑教室>删除教室"""
    class_uuid = request.POST.get('uuid', None)
    if not class_uuid:
        return create_failure_dict(msg='未获取到电脑教室信息')
    if not cache.get('sudo'):
        return create_failure_dict(msg='请输入正确的超级管理员admin密码')
    try:
        c = models.Class.objects.get(uuid=class_uuid)
    except:
        return create_failure_dict(msg='错误的UUID')
    if c.classmacv2_set.count() > 0:
        return create_failure_dict(msg='请先清除MAC地址绑定')
    try:
        term = c.grade.term
        if not term.allow_import_lesson():
            return create_failure_dict(msg='该电脑教室对应的学年学期已过期,不能删除')
    except:
        return create_failure_dict(msg='该电脑教室无对应的学年学期,删除失败')
    grade = c.grade
    c.delete()
    if grade.class_set.count() == 0:
        grade.delete()
    return create_success_dict(msg='删除成功')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_grade_class')
def view_curriculum(request, *args, **kwargs):
    """年级班级管理>班班通电脑教室>查看课表"""
    class_uuid = request.POST.get('uuid', None)
    try:
        cc = models.ComputerClass.objects.get(class_bind_to=class_uuid)
    except:
        return create_failure_dict(msg='不存在的电脑教室')
    lessons = cc.get_curriculum()
    curriculum = lessons.values('weekday',
                                # 'class_uuid',
                                'class_uuid__name',
                                'class_uuid__number',
                                # 'class_uuid__grade__uuid',
                                'class_uuid__grade__name',
                                'class_uuid__grade__number',
                                # 'lesson_period__uuid',
                                'lesson_period__sequence',
                                'lesson_period__start_time',
                                'lesson_period__end_time',
                                # 'lesson_name',
                                'lesson_name__name')
    return create_success_dict(data=model_list_to_dict(curriculum))


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_grade_class')
def list_current(request, *args, **kwargs):
    """年级班级管理>班班通电脑教室>显示电脑教室"""
    terms = models.Term.objects.filter(deleted=False)
    q = models.Class.objects.filter(grade__term__in=terms, grade__number=13)
    uuids = q.values_list('uuid', flat=True)
    cc = models.ComputerClass.objects.filter(class_bind_to__in=uuids).order_by('class_bind_to__number')
    ret = []
    for i in cc:
        d = {}
        d['uuid'] = i.class_bind_to.uuid
        d['computerclass_uuid'] = i.uuid
        d['mac'] = i.class_bind_to.mac()
        d['school_year'] = i.class_bind_to.grade.term.school_year
        d['term_type'] = i.class_bind_to.grade.term.term_type
        d['name'] = i.class_bind_to.name
        d['number'] = i.class_bind_to.number
        d['client_number'] = i.client_number
        d['lesson_range'] = [list(j) for j in i.lesson_range.values_list('uuid', 'name', flat=False)]
        d['grade_name'] = i.class_bind_to.grade.name
        ret.append(d)

    return paginatoooor(request, ret)
