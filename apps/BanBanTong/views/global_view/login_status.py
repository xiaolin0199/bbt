#!/usr/bin/env python
# coding=utf-8
import datetime
from django.core.cache import cache
from BanBanTong.db import models
from BanBanTong.utils import decorator
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import str_util


def _get_login_status(c, now, lp):
    '''获取指定班级的登录状态（X年级X班、是否在线、课程名、登录时长）'''
    ret = {'grade_name': c.grade.name, 'class_name': c.name,
           'online': False, 'lesson_name': '', 'login_time': 0}
    # cache内有状态（90秒内活动）的班级都判定为在线
    key = 'class-%s-active-time' % c.uuid
    value = cache.get(key)
    if value:
        ret['online'] = True
    # 获取当前课程
    try:
        s = datetime.datetime.combine(now.date(), lp.start_time)
        e = datetime.datetime.combine(now.date(), lp.end_time)
        tl = models.TeacherLoginLog.objects.get(lesson_period=lp,
                                                class_uuid=c,
                                                created_at__range=(s, e))
        ret['lesson_name'] = tl.lesson_name
    except:
        return ret
    # 从cache获取使用时长
    key = 'class-%s-teacherlogintime' % c.uuid
    value = cache.get(key)
    if value:
        ret['login_time'] = value
    return ret


def _sort_records(a, b):
    grade_a = str_util.grade_name_to_number(a['grade_name'])
    grade_b = str_util.grade_name_to_number(b['grade_name'])
    if grade_a != grade_b:
        return grade_a - grade_b
    else:
        class_a = str_util.class_name_to_number(a['class_name'])
        class_b = str_util.class_name_to_number(b['class_name'])
        return class_a - class_b


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('global_login_status')
def list_class(request, *args, **kwargs):
    uu = request.GET.get('uuid')
    computerclass_need = request.GET.get('computerclass_need', False)
    try:
        school = models.Group.objects.get(uuid=uu, group_type='school')
    except:
        try:
            school = models.Group.objects.get(group_type='school')
        except:
            return create_failure_dict(msg='错误的uuid')
    # print school
    try:
        term = models.Term.get_current_term_list(school)[0]
    except:
        return create_failure_dict(msg='当前时间不在任何学期内')
    # print term
    q = models.Class.objects.filter(grade__term=term)
    if not computerclass_need:
        q = q.exclude(grade__number=13)
    records = []
    now = datetime.datetime.now()
    # print now
    try:
        lp = models.LessonPeriod.objects.get(term=term,
                                             start_time__lte=now.time(),
                                             end_time__gte=now.time())
    except:
        lp = None
    # print 'lp:', lp
    for i in q:
        records.append(_get_login_status(i, now, lp))
    data = {'records': sorted(records, _sort_records)}
    if lp:
        data['lesson_period'] = {'sequence': lp.sequence,
                                 'start_time': lp.start_time,
                                 'end_time': lp.end_time}
    return create_success_dict(data=data)
