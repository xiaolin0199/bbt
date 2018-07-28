#!/usr/bin/env python
# coding=utf-8
import datetime
import traceback
import json
import logging
from django.core.cache import cache
from django.db import transaction
from django.utils.dateparse import parse_time
from BanBanTong.db import models
from BanBanTong.forms.api.lesson import LessonStartForm
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import format_record
from BanBanTong.utils import model_list_to_dict
from BanBanTong.utils import simplecache
from BanBanTong.utils.get_cache_timeout import get_timeout
from BanBanTong.views.system.lesson_schedule import update_lessonschedule
from django.conf import settings
DEBUG = settings.DEBUG
del settings

logger = logging.getLogger(__name__)


@transaction.atomic
def update_time_used(class_obj, now, obj=None):
    if not obj:
        s = datetime.datetime.combine(now.date(), datetime.time.min)
        e = datetime.datetime.combine(now.date(), datetime.time.max)
        try:
            obj = models.TeacherLoginLog.objects.get(
                class_uuid=class_obj,
                lesson_period_start_time__lte=now.time(),
                lesson_period_end_time__gte=now.time(),
                created_at__range=(s, e)
            )
        except models.TeacherLoginLog.DoesNotExist:
            # # 如果没有TeacherLoginLog,说明当前不在上课/或者是登录失败
            # if DEBUG:
            #     print 'update_time_used failed'
            #     print 'grade:', class_obj.grade.number, 'class', class_obj.number
            #     print 'current time:', now
            #     traceback.print_exc()
            return
        except Exception as e:
            logger.exception('')
            return

    try:
        o = models.TeacherLoginTimeTemp.objects.get(teacherloginlog=obj)
        # 客户端上次发送api/lesson/status/时，服务器记录了当时的datetime。
        # 本次再处理status时，取出上次的时间，计算timedelta。
        seconds = (now - o.last_login_datetime).total_seconds()
        if seconds > 180:  # 两次心跳间隔超过三分钟的认定为不在使用状态
            seconds = 15
        o.login_time += seconds
        o.last_login_datetime = now
        o.save()
    except models.TeacherLoginTimeTemp.DoesNotExist:
        if DEBUG:
            traceback.print_exc()
        return
    except Exception as e:
        logger.exception('')
        return
    return o


def _create_logtag(request, log):
    """在电脑教室的教师登录记录会同时在TeacherLoginLogTag中生成一条记录"""
    in_computerclass = request.GET.get('in_computerclass', False)
    if not in_computerclass:
        return
    if DEBUG:
        print 'DEBUG lesson_start ---2.3.1 --begin to create_logtag'
    mac = request.GET.get('computerclass', None)
    if not (mac and hasattr(log, 'term') and log.term):
        if DEBUG:
            print log.__dict__
        return
    try:
        o = models.ClassMacV2.objects.get(
            mac=mac,
            class_uuid__grade__number=13,
            class_uuid__grade__term=log.term
        )
    except models.ClassMacV2.DoesNotExist:
        return
    except:
        if DEBUG:
            traceback.print_exc()
        logger.exception('')
        # return
    if o and log:
        try:
            models.TeacherLoginLogTag.objects.get_or_create(
                bind_to=log,
                created_at=o.class_uuid
            )
            if DEBUG:
                print 'DEBUG lesson_start ---2.3.2 --create_logtag ok'
        except Exception as e:
            if DEBUG:
                traceback.print_exc()
            logger.exception('')
            if DEBUG:
                print 'DEBUG _create_logtag:failed trying save teacherloginlog in computerclass\n%s' % e

        lsn = log.school.lessonname_set.get(name=log.lesson_name, deleted=False)
        update_lessonschedule(o.class_uuid, log.lesson_period, lsn)


