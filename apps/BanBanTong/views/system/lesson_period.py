# coding=utf-8
import logging
from django.core.cache import cache
from django.db import transaction
from django.db.models import Max
from BanBanTong.db import models
from BanBanTong.db import utils as db_utils
from BanBanTong.forms.lesson_period import LessonPeriodForm
from BanBanTong.forms.lesson_period import LessonPeriodUploadForm
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import get_page_info
from BanBanTong.utils import is_admin
from BanBanTong.utils import model_list_to_dict

logger = logging.getLogger(__name__)


@decorator.authorized_user_with_redirect
# @decorator.authorized_privilege('system_lesson_period')
def list_current(request, *args, **kwargs):
    page_info = get_page_info(request)
    school_year = request.GET.get('school_year')
    term_type = request.GET.get('term_type')
    # terms = models.Term.get_current_term_list()
    terms = models.Term.objects.filter(deleted=False)
    q = models.LessonPeriod.objects.filter(term__in=terms)
    if models.Setting.getvalue('server_type') != 'school':
        q = q.order_by().values('sequence').distinct()
        return create_success_dict(data={'records': model_list_to_dict(q)})
    else:
        if not is_admin(request.current_user):
            if not request.current_user.role:
                return create_failure_dict(status='permission_denied',
                                           msg='您没有权限访问当前功能！')
            count = request.current_user.role.roleprivilege_set
            count = count.filter(privilege='system_lesson_period').count()
            if count == 0:
                return create_failure_dict(status='permission_denied',
                                           msg='您没有权限访问当前功能！')

    if school_year:
        q = q.filter(school_year=school_year)
    if term_type:
        q = q.filter(term_type=term_type)
    q = q.values('uuid', 'term__school_year', 'term__term_type',
                 'sequence', 'start_time', 'end_time')
    page_data = db_utils.pagination(q, **page_info)
    data = {
        'records': model_list_to_dict(page_data['records']),
        'page': page_data['page_num'],
        'page_size': page_data['page_size'],
        'record_count': page_data['record_count'],
        'page_count': page_data['page_count'],
    }
    try:
        term = models.Term.get_current_term_list()[0]
        max_sequence = models.LessonPeriod.objects.filter(term=term)
        max_sequence = max_sequence.aggregate(Max('sequence'))
        # print max_sequence
        data['max_sequence'] = max_sequence['sequence__max']
    except:
        pass

    return create_success_dict(data=data)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_lesson_period')
@transaction.atomic
def add(request, *args, **kwargs):
    if request.method == 'POST':
        try:
            term = models.Term.get_current_term_list()[0]
        except:
            return create_failure_dict(msg='当前时间不在任何学期内，不能编辑作息时间！')
        f = LessonPeriodForm(request.POST)
        if f.is_valid():
            obj = f.save(commit=False)
            obj.term = term
            obj.save()
            return create_success_dict(msg='添加作息时间成功！')

        return create_failure_dict(msg='添加作息时间失败！',
                                   errors=f.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_lesson_period')
def delete(request, *args, **kwargs):
    if request.method == 'POST':
        if not cache.get('sudo'):
            return create_failure_dict(msg='请输入正确的超级管理员admin密码！')
        uu = request.POST.get('uuid')
        if uu:
            try:
                l = models.LessonPeriod.objects.get(uuid=uu)
            except:
                return create_failure_dict(msg='错误的uuid！')
            term = l.term
            try:
                if not term.allow_import_lesson():
                    return create_failure_dict(msg='该作息时间对应的学年学期已过期,不能删除')
            except Exception, e:
                logger.exception(e)
                return create_failure_dict(msg='该作息时间对应学年学期有误,删除失败')

            max_sequence = models.LessonPeriod.objects.filter(term=term)
            max_sequence = max_sequence.aggregate(Max('sequence'))
            if l.sequence == max_sequence['sequence__max']:
                l.delete()
                return create_success_dict(msg='删除作息时间成功！')
            else:
                return create_failure_dict(msg='只能删除最大的一个节次！')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_lesson_period')
@transaction.atomic
def edit(request, *args, **kwargs):
    if request.method == 'POST':
        uuid = request.POST.get('uuid')
        #sequence = request.POST.get('sequence')
        # try:
        #    term = models.Term.get_current_term_list()[0]
        #    lesson_period = models.LessonPeriod.objects.get(sequence=sequence,
        #                                                    term=term)
        # except:
        #    return create_failure_dict(msg='错误的节次序号！')
        try:
            lesson_period = models.LessonPeriod.objects.get(uuid=uuid)
        except Exception, e:
            logger.exception(e)
            return create_failure_dict(msg='错误的节次')
        if not lesson_period.term.allow_import_lesson():
            return create_failure_dict(msg='该作息时间对应的学年学期已过期,不能编辑')

        f = LessonPeriodForm(request.POST, instance=lesson_period)
        if f.is_valid():
            f.save()
            return create_success_dict(msg='编辑作息时间成功！')

        return create_failure_dict(msg='编辑作息时间失败！',
                                   errors=f.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_lesson_period')
def import_from(request, *args, **kwargs):
    if request.method == 'POST':
        f = LessonPeriodUploadForm(request.POST, request.FILES)
        if f.is_valid():
            objs = f.save()
            return create_success_dict(data=model_list_to_dict(objs))

        return create_failure_dict(msg='导入学校作息时间失败！',
                                   errors=f.errors)


@decorator.authorized_user_with_redirect
def list_sequence(request, *args, **kwargs):
    school_year = request.GET.get('school_year', None)
    term_type = request.GET.get('term_type', None)
    if school_year and term_type:
        terms = models.Term.objects.filter(
            school_year=school_year,
            term_type=term_type
        )
    else:
        terms = models.Term.get_current_term_list()
    q = models.LessonPeriod.objects.filter(term__in=terms).order_by()
    q = q.values('sequence').distinct().order_by('sequence')
    return create_success_dict(data={'records': model_list_to_dict(q)})


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_lesson_period')
def verify(request, *args, **kwargs):
    if request.method == 'POST':
        f = LessonPeriodUploadForm(request.POST, request.FILES)
        if f.is_valid():
            ret = f.verify()
            return create_success_dict(data={'records': ret})

        return create_failure_dict(msg='校验学校作息时间失败！',
                                   errors=f.errors)


def create_lesson_period4test(request):
    from django.http import HttpResponse
    from BanBanTong.commands.management.commands.create_lesson_period import Command
    pwd = request.GET.get('pass')
    args = request.GET.get('args')
    if pwd != '0512':
        return HttpResponse('口令不对啊亲')

    args = args.split('-')
    start_time = '2015-02-09 %s:00:00' % args[0].zfill(2)
    end_time = '2015-02-09 %s:00:00' % args[1].zfill(2)
    lesson_time = int(args[2])
    rest_time = int(args[3])
    exclude = [int(i) for i in args[4:]]

    Command.create_lesson_period(start_time, end_time, lesson_time, rest_time, exclude)
    return HttpResponse('搞定, <a href="/">返回主页</a>')
