# coding=utf-8
# client.py
import datetime
import json
from BanBanTong.db import models
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import create_failure_dict
from django.conf import settings
DEBUG = settings.DEBUG
del settings


def get_client_status(request, *args, **kwargs):
    """客户端状态获取"""
    mac = request.GET.get('mac')
    term = models.Term.get_current_term_list()
    server_type = models.Setting.getvalue('server_type')
    if server_type != 'school':
        return create_failure_dict(msg=u'未找到服务器/错误的服务器类型.')
    if not term:
        return create_failure_dict(msg=u'学期尚未开始或已经结束.')
    if not mac:
        return create_failure_dict(msg=u'参数获取失败.', debug='no mac found')
    objs = models.ClassMacV2.objects.filter(
        mac=mac,
        class_uuid__grade__term__in=term
    )
    if not objs.exists():
        return create_failure_dict(msg=u'客户端尚未申报.')
    if objs.count() != 1:
        return create_failure_dict(
            msg=u'客户端存在重复绑定现象,当前已绑定班级数: %s.' % objs.count()
        )

    cls = objs[0].class_uuid
    is_started, log = cls.get_status()
    obj = cls.grade.number != 13 and \
        models.Statistic.objects.get(key=cls.pk) or None
    now = datetime.datetime.now()
    lp = models.LessonPeriod.get_current_or_next_period()
    tag = DEBUG and 'x' or ''
    data = {
        'status': 'unstarted',
        'sequence': lp and lp.sequence or None,
        'server_time': now.strftime('%Y-%m-%d %H:%M:%S'),
        'start_time': lp and lp.start_time or None,
        'end_time': lp and lp.end_time or None,
        'runtime': 0,
    }

    # 需求上面的几个模糊的参数,放在这里扩展注释一下,以免读的云里雾里.
    # finished_lesson 本班级本课程实际授课次数
    # schedule_lesson 本班级本课程计划授课次数
    # finished_all    本教师所有课程实际授课次数
    # schedule_all    本教师所有课程计划授课次数
    # finished        本班实际授课次数
    # schedule        本班计划授课次数
    # rank_school     本班已授课时在全校的排名
    # rank_grade      本班已授课时在年级的排名
    # rank_lesson

    # 已登录
    if is_started:
        if cls.grade.number == 13:
            cls = log.class_uuid
            obj = models.Statistic.objects.get(key=cls.pk)
        dl = cls.get_lesson_schedule_info(log.lesson_name)
        # dl_all1 = cls.get_lesson_schedule_info()
        dl_all = models.LessonTeacher.get_info
        if hasattr(log, 'teacherlogintime') and log.teacherlogintime:
            runtime = log.teacherlogintime.login_time
        elif hasattr(log, 'teacherlogintimetemp') and log.teacherlogintimetemp:
            runtime = log.teacherlogintimetemp.login_time
        else:
            runtime = 0

        lessoncontent_title = u'其它'
        lessoncontent = -1
        if hasattr(log, 'teacherloginloglessoncontent') and \
                log.teacherloginloglessoncontent.lessoncontent:
            lessoncontent_title = log.teacherloginloglessoncontent.lessoncontent.title
            lessoncontent = log.teacherloginloglessoncontent.lessoncontent.id

        data.update({
            # Current client status
            'status': 'started',
            'runtime': runtime,
            # The base info of current class/lesson
            'class_name': u'%s年级%s班' % (cls.grade.name, cls.name),
            'teacher_name': log.teacher_name,
            'lesson_name': log.lesson_name,
            'resource_from': log.resource_from,
            'resource_type': log.resource_type,
            'lessoncontent': lessoncontent,
            'lessoncontent_title': lessoncontent_title,
            # The progress of the course
            'finished_lesson': dl.get('finished_time', tag),
            'schedule_lesson': dl.get('schedule_time', tag),
            # 'finished_all': dl_all.get('finished_time', tag), # 本班所有课程实际授课次数
            # 'schedule_all': dl_all.get('schedule_time', tag), # 本班所有课程计划授课次数
            'finished_all': dl_all('finished_time', teacher=log.teacher, term=log.term),
            'schedule_all': dl_all('schedule_time', teacher=log.teacher, term=log.term),
            'finished': obj.teach_count,
            'schedule': obj.get_schedule_time(),

            # The rank of the class
            'rank_school': cls.rank('school'),
            'rank_grade': cls.rank('grade'),
            'rank_lesson': cls.rank('lesson', lesson_name=log.lesson_name),
        })

    # 预登陆
    else:
        models.Token.clean_bad_tokens('lesson_start')
        tokens = models.Token.objects.filter(token_type='lesson_start')
        if tokens.exists():
            for token in tokens:
                d = json.loads(token.info)
                if cls.pk in (d['class'], d['token_created_at']):
                    cls = models.Class.objects.get(pk=d['class'])
                    obj = models.Statistic.objects.get(key=cls.pk)
                    dl = cls.get_lesson_schedule_info(d['lesson_name__name'])
                    # dl_all = cls.get_lesson_schedule_info()
                    dl_all = models.LessonTeacher.get_info

                    lessoncontent_title = u'其它'
                    if d['lessoncontent'] > 0:
                        try:
                            lessoncontent_title = models.SyllabusGradeLessonContent.objects.get(id=d['lessoncontent']).title
                        except Exception:
                            #lessoncontent_title = lessoncontent
                            pass

                    data.update({
                        'status': 'starting',
                        'class_name': u'%s年级%s班' % (cls.grade.name, cls.name),
                        'teacher_name': d['teacher_name'],
                        'lesson_name': d['lesson_name__name'],
                        'resource_from': d['resource_from'],
                        'resource_type': d['resource_type'],
                        #'lessoncontent': d['lessoncontent'] != -1 and \
                        #    d['lessoncontent'] or u'其他',
                        'lessoncontent': d['lessoncontent'],
                        'lessoncontent_title': lessoncontent_title,
                        'finished_lesson': dl.get('finished_time', tag),
                        'schedule_lesson': dl.get('schedule_time', tag),
                        # 'finished_all': dl_all.get('finished_time', tag),
                        # 'schedule_all': dl_all.get('schedule_time', tag),
                        'finished_all': dl_all('finished_time', teacher=d['teacher']),
                        'schedule_all': dl_all('schedule_time', teacher=d['teacher']),
                        'finished': obj.teach_count,
                        'schedule': obj.get_schedule_time(),

                        'rank_school': cls.rank('school'),
                        'rank_grade': cls.rank('grade'),
                        'rank_lesson': cls.rank('lesson', lesson_name=d['lesson_name__name']),
                    })

    # 未登录
    if data['status'] == 'unstarted':
        if lp:
            d = cls.get_lesson_info()
            if cls.grade.number != 13:
                class_name = u'%s年级%s班' % (cls.grade.name, cls.name)
            else:
                class_name = u'%s(%s)' % (cls.name, cls.grade.name)
            dl = cls.get_lesson_schedule_info(d['lesson_name'])
            dl_all = cls.get_lesson_schedule_info()
            data.update({
                'class_name': class_name,
                'teacher_name': d['teacher_name'],
                'lesson_name': d['lesson_name'],

                'rank_school': obj and cls.rank('school') or tag,
                'rank_grade': obj and cls.rank('grade') or tag,
                # 'rank_lesson': obj and cls.rank('lesson', lesson_name=d['lesson_name']) or tag, # 课程排名

                'finished_lesson': dl.get('finished_time', tag),
                'schedule_lesson': dl.get('schedule_time', tag),
                'finished_all': dl_all.get('finished_time', tag),
                'schedule_all': dl_all.get('schedule_time', tag),
                'finished': obj and obj.teach_count or tag,
                'schedule': obj and obj.get_schedule_time() or tag,
            })

    return create_success_dict(data=data)


def clean_token(request, *args, **kwargs):
    """客户端取消当前的登录操作,清除掉本次登录产生的token"""
    client_mac = request.GET.get('mac')
    term = models.Term.get_current_term_list()
    if not term:
        return create_failure_dict(msg=u'无可用学年学期.', debug='no term')
    cls = models.ClassMacV2.objects.filter(
        mac=client_mac,
        class_uuid__grade__term=term[0]
    )
    if not cls.exists():
        return create_failure_dict(msg=u'客户端尚未申报.', debug='not reported')

    uuid = str(cls[0].class_uuid.pk).lower().replace('-', '')
    models.Token.objects.filter(
        token_type='lesson_start',
        value=uuid
    ).all().delete()
    return create_success_dict(debug=uuid)

    # 前端要求这里只传递MAC地址,所以换成上面的清理方法.
    token_key = request.GET.get('token')
    if token_key:
        tokens = models.Token.objects.filter(token_type='lesson_start', value=token_key)
        tokens.all().delete()
        return create_success_dict(debug=token_key)
    return create_failure_dict(msg=u'参数获取失败.', debug='token')
