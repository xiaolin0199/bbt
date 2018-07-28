# coding=utf-8
import datetime
import traceback
import logging
import cPickle
from django.core.cache import cache
from BanBanTong.db import models
from BanBanTong.utils import simplecache
from BanBanTong.utils import model_list_to_dict
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils.get_cache_timeout import get_timeout
from BanBanTong.views.api.interfaces.lesson import update_time_used
from django.conf import settings
DEBUG = settings.DEBUG


logger = logging.getLogger(__name__)


def get_defaultlesson(cls_pk):
    """
    获取指定班级当前节次的默认课程/教师
    """
    d = {
        'lesson': {'key': '', 'text': ''},
        'teacher': {'key': '', 'text': ''},
        '#debug': 'no errors'
    }
    try:
        cls = models.Class.objects.get(pk=cls_pk)
        lp = models.LessonPeriod.get_current_or_next_period()
        if not lp:
            return d
    except Exception as e:
        if DEBUG:
            traceback.print_exc()
        d['#debug'] = str(e)
        return d
    try:
        week = datetime.datetime.now().strftime('%a').lower()
        o = cls.lessonschedule_set.get(
            lesson_period=lp,
            weekday=week
        )
        thr = cls.lessonteacher_set.filter(lesson_name=o.lesson_name)
        t = thr[0]
    except Exception as e:
        if DEBUG:
            traceback.print_exc()
        d['#debug'] = str(e)
        return d
    d.update({
        'lesson': {'key': o.lesson_name.pk, 'text': o.lesson_name.name},
        'teacher': {'key': t.teacher.pk, 'text': t.teacher.name}
    })
    return d


def get_lessonteacher(cls, lesson_name):
    lst = cls.lessonteacher_set.filter(lesson_name=lesson_name)
    lst = lst.values(
        'teacher', 'lesson_name',
        'teacher__name', 'teacher__birthday'
    ).distinct()
    lst = list(lst)
    # d = {}
    # for o in lst[:]:
    #     if not d.has_key(o['lesson_name']):
    #         d[o['lesson_name']] = [lst.index(o)]
    #     else:
    #         d[o['lesson_name']].append(lst.index(o))
    #
    # for k in d:
    #     if len(d[k]) > 1:
    #         for i in d[k]:
    #             v = lst[i]
    #             vv = '%s(%s)' % (
    #                 v['teacher__name'],
    #                 v['teacher__birthday'].strftime('%m%d'))
    #             lst[i]['teacher__name'] = vv
    return lst


# V4.3.0
# /api/grade-class/
def get_grade_class(request, *args, **kwargs):
    """
    电脑教室登录上课前需要先选定年级班级,然后才能获取对应的课程表
    课表获取原则是:
    选定年级班级->获取选中班级的课表->筛选出能在电脑教室里面上的教室-课程信息
    """
    mac = request.GET.get('mac')
    if not mac:
        return create_failure_dict(msg=u'MAC地址获取失败')

    terms = models.Term.get_current_term_list()
    if not terms:
        return create_failure_dict(msg=u'当前时间不在任何学期内')

    objs = models.ClassMacV2.objects.filter(
        mac=mac,
        class_uuid__grade__term__in=terms
    )
    if objs.count() != 1:
        return create_failure_dict(
            msg=u'客户端尚未申报或数据异常',
            debug=objs.count()
        )

    o = objs[0].class_uuid

    # Define
    _get_class = lambda grd: grd.class_set.all()
    _get_lesson = lambda cls, range: cls.lessonteacher_set.filter(
        lesson_name__in=range
    ).values('lesson_name', 'lesson_name__name').distinct()
    _get_default = lambda cls_pk: get_defaultlesson(cls_pk)

    cache_key = 'grade_class_lesson_teacher::%s' % o.pk
    cached_value = cache.get(cache_key)
    if cached_value:
        data = cPickle.loads(cached_value)
        for ginfo in data:
            for cinfo in ginfo['class']:
                cinfo['default'] = _get_default(cinfo['key'])
        return create_success_dict(data=data, debug='from cache')

    if o.grade.number == 13:
        grade = models.Grade.objects.filter(term__in=terms).exclude(number=13)
        grade = grade.order_by('number')
        lsn = o.computerclass.computerclasslessonrange_set
        lst = lsn.values_list('lessonname', flat=True)
        data = map(lambda g: {
            'key': g.pk,
            'text': u'%s年级' % g.name,
            'class': map(lambda c: {
                'default': _get_default(c.pk),
                'key': c.pk,
                'text': c.name,
                'lesson': map(lambda lt: {
                    'key': lt['lesson_name'],
                    'text': lt['lesson_name__name'],
                    'teacher': map(lambda ltt: {
                        'key': ltt['teacher'],
                        'text': ltt['teacher__name']
                    }, get_lessonteacher(c, lt['lesson_name']))
                }, _get_lesson(c, lst))
            }, _get_class(g))
        }, grade)

    else:
        data = [{
            'key': o.grade.pk,
            'text': u'%s年级' % o.grade.name,
            'class': [{
                'default': _get_default(o.pk),
                'key': o.pk,
                'text': o.name,
                'lesson': map(lambda lt: {
                    'key': lt['lesson_name'],
                    'text': lt['lesson_name__name'],
                    'teacher': map(lambda ltt: {
                        'key': ltt['teacher'],
                        'text': ltt['teacher__name']
                    }, get_lessonteacher(o, lt['lesson_name']))
                }, o.lessonteacher_set.values(
                    'lesson_name',
                    'lesson_name__name'
                ).distinct())
            }]
        }]
    if not DEBUG:
        cache.set(
            cache_key,
            cPickle.dumps(data, cPickle.HIGHEST_PROTOCOL),
            get_timeout(cache_key, 60 * 45)
        )
    return create_success_dict(data=data)