def status(request, *args, **kwargs):
    '''班级课程状态更新/获取'''
    now = datetime.datetime.now()
    mac = request.GET.get('mac', None)

    terms = models.Term.get_current_term_list()
    if not terms:
        return create_failure_dict(msg=u'无可用学年学期！', reported=False)

    if not terms[0].start_date <= now.date() <= terms[0].end_date:
        return create_failure_dict(msg=u'学期尚未开始', reported=False)

    try:
        c = models.Class.objects.get(classmacv2__mac=mac, grade__term=terms[0])
    except models.Class.DoesNotExist:
        return create_failure_dict(
            msg=u'教室尚未申报！',
            reported=False
        )
    except Exception as e:
        logger.exception('')
        return create_failure_dict(
            msg=u'教室尚未申报！',
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


# 客户端点击上课
def start(request, *args, **kwargs):
    """
    客户端点击上课
    参数:
        in_computerclass: 是否发送于电脑教室
        computerclass: 电脑教室客户端MAC
        mac/class_uuid: 上课班级MAC/UUID

    """
    in_computerclass = request.GET.get('in_computerclass', False)
    computerclass_mac = request.GET.get('computerclass', None)
    mac_or_uuid = request.GET.get('mac', request.GET.get('class_uuid', None))

    terms = models.Term.get_current_term_list()
    now = datetime.datetime.now()
    server_type = models.Setting.getvalue('server_type')
    if server_type != 'school':
        return create_failure_dict(msg=u'服务器类型错误')
    if not terms:
        return create_failure_dict(msg=u'无可用学年学期')
    elif not terms[0].start_date <= now.date() <= terms[0].end_date:
        return create_failure_dict(msg=u'学期尚未开始')
    if not mac_or_uuid:
        return create_failure_dict(msg=u'参数获取失败')

    # 1.获取欲上课的班级
    try:
        try:
            c = models.Class.objects.get(
                classmacv2__mac=mac_or_uuid,
                grade__term=terms[0]
            )
        except:
            # 未申报的班级去电脑教室上课时可通过uuid判断
            c = models.Class.objects.get(uuid=mac_or_uuid)

        mac = c.classmacv2_set.values_list('mac', flat=True)
        mac = mac and mac or u''
    except models.Class.DoesNotExist:
        return create_failure_dict(msg=u'服务器中未找到该班级')
    except Exception as e:
        traceback.print_exc()
        logger.exception('')
        return create_failure_dict(msg=u'服务器中未找到该班级', debug=str(e))

    # 2.判断班级授课状态
    is_started, log = c.get_status()
    if is_started:
        try:
            tag = models.TeacherLoginLogTag.objects.get(bind_to=log)
            started_class = tag.created_at  # 在电脑教室上课
        except models.TeacherLoginLogTag.DoesNotExist:
            started_class = log.class_uuid  # 在普通班级上课
        except Exception as e:
            if DEBUG:
                traceback.print_exc()
            logger.exception('')
            started_class = log.class_uuid  # 在普通班级上课

        if mac != started_class.mac():
            return create_failure_dict(msg=u'已在[%s年级%s班]登录上课中' % (
                started_class.grade,
                started_class
            ))

        return create_success_dict(data={
            'started': True,
            'server_time': datetime.datetime.now(),
            'time': log.lesson_period_end_time,
        })

    # 3.处理客户端上课的信息
    f = LessonStartForm(request.GET)
    if f.is_valid():
        if in_computerclass and computerclass_mac:
            try:
                o = models.ClassMacV2.objects.get(
                    mac=computerclass_mac,
                    class_uuid__grade__term=terms[0]
                )
                started, data = f.save(o.class_uuid)  # 传入电脑教室
            except:
                logger.exception('')
                started, data = f.save()
        else:
            started, data = f.save()

        if started:
            _create_logtag(request, data.get('log', None))
            if data.has_key('log'):
                del data['log']
            time = datetime.datetime.combine(now.date(), data['time'])
            data['time'] = time
            return create_success_dict(data=data)

        if data:
            if data.has_key('early_token'):
                # 返回的data中有一个更早的token,说明已经在另外的客户端提前登录了
                client_in = data['early_token'].get('client_in', '')
                return create_failure_dict(msg=u'已在[%s]登录' % client_in)
            time = datetime.datetime.combine(now.date(), data['time'])
            data['time'] = time
            return create_success_dict(data=data)
        return create_failure_dict(data={})
    return create_failure_dict(msg=u'上课失败！', errors=f.errors)


# 客户端提前点击上课
def start_status(request, *args, **kwargs):
    """
    如果点击上课按钮时，尚未进入上课时间，服务器回应一个token，
    客户端开始倒计时。倒计时结束，客户端用start_status检查是否
    开始上课。
    """

    # in_computerclass = request.GET.get('in_computerclass', False)
    if models.Setting.getvalue('server_type') != 'school':
        return create_failure_dict(msg=u'错误的服务器级别')
    token = request.GET.get('token', None)
    if not token:
        return create_failure_dict(msg=u'token获取失败')
    try:
        t = models.Token.objects.get(token_type='lesson_start', value=token)
        info = json.loads(t.info)
        c = models.Class.objects.get(uuid=info['class'])
    except Exception as e:
        if DEBUG:
            traceback.print_exc()
        return create_failure_dict(msg='错误的token', debug=str(e))

    # 通过token登录的,会先检测欲登录的班级的状态
    # 若已经登录上课,且属于该客户端的操作,则直接返回对应信息
    # 若已经登录上课,且属于另外客户端的操作,则返回上课失败提示信息
    # 若未登录上课,则通过该token登录上课
    started, log = c.get_status()
    if started:
        token_created_at = info.get('token_created_at', '-NO-UUID-')
        try:
            tag = models.TeacherLoginLogTag.objects.filter(bind_to=log)
            if tag.exists():
                place = tag[0].created_at  # 电脑教室
            else:
                place = log.class_uuid  # 普通班级
        except:
            place = log.class_uuid
        if token_created_at != place.uuid:
            t.delete()
            return create_failure_dict(msg='已在[%s]登录上课中.' % place)

        t.delete()
        return create_success_dict(data={
            'started': True,
            'server_time': datetime.datetime.now(),
            'time': log.lesson_period_end_time,
        })

    now = datetime.datetime.now()
    s = parse_time(info['start_time'])
    e = parse_time(info['end_time'])
    if s <= now.time() <= e:  # 上课中
        resource_from = info['resource_from']
        resource_type = info['resource_type']
        lessoncontent = info['lessoncontent']
        teacher = models.Teacher.objects.get(uuid=info['teacher'])
        c = models.Class.objects.get(uuid=info['class'])
        lsn = models.LessonName.objects.get(uuid=info['lesson_name'])
        try:
            lt = models.LessonTeacher.objects.get(
                class_uuid=c,
                lesson_name=lsn,
                teacher=teacher
            )
            lt.finished_time += 1
            lt.save()
        except:
            if DEBUG:
                traceback.print_exc()
            logger.exception('')
        lp = models.LessonPeriod.objects.get(pk=info['lesson_period'])
        log = models.TeacherLoginLog.log_teacher('login',
                                                 teacher=teacher,
                                                 lesson_name=lsn.name,
                                                 class_uuid=c,
                                                 lesson_period=lp,
                                                 resource_from=resource_from,
                                                 resource_type=resource_type,
                                                 lessoncontent=lessoncontent
                                                 )
        _create_logtag(request, log)
        t.delete()
        # 更新课表 Newly updated: V4.3.0
        lesson_period = models.LessonPeriod.objects.get(pk=info['lesson_period'])
        update_lessonschedule(c, lesson_period, lsn)
        return create_success_dict(data={
            'started': True,
            'server_time': now,
            'time': info['end_time'],
        })

    elif now.time() <= s:
        return create_success_dict(data={
            'started': False,
            'server_time': now,
            'time': info['start_time'],
            'token': token,
        })
    else:  # now.time() >= e
        return create_failure_dict(msg='token对应的课程已下课！')


def syllabus_content(request):
    if models.Setting.getvalue('server_type') != 'school':
        return create_failure_dict()
    mac = request.GET.get('mac')
    lesson_name = request.GET.get('lesson_name')
    # 2015-07-17修改,该值变成了uuid这里需要转换一下
    try:
        lesson_name = models.LessonName.objects.get(uuid=lesson_name).name
    except:
        pass

    # edition = request.GET.get('edition')
    try:
        t = models.Term.get_current_term_list()[0]
    except:
        return create_failure_dict(msg='当前没有可用的学期')
    try:
        c = models.Class.objects.get(grade__term=t, classmacv2__mac=mac)
    except:
        # 未申报的班级去电脑教室上课,这时候通过uuid判断
        try:
            c = models.Class.objects.get(uuid=mac)
        except Exception as e:
            return create_failure_dict(msg='不存在的班级', errors=str(e))
    try:
        g = models.SyllabusGrade.objects.get(school_year=t.school_year,
                                             term_type=t.term_type,
                                             grade_name=c.grade.name)
    except:
        return create_failure_dict(msg=u'大纲数据中没有%s年级' % c.grade.name)
    try:
        l = models.SyllabusGradeLesson.objects.get(syllabus_grade=g,
                                                   lesson_name=lesson_name,
                                                   in_use=True
                                                   )
    except:
        msg = u'大纲数据的%s年级没有%s课程' % (c.grade.name, lesson_name)
        return create_failure_dict(msg=msg)

    if not l.in_use:
        return create_failure_dict(msg=u'该课程大纲未启用')

    q = models.SyllabusGradeLessonContent.objects.filter(syllabus_grade_lesson=l)
    q = q.values().order_by('seq', 'subseq')
    q = format_record.syllabus_content_list(q)
    return create_success_dict(data={'records': model_list_to_dict(q)})
