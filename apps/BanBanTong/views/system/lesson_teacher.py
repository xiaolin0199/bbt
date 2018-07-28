# coding=utf-8
import logging
import os
import uuid
import xlwt
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db import transaction
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.db import utils as db_utils
from BanBanTong.forms.lesson_teacher import LessonTeacherForm
from BanBanTong.forms.lesson_teacher import LessonTeacherUploadForm
from BanBanTong.forms.lesson_teacher import LessonTeacherUploadVerifyForm
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import get_page_info
from BanBanTong.utils import model_list_to_dict
from BanBanTong.utils import model_to_dict
from BanBanTong.utils import simplecache

logger = logging.getLogger(__name__)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_class_lesson')
@transaction.atomic
def add(request, *args, **kwargs):
    if request.method == 'POST':
        try:
            f = LessonTeacherForm(request.POST)
            if f.is_valid():
                lesson_teacher = f.save()
                simplecache.LessonTeacher.update(lesson_teacher.class_uuid.uuid)
                data = model_to_dict(lesson_teacher)
                school_year = lesson_teacher.class_uuid.grade.term.school_year
                data['class_uuid__grade__term__school_year'] = school_year
                term_type = lesson_teacher.class_uuid.grade.term.term_type
                data['class_uuid__grade__term__term_type'] = term_type
                grade_name = lesson_teacher.class_uuid.grade.name
                data['class_uuid__grade__name'] = grade_name
                data['class_uuid__name'] = lesson_teacher.class_uuid.name
                data['lesson_name__name'] = lesson_teacher.lesson_name.name
                data['teacher__name'] = lesson_teacher.teacher.name
                try:
                    stat_obj = models.Statistic.objects.get(key=lesson_teacher.class_uuid.pk)
                    stat_obj.cala('teacher_num', True)
                except Exception as e:
                    logger.exception(e)
                return create_success_dict(msg='添加班级课程授课教师记录成功！',
                                           data=data)

            return create_failure_dict(msg='添加班级课程授课教师记录失败！',
                                       errors=f.errors)
        except IntegrityError:
            msg = '已有相同的年级班级-课程-教师姓名，无法重复添加！'
            return create_failure_dict(msg=msg)
        except Exception as e:
            logger.exception(e)
            return create_failure_dict(msg=u'添加班级课程授课教师记录失败！', debug=str(e))


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_class_lesson')
def delete(request, *args, **kwargs):
    if request.method == 'POST':
        if not cache.get('sudo'):
            return create_failure_dict(msg=u'请输入正确的超级管理员admin密码！')
        uu = request.POST.get('uuid')
        if uu:
            try:
                obj = models.LessonTeacher.objects.get(uuid=uu)
                objs = obj.teacherloginlog_set.count()
                if objs > 0:
                    return create_failure_dict(msg=u'该教师已经产生登录授课记录,仅支持编辑.')
            except:
                return create_failure_dict(msg=u'错误的uuid！')
            try:
                if not obj.class_uuid.grade.term.allow_import_lesson():
                    return create_failure_dict(msg=u'该信息学年学期已过期,不能删除')
                obj.delete()
                simplecache.LessonTeacher.update(obj.class_uuid.uuid)
            except Exception as e:
                logger.exception('')
                return create_failure_dict(msg=u'内部错误', debug=str(e))
        return create_success_dict(msg=u'删除班级课程授课教师记录成功！')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_class_lesson')