################################################################################
def _get_class_teacher_lessons(lr, cuus):
    """在指定电脑教室上课班级的的所有的授课教师的信息
    d = {'class_uuid1': {
            'teacher_uuid1':{'lesson_uuid1':'lesson_name1', 'lesson_uuid2':'lesson_name2'},
            'teacher_uuid2':{'lesson_uuid1':'lesson_name3', 'lesson_uuid3':'lesson_name4'},
        },
        'class_uuid2': {...},
    }
    """
    def __t(class_uuid):
        # 从LessonTeacher表获取指定班级的授课教师
        base = lt.filter(class_uuid=class_uuid)
        return list(set(base.values_list('teacher', flat=True)))

    def __l(class_uuid, teacher_uuid):
        # 从LessonTeacher表获取指定班级,授课教师的课程
        base = lt.filter(class_uuid=class_uuid, teacher=teacher_uuid)
        return list(set(base.values_list('lesson_name', flat=True)))

    def __set(lu, lst):
        x = []
        for luu, tu in lst:
            if luu == lu:
                x.append(tu)
        return list(set(x))
    lt = models.LessonTeacher.objects
    lt = lt.filter(class_uuid__in=cuus, lesson_name__in=lr)
    teachers = dict(lt.values_list('teacher', 'teacher__name', flat=False))
    lessons = dict(lt.values_list('lesson_name', 'lesson_name__name', flat=False))
    lts = lt.values_list('lesson_name', 'teacher', flat=False)
    dlt = {lu: __set(lu, lts) for lu in lr}
    # d = {c: {t: {l:{teachers[t]:lessons[l]}
    d = {c: {t: {l: lessons[l]  # 2014-12-24 修改了一下第三级的数据结构
                 for l in __l(c, t)}  # 该班级教师的课程
             for t in __t(c)}  # 该班级的教师
         for c in cuus}  # 班级
    return d, teachers, lessons, dlt


def _format(c, dctl, dt, dl, lesson_uuid=None):
    """格式化输出指定班级的的授课教师-课程信息"""
    ret, d_teacher_lessons = [], dctl.get(c.uuid, [])
    for teacher_uuid in d_teacher_lessons:
        d_lessons = list(d_teacher_lessons[teacher_uuid])
        # 如果指定了课程的话,那么只返回该班级指定课程的信息(即按课程表推送)
        if lesson_uuid and not lesson_uuid in d_lessons:
            continue
        ret.append({  # '#tag': '%s-%s' %(c.grade.number, c.number),
            'key': teacher_uuid,
            'text': dt.get(teacher_uuid, u''),
            'lessons': [{'key': dl.get(lu, u''),
                         'text': dl.get(lu, u'')} for lu in d_lessons]})
    return ret


