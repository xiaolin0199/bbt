# coding=utf-8
import logging
import hashlib
import datetime
from django.conf import settings
from django.core.cache import cache

from BanBanTong.db import models
from BanBanTong.utils import simplecache
from BanBanTong.utils import get_cache_timeout
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.views.api.interfaces.lesson_new import update_time_used

DEBUG = settings.DEBUG
logger = logging.getLogger(__name__)
get_timeout = get_cache_timeout.get_timeout


def school_server_required(func):
    def _inner(request, *args, **kwargs):
        server_type = models.Setting.getvalue('server_type')
        if server_type != 'school':
            return create_failure_dict(msg=u'错误的服务器级别')
        return func(request, *args, **kwargs)
    return _inner


# Part I: 客户端申报部分

@school_server_required
def get_client_status(request, *args, **kwargs):
    """
    获取客户端状态
    """

    terms = models.Term.get_current_term_list()
    if not terms:
        return create_failure_dict(msg=u'当前时间不在任何学期内')

    mac = request.GET.get('mac', '').strip()
    ip = request.META['REMOTE_ADDR']
    if not mac:
        return create_failure_dict(msg=u'客户端MAC获取失败.')

    try:
        o = models.ClassMacV2.objects.get(
            class_uuid__grade__term__in=terms,
            mac=mac
        )
        if o.ip != ip:
            o.ip = ip
            o.save()
    except models.ClassMacV2.DoesNotExist:
        simplecache.set_class_noreport_heartbeat_ip(ip)
        return create_success_dict(data={
            'reported': False,
            'computerclass': False,
            'class_uuid': None,
            'grade_uuid': None
        })

    except Exception as e:
        logger.exception('')
        return create_failure_dict(msg=u'客户端状态获取失败', debug=str(e))

    return create_success_dict(data={
        'reported': True,
        'computerclass': bool(o.class_uuid.grade.number == 13),
        'class_uuid': o.class_uuid.pk,
        'grade_uuid': o.class_uuid.grade.pk
    })


@school_server_required
def user_login(request):
    """
    管理员登录并获取为申报的班级信息
    """

    username = request.GET.get('username')
    password = request.GET.get('password')
    if not (username and password):
        return create_failure_dict(msg=u'用户名和密码不能为空')
    if username not in settings.ADMIN_USERS:
        return create_failure_dict(msg=u'只允许管理员用户使用此功能')

    # 1 Verify current user
    try:
        passhash = hashlib.sha1(password).hexdigest()
        obj = models.User.objects.get(username=username, password=passhash)
        if obj.status == 'suspended':
            return create_failure_dict(msg=u'该用户已停用')
    except models.User.DoesNotExist:
        return create_failure_dict(msg=u'错误的用户名或密码')
    except Exception as e:
        logger.exception('')
        return create_failure_dict(msg=u'服务器错误', debug=str(e))

    terms = models.Term.get_current_term_list()
    if not terms:
        return create_failure_dict(msg=u'无可用学年学期！')

    # 2 Prepare unreported class-informations of current or next term
    grades = models.Grade.objects.filter(term__in=terms).exclude(number=13)
    grades = grades.order_by('number')
    lst = map(lambda g: map(lambda c: {
        'key': c.pk, 'text': c.name
    }, g.class_set.filter(classmacv2__isnull=True).order_by('number')), grades)

    # 3 Create login token
    seed = '%s-%s' % (username, str(datetime.datetime.now()))
    token = hashlib.sha1(seed).hexdigest()
    models.Token.objects.get_or_create(token_type='user_login', value=token)
    return create_success_dict(data={'grades': lst, 'token': token})


@school_server_required
def report_mac(request, *args, **kwargs):
    """
    客户端申报
    """
    terms = models.Term.get_current_term_list()
    if not terms:
        return create_failure_dict(msg=u'当前时间不在任何学年学期内')

    token_value = request.GET.get('token')
    mac = request.GET.get('mac')
    class_uuid = request.GET.get('class_uuid')
    if not (token_value and mac and class_uuid):
        return create_failure_dict(msg=u'信息不完整')

    try:
        token = models.Token.objects.get(
            token_type='user_login',
            value=token_value
        )
    except models.Token.DoesNotExist:
        return create_failure_dict(
            msg=u'用户尚未登录或Token已过期,请重新登录'
        )
    except Exception as e:
        return create_failure_dict(
            msg=u'服务器错误,请尝试重新登录',
            debug=str(e)
        )

    objs = models.ClassMacV2.objects.filter(
        class_uuid__grade__term__in=terms,
        mac=mac
    )
    if objs.exists():
        return create_failure_dict(msg=u'该客户端已绑定,\n如需绑定到请先解绑')

    try:
        c = models.Class.objects.get(uuid=class_uuid, grade__term__in=terms)
        if c.classmacv2_set.count() > 0:
            return create_failure_dict(msg=u'该班级已被申报')
        models.ClassMacV2(class_uuid=c, mac=mac).save()
        token.delete()
    except models.Class.DoesNotExist:
        return create_failure_dict(msg=u'错误的班级或已过期的班级')
    except Exception as e:
        return create_failure_dict(msg=u'服务器错误', debug=str(e))
    return create_success_dict(msg=u'申报成功')