@transaction.atomic
def edit(request):
    if request.method == 'POST':
        uu = request.POST.get('uuid')
        try:
            l = models.LessonTeacher.objects.get(uuid=uu)
        except:
            return create_failure_dict(msg='错误的uuid！')
        if not l.class_uuid.grade.term.allow_import_lesson():
            return create_failure_dict(msg='该信息学年学期已过期,不能编辑')
        form = LessonTeacherForm(request.POST, instance=l)
        if form.is_valid():
            form.save()
            simplecache.LessonTeacher.update(l.class_uuid.uuid)
            return create_success_dict(msg='编辑班级课程授课教师记录成功！')

        return create_failure_dict(msg='编辑班级课程授课教师记录失败！',
                                   errors=form.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_class_lesson')
def export(request, *args, **kwargs):
    '''导出所有班级课程授课教师信息'''
    xls = xlwt.Workbook(encoding='utf8')
    title = u'学期班级课程授课老师信息'
    sheet = xls.add_sheet(title)
    header = [u'姓名', u'生日', u'授课年级', u'授课班级',
              u'授课课程', u'计划课时']
    for i in range(len(header)):
        sheet.write(0, i, header[i])
    row = 1
    try:
        t = models.Term.get_current_term_list()[0]
    except:
        return create_failure_dict(msg='当前时间不在任何学期内')
    q = models.LessonTeacher.objects.filter(class_uuid__grade__term=t)
    grade_name = request.REQUEST.get('grade_name', None)
    class_name = request.REQUEST.get('class_name', None)
    lesson_name = request.REQUEST.get('lesson_name', None)
    teacher_name = request.REQUEST.get('teacher_name', None)
    if grade_name:
        q = q.filter(class_uuid__grade__name=grade_name)
    if class_name:
        q = q.filter(class_uuid__name=class_name)
    if lesson_name:
        q = q.filter(lesson_name__name=lesson_name)
    if teacher_name:
        q = q.filter(teacher__name__contains=teacher_name)

    q = q.values('teacher__name', 'teacher__birthday',
                 'class_uuid__grade__name', 'class_uuid__name',
                 'lesson_name__name', 'schedule_time')
    for i in q:
        sheet.write(row, 0, i['teacher__name'])
        sheet.write(row, 1, str(i['teacher__birthday']).replace('-', ''))
        sheet.write(row, 2, i['class_uuid__grade__name'])
        sheet.write(row, 3, i['class_uuid__name'])
        sheet.write(row, 4, i['lesson_name__name'])
        sheet.write(row, 5, i['schedule_time'])
        row += 1
    cached_id = str(uuid.uuid1())
    tmp_file = os.path.join(constants.CACHE_TMP_ROOT, cached_id)
    xls.save(tmp_file)
    filename = u'%s.xls' % title
    return create_success_dict(url=reverse('base:xls_download',
                                           kwargs={'cached_id': cached_id,
                                                   'name': filename}))


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_class_lesson')
def import_from(request, *args, **kwargs):
    if request.method == 'POST':
        f = LessonTeacherUploadForm(request.POST, request.FILES)
        if f.is_valid():
            objs = f.save()
            simplecache.LessonTeacher.update()

            # 更新一下Statistic表中的登记教师总数
            klasses = map(lambda i: i.class_uuid.uuid, objs)
            klasses = models.Class.objects.filter(uuid__in=klasses)
            for cls in klasses:
                try:
                    stat_obj = models.Statistic.objects.get(key=cls.pk)
                    stat_obj.cala('teacher_num', True)
                except Exception as e:
                    logger.exception(e)

            return create_success_dict(data=model_list_to_dict(objs))
        return create_failure_dict(msg='导入班级课程授课老师失败！',
                                   errors=f.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_class_lesson')
def list_current(request, *args, **kwargs):
    page_info = get_page_info(request)
    grade_name = request.GET.get('grade_name')
    class_name = request.GET.get('class_name')
    lesson_name = request.GET.get('lesson_name')
    teacher_name = request.GET.get('teacher_name')

    terms = models.Term.objects.filter(deleted=False)
    q = models.LessonTeacher.objects.filter(class_uuid__grade__term__in=terms)
    if grade_name:
        q = q.filter(class_uuid__grade__name=grade_name)
    if class_name:
        q = q.filter(class_uuid__name=class_name)
    if lesson_name:
        q = q.filter(lesson_name__name=lesson_name)
    if teacher_name:
        q = q.filter(teacher__name__contains=teacher_name)
    order_lst = (
        'class_uuid__grade__number',
        'class_uuid__number',
        'lesson_name__name'
    )
    q = q.order_by(*order_lst)
    q = q.values('uuid', 'class_uuid__grade__term__school_year',
                 'class_uuid__grade__term__term_type',
                 'class_uuid__grade__name', 'class_uuid__name',
                 'lesson_name__name', 'teacher__name', 'teacher__uuid',
                 'teacher__birthday',
                 'schedule_time')
    grade_class_assigned_time_dict = {}
    q = list(q)
    for one in q:
        key = u'%s_%s' % (one['class_uuid__grade__name'], one['class_uuid__name'])
        if not grade_class_assigned_time_dict.has_key(key):
            uuid = one.get('uuid')
            one_class = models.LessonTeacher.objects.get(uuid=uuid).class_uuid
            one['remain_time'] = int(one_class.grade.term.schedule_time) - int(one_class.cala_assigned_time())
            grade_class_assigned_time_dict[key] = one['remain_time']
        else:
            one['remain_time'] = grade_class_assigned_time_dict[key]

    page_data = db_utils.pagination(q, **page_info)

    return create_success_dict(data={
        'records': model_list_to_dict(page_data['records']),
        'page': page_data['page_num'],
        'page_size': page_data['page_size'],
        'record_count': page_data['record_count'],
        'page_count': page_data['page_count'],
    })


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_class_lesson')
def verify(request, *args, **kwargs):
    if request.method == 'POST':
        f = LessonTeacherUploadVerifyForm(request.POST, request.FILES)
        if f.is_valid():
            objs = f.save()
            return create_success_dict(data={'records': model_list_to_dict(objs)})

        return create_failure_dict(msg='验证班级课程授课老师失败！',
                                   errors=f.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_class_lesson')
def get_remain_time(request):
    '''获取每个班级的剩余可分配课时'''
    if request.method == 'GET':
        data = request.GET
    else:
        data = request.POST
    grade_name = data.get('grade_name')
    class_name = data.get('class_name')

    try:
        term = models.Term.get_current_term_list()[0]
        class_obj = models.Class.objects.get(name=class_name, grade__name=grade_name, grade__term=term)
    except Exception as e:
        logger.exception(e)
        return create_failure_dict(msg='错误的班级名称')

    remain_time = class_obj.cala_remain_time()

    return create_success_dict(data={'grade_name': class_obj.grade.name, 'class_name': class_obj.name, 'remain_time': remain_time})
