# coding=utf-8
import os
import uuid
import datetime
from django.conf import settings
from BanBanTong.db import models
from BanBanTong.utils import decorator
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import model_list_to_dict
from BanBanTong.utils import simplecache
import xlwt
from BanBanTong import constants
from django.core.urlresolvers import reverse
from BanBanTong.forms.lesson_schedule import LessonScheduleUploadForm


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_class_lesson')
def import_from(request, *args, **kwargs):
    if request.method == 'POST':
        f = LessonScheduleUploadForm(request.POST, request.FILES)
        if f.is_valid():
            objs = f.save()
            grade_name = request.POST.get('grade_name')
            class_name = request.POST.get('class_name')
            simplecache.LessonSchedule.update_class(grade_name, class_name)
            return create_success_dict(data=model_list_to_dict(objs))

        return create_failure_dict(msg='导入班级课程表失败！',
                                   errors=f.errors)

    return create_failure_dict(msg='请上传课程表文件！')


def update_lessonschedule(cls, lp, lsn):
    """
    4.3.0版本去除了课表必要性的限制,取而代之的是通过上课的历史记录更新课表
    这里的这个方法就是用来做这件事的
    参数:
        cls: models.Class instance
        lp: models.LessonPeriod instance
        lsn: models.LessonName instance
    """
    if settings.AUTO_LESSONSCHEDULE:
        if not (cls and lp and lsn):
            return
        is_new, obj = models.LessonSchedule.objects.get_or_create(
            class_uuid=cls,
            lesson_period=lp,
            weekday=datetime.datetime.now().strftime('%a').lower(),
            defaults={
                'lesson_name': lsn
            }
        )
        if not is_new and obj.lesson_name != lsn:
            obj.lesson_name = lsn
            obj.save()


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_class_lesson')
def export(request, *args, **kwargs):
    '''导出班级课程表'''
    grade_name = request.GET.get('grade_name', None)
    class_name = request.GET.get('class_name', None)
    xls = xlwt.Workbook(encoding='utf8')
    title = u'%s年级%s班课程表' % (grade_name, class_name)
    sheet = xls.add_sheet(title)
    header = (
        u'节次', u'周一', u'周二', u'周三',
        u'周四', u'周五', u'周六', u'周日'
    )
    weekday = (u'mon', u'tue', u'wed', u'thu', u'fri', u'sat', u'sun')
    for i in range(len(header)):
        sheet.write(0, i, header[i])
    row = 1
    try:
        t = models.Term.get_current_term_list()[0]
    except:
        return create_failure_dict(msg='当前时间不在任何学期内')

    if not (grade_name and class_name):
        return create_failure_dict(msg='grade_name and class_name are required')
    klass = models.Class.objects.filter(
        grade__term=t,
        grade__name=grade_name,
        name=class_name
    )
    if not klass.exists():
        return create_failure_dict(msg='This class is not exists!')
    klass = klass[0]
    objs = models.LessonSchedule.objects.filter(class_uuid=klass)

    objs = objs.values(
        'lesson_period__sequence',
        'weekday',
        'lesson_name__name',
    )

    for i in objs:
        row = int(i['lesson_period__sequence'])
        column = weekday.index(i['weekday']) + 1
        try:
            sheet.write(row, 0, row)
        except:
            pass
        sheet.write(row, column, i['lesson_name__name'])

    cached_id = str(uuid.uuid1())
    tmp_file = os.path.join(constants.CACHE_TMP_ROOT, cached_id)
    xls.save(tmp_file)
    filename = u'%s.xls' % title
    return create_success_dict(url=reverse('base:xls_download',
                                           kwargs={'cached_id': cached_id,
                                                   'name': filename}))


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_class_lesson')
def list_current(request, *args, **kwargs):
    uuid = request.GET.get('uuid')
    q = models.LessonSchedule.objects.all()
    q = q.filter(class_uuid__grade__term__deleted=False)
    if uuid:
        q = q.filter(class_uuid=uuid)
    q = q.values('uuid', 'class_uuid', 'lesson_period__uuid',
                 'lesson_period__sequence', 'lesson_period__start_time',
                 'lesson_period__end_time', 'weekday', 'lesson_name__name')
    return create_success_dict(data={
        'records': model_list_to_dict(q)
    })


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_class_lesson')
def verify(request, *args, **kwargs):
    if request.method == 'POST':
        f = LessonScheduleUploadForm(request.POST, request.FILES, 'verify')
        if f.is_valid():
            ret = f.verify()
            return create_success_dict(data={'records': ret})

        return create_failure_dict(msg='校验班级课程表失败！',
                                   errors=f.errors)