def _get_last_logs():
    """当前节次的教师登录记录"""
    today = datetime.datetime.now().date()
    s = datetime.datetime.combine(today, datetime.time.min)
    e = datetime.datetime.combine(today, datetime.time.max)
    lp = models.LessonPeriod.get_current_or_next_period()
    if not lp:
        return []
    logs = models.TeacherLoginLog.objects
    logs = logs.filter(lesson_period=lp, created_at__range=(s, e))
    if logs.exists():
        return logs
    return []


def _praser(lst):
    d = {}
    for tu, tn, lu, ln in lst:
        if not tu in d:
            # d[tu] = {'key':tu, 'text':tn, 'lessons':[{'key': ln, 'text': ln},]}
            d[tu] = {'key': tn, 'text': tn, 'lessons': [{'key': ln, 'text': ln}, ]}
            continue
        if not {'key': ln, 'text': ln} in d[tu]['lessons']:
            d[tu]['lessons'].append({'key': ln, 'text': ln})
    return [d[i] for i in d]


def get_current_or_nextlesson(request, *args, **kwargs):
    """客户端获取电脑教室当前或下一节课的课程信息"""
    mac = request.GET.get('mac')
    # flag = request.GET.get('in_computerclass')
    if models.Setting.getvalue('server_type') != 'school':
        return create_failure_dict(msg='客户端应当连接校级服务器')
    if not mac:
        return create_failure_dict(msg='获取电脑教室Mac失败')
    lp = models.LessonPeriod.get_current_or_next_period()
    if not lp:
        return create_failure_dict(msg='今天的课程已经上完')

    t = models.Term.get_current_term_list()[0]
    u = models.Class.objects.get(classmacv2__mac=mac, grade__term=t).uuid
    cc = models.ComputerClass.objects.get(class_bind_to=u)
    ls = cc.get_curriculum()
    if not ls.exists():
        return create_failure_dict(msg='本教室授课范围内无可使用班级')

    rf = cache.get('resource_from_for_%s' % mac)
    rt = cache.get('resource_types_for_%s' % mac)
    if not rf:
        rf = models.ResourceFrom.objects.values_list('value', flat=True)
        rf = [{'key': i, 'text': i} for i in rf]
        key = 'resource_from_for_%s' % mac
        cache.set(key, rf, get_timeout(key, 60 * 45))
    if not rt:
        rt = models.ResourceType.objects.values_list('value', flat=True)
        rt = [{'key': i, 'text': i} for i in rt]
        key = 'resource_types_for_%s' % mac
        cache.set(key, rt, get_timeout(key, None))

    lr = cc.lesson_range.all().values_list('uuid', flat=True)
    cuus = list(set(ls.values_list('class_uuid', flat=True)))
    lt = models.LessonTeacher.objects.filter(lesson_name__in=lr, class_uuid__in=cuus)

    all_teachers = lt.values_list('teacher__uuid', 'teacher__name',
                                  'lesson_name', 'lesson_name__name', flat=False)

    now = datetime.datetime.now()
    wk = now.strftime('%a').lower()
    ls_name = ls.filter(lesson_period=lp.uuid, weekday=wk)
    ls_name = list(set(ls_name.values_list('lesson_name', flat=True)))
    current_teachers = lt.filter(lesson_name__in=ls_name)
    current_teachers = current_teachers.values_list('teacher__uuid', 'teacher__name',
                                                    'lesson_name', 'lesson_name__name', flat=False)

    data = {'status': False}  # , 'lesson': [], 'teacher': []}
    data['resource_from'] = rf
    data['resource_types'] = rt
    data['all_teachers'] = _praser(all_teachers)
    data['lesson'] = _praser(current_teachers)

    started, log = cc.get_status()
    if started:
        data['status'] = True
        lesson = models.LessonName.objects.get(name=log.lesson_name)
        data['info'] = {
            'teacher_key': log.teacher.uuid,
            'password': log.teacher.password,
            'lesson_key': lesson.uuid,
            'resource_from': log.resource_from,
            'resource_types': log.resource_type,
            'server_time': now,
            'time': log.lesson_period_end_time,
            'class_uuid': log.class_uuid.uuid,
            'class_mac': log.class_uuid.mac()
        }
    return create_success_dict(data=data)