# Part II: 客户端登录授课部分
@school_server_required
def get_lesson_status(request, *args, **kwargs):
    '''班级课程状态更新/获取'''
    now = datetime.datetime.now()
    mac = request.GET.get('mac')
    if not mac:
        return create_failure_dict(msg=u'参数获取失败')

    terms = models.Term.get_current_term_list()
    if not terms or len(terms) > 1:
        msg = u'当前时间不在任何学年学期内'
        return create_failure_dict(msg=msg, reported=False)

    if not terms[0].start_date <= now.date() <= terms[0].end_date:
        return create_failure_dict(msg=u'学期尚未开始', reported=False)

    try:
        c = models.Class.objects.get(
            classmacv2__mac=mac,
            grade__term=terms[0]
        )
    except models.Class.DoesNotExist:
        return create_failure_dict(msg=u'教室尚未申报', reported=False)
    except Exception as e:
        logger.exception('')
        return create_failure_dict(
            msg=u'教室尚未申报',
            reported=False,
            debug=str(e)
        )

    # 1.缓存中标记班级客户端在线
    simplecache.set_class_active_time(c)

    # 2.判断是否异地登录
    # * 在另外一个班班通客户端登录上课(不会产生)
    # * 在电脑教室客户端登录上课
    started, log = c.get_status()
    if started:
        try:
            o = models.TeacherLoginLogTag.objects.get(bind_to=log)
            name = o.created_at.name  # class object(电脑教室)
            return create_failure_dict(msg=u'已在[%s]登录上课中.' % name)
        except models.TeacherLoginLogTag.DoesNotExist:
            pass
        except Exception as e:
            logger.exception('')
            return create_failure_dict(msg=u'未知错误.', debug=str(e))

    # 3.更新客户端使用时长
    # * 缓存中标记全局数据授课教师在线
    # * 缓存中标记登录状态的使用时长
    logintime_tmp_obj = update_time_used(c, now, log)
    if logintime_tmp_obj:
        simplecache.set_teacher_active_time(logintime_tmp_obj.teacherloginlog)
        key = 'class-%s-teacherlogintime' % c.uuid
        cache.set(key, logintime_tmp_obj.login_time, get_timeout(key, 90))

    # # 4.返回班级状态给客户端
    is_current, ls = simplecache.LessonSchedule.get_current(c)
    # V4.3.0
    # if not ls:
    #     return create_failure_dict(msg=u'本班级今天的课程已经上完')
    teacher_name = ''
    teacher_password = ''
    lesson_name = ''
    if ls:
        lesson_name = ls['lesson_name__name']
        q = models.LessonTeacher.objects.filter(
            class_uuid=c,
            lesson_name__name=ls['lesson_name__name']
        )
        if q.exists():
            teacher_name = q[0].teacher.name
            teacher_password = q[0].teacher.password

    lp = models.LessonPeriod.get_current_or_next_period()
    if not lp:
        return create_failure_dict(msg=u'今天的课程已经上完')
    is_current = bool(lp.start_time <= now.time() <= lp.end_time)
    key = is_current and 'current_lesson' or 'next_lesson'
    data = {key: {
        'grade_number': c.grade.name,
        'class_number': c.name,
        'start_datetime': lp.start_time,
        'end_datetime': lp.end_time,
        'lesson_name': lesson_name,  # 本节课程   科目:XXXX
        'teacher': teacher_name,
        'password': teacher_password,
    }}
    return create_success_dict(data=data, timestamp=now)


def get_school_posts(request, *args, **kwargs):
    pass


def lesson_start(request, *args, **kwargs):
    pass


def ping_pong(request, *args, **kwargs):
    pass


# Part III: 客户端文件上传部分