# api/computer-class/classes/
def get_baseinfo(request, *args, **kwargs):
    """客户端获取当天课程信息,当前节次课程信息"""
    mac = request.GET.get('mac')
    if models.Setting.getvalue('server_type') != 'school':
        return create_failure_dict()
    if not mac:
        return create_failure_dict(msg='获取客户端Mac地址失败')
    lp = models.LessonPeriod.get_current_or_next_period()
    if not lp:
        return create_failure_dict(msg='今天的课程已经上完')

    t = models.Term.get_current_term_list()[0]
    c = models.Class.objects.filter(classmacv2__mac=mac, grade__term=t)
    cc = models.ComputerClass.objects.get(class_bind_to=c)

    # 获取当天剩余的课程信息
    ls = cc.get_curriculum(today=True).filter(lesson_period__sequence__gte=lp.sequence)
    if not ls.exists():
        return create_failure_dict(msg='本教室今天的课程已经上完')

    # 获取当前节次已经登录的教师登录记录
    logs = _get_last_logs()  # QuertSet or []
    if logs:
        logs = list(set(logs.values_list('class_uuid', flat=True)))

    # 剔除掉当前节次已经登录的班级
    # ls = ls.filter(lesson_period=lp) ## 暂时性的修复一个bug
    ls = ls.exclude(class_uuid__in=logs)
    if not ls.exists():
        return create_failure_dict(msg='本教室当前节次无可用班级')

    # 从剩余的课程中获取当前或即将到来的课程信息
    sequence = lp.sequence
    next = ls.filter(lesson_period__sequence=sequence)
    while not next.exists():
        sequence += 1
        next = ls.filter(lesson_period__sequence=sequence)

    # 获取剩余的'班级-教师-课程'信息
    uuids = list(set(ls.values_list('class_uuid', flat=True)))
    lr = cc.lesson_range.all().values_list('uuid', flat=True)
    dctl, dt, dl, dlt = _get_class_teacher_lessons(lr, uuids)
    defaults = {}
    for i in next:
        # 该班级的授课教师-课程
        dtl = dctl.get(i.class_uuid.uuid, {})
        # 能授该课的教师
        tuus = dlt.get(i.lesson_name.uuid, ['no uuid'])
        tu = ''
        # 获取能上当前课程的属于该班级的授课教师
        for tuu in tuus:
            if tuu in dtl:
                tl = dtl.get(tuu, {})
                # 如果该班级的该教师分配过当前的课程
                if tl.has_key(i.lesson_name.uuid):
                    tu = tuu
                    break

        defaults['%s%s' % (i.class_uuid.grade.uuid, i.class_uuid.uuid)] = {
            '#key': tu and dt.get(tu, '') or u'',
            # 'key': tu and tu or u'No Teacher For This Lesson',
            # 'text': tu and dt.get(tu, 'no name')  or u'尚未分配授课教师',
            'key': tu,
            'text': tu and dt.get(tu, '') or '',
            'lesson_uuid': i.lesson_name.uuid,
            # 前端要求课程信息的key和text都是课程名字
            'lessons': {'key': i.lesson_name.name, 'text': i.lesson_name.name}
        }
        if DEBUG:
            defaults['%s%s' % (i.class_uuid.grade.uuid, i.class_uuid.uuid)].update({
                '#debug': 'key start wit # is for debug',
                '#tag': '%s-%s' % (i.class_uuid.grade.number, i.class_uuid.number),
                '#sequence': i.lesson_period.sequence,
                '#time': '%s-%s' % (i.lesson_period.start_time, i.lesson_period.end_time),
            })

    info = models.Class.objects.filter(uuid__in=uuids).order_by('grade__number',
                                                                'number')

    data = []
    # null = {'key': u'', 'text': u'', 'lessons': {'key': '', 'text': ''}}
    for c in info:
        # df = defaults.get(str(c.grade.uuid+c.uuid), null)
        df = defaults.get(str(c.grade.uuid + c.uuid), None)
        if not df:
            continue
        data.append({
            '#tag': u'%s-%s' % (c.grade.number, c.number),
            'grade_uuid': c.grade.uuid,
            'class_uuid': c.uuid,
            'name': u'%s年级%s班' % (c.grade, c),
            'mac': c.mac(),
            # 原始需求,要求推送当天的课程信息
            # V1
            # 'teacher': _format(c, dctl, dt, dl), # 课程不指定则推送全部

            # 要只推送当前节次的
            # V2
            # 'teacher': [{'key': df['key'],
            #              'text': df['text'],
            #              'lessons': [df['lessons'], ]}, ],

            # 要只推送当前节次的(能上课的老师也得有)
            # V3
            'teacher': _format(c, dctl, dt, dl, df['lesson_uuid']),
            'default': df
        })
    return create_success_dict(data=data)


# api/computer-class/all/
def get_unreported(request, *args, **kwargs):
    """客户端获取未申报的电脑教室列表"""
    if models.Setting.getvalue('server_type') != 'school':
        return create_failure_dict()
    term = models.Term.get_current_term_list()
    if not term:
        return create_failure_dict(msg='当前时间不在任何学期内')
    t = term[0]
    cc = models.ComputerClass.objects.filter(class_bind_to__grade__term=t)
    if cc.exists():
        uuids = models.ClassMacV2.objects.all().values_list('class_uuid', flat=True)
        cc = cc.exclude(class_bind_to__in=uuids).order_by(
            'class_bind_to__name',
            'class_bind_to__number').values_list(
            'class_bind_to',
            'class_bind_to__name',
            'class_bind_to__number',
            'class_bind_to__grade__uuid', flat=False)
        data = map(lambda c: {'uuid': c[0], 'name': c[1], 'number': c[2],
                              'grade_uuid': c[3]}, cc)
        return create_success_dict(data=data, term=model_list_to_dict(term))
    return create_success_dict(data=[])


# /api/lesson/status/computer-class/
def get_lessonstatus(request, *args, **kwargs):
    """
    客户端获取当前电脑教室的授课状态
    """
    mac = request.GET.get('mac')
    if models.Setting.getvalue('server_type') != 'school':
        return create_failure_dict()
    if not mac:
        return create_failure_dict(msg='获取客户端Mac地址失败')
    now = datetime.datetime.now()
    term = models.Term.get_current_term_list()
    if not term:
        return create_failure_dict(msg='当前时间不在任何学期内', reported=False)
    t = term[0]
    if not t.start_date <= now.date() <= t.end_date:
        return create_failure_dict(msg='学期尚未开始', reported=False)
    try:
        klass = models.Class.objects.get(classmacv2__mac=mac, grade__term=t)
        cc = models.ComputerClass.objects.get(class_bind_to=klass)
    except:
        return create_failure_dict(msg='当前电脑教室尚未申报', reported=False)

    # 1.标记电脑教室在线
    simplecache.set_class_active_time(klass)
    lp = models.LessonPeriod.get_current_or_next_period()
    if not lp:
        return create_failure_dict(msg='今天的课程已经上完')

    # 2.判断当前电脑教室状态
    # * 已经登录授课,则标记上课班级在线、标记教师在线、更新使用时长
    # * 未登录授课,则返回下一节课的时间(可多选,故不返回课程信息)
    started, log = cc.get_status()
    if started:
        c = log.class_uuid
        simplecache.set_class_active_time(c, True)  # in_computerclass=True
        tmp = update_time_used(c, now)
        if tmp:
            simplecache.set_teacher_active_time(tmp.teacherloginlog, klass)
            key = 'class-%s-teacherlogintime' % c.uuid
            cache.set(key, tmp.login_time, get_timeout(key, 90))

            data = {'status': True, 'current_lesson': {
                'lesson_name': log.lesson_name,
                'start_datetime': log.lesson_period_start_time,
                'end_datetime': log.lesson_period_end_time,
                'grade_number': log.grade.number,
                'class_number': log.class_uuid.number
            }}
            # 若教师在线时长更新失败,说明当前节次的课程已经结束
            return create_success_dict(data=data, timestamp=now)

    if lp.start_time < now.time() < lp.end_time:
        key = 'current_lesson'
    else:
        key = 'next_lesson'
    data = {'status': False, key: {
        'lesson_name': '',
        'start_datetime': lp.start_time,
        'end_datetime': lp.end_time,
        'class_number': '%s' % cc
    }}

    return create_success_dict(data=data, timestamp=now)
