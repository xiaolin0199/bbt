#!/usr/bin/env python
# coding=utf-8
import cPickle
import datetime
import json
import pypinyin
from django.db.models.query import QuerySet
from django.core.cache import cache
from django.utils.dateparse import parse_time
from BanBanTong.db import models
from BanBanTong.utils import is_admin
from BanBanTong.utils import model_list_to_dict
from BanBanTong.utils import RevisedDjangoJSONEncoder
from BanBanTong.utils import get_cache_timeout as cache_config
import cPickle as pickle


get_timeout = cache_config.get_timeout
ONLINE_CACHE_KEY_PREFIX = cache_config.ONLINE_CACHE_KEY_PREFIX
TOTALS_CACHE_KEY_PREFIX = cache_config.TOTALS_CACHE_KEY_PREFIX
SERVER_TYPE = models.Setting.getvalue('server_type')


'''
    # 校:
    class-teacher-online::class-uuid  (1/0, 1/0) 90s
    class-teacher-totals::class-uuid  (1, 10) None

    # 校
    class-teacher-online::grade-uuid  (int, int) 90s
    class-teacher-totals::grade-uuid  (int, int) None

    # 县, 校
    class-teacher-online::school-uuid  (int, int) 90s
    class-teacher-totals::school-uuid  (int, int) None

    class-teacher-detail::school-uuid  {
        'class-uuid1': ('XX年级x班', n), # class_name use_time
        'class-uuid2': ('XX年级x班', n), # class_name use_time
        'class-uuid3': ('XX年级x班', n), # class_name use_time
    } 90s

'''


def _cache(key, value, timeout=None, **extra_items):
    pass


def _set_class_teacher_online(cls, teacher_online=False):
    pass

set_online = _set_class_teacher_online


def _update_class_teacher_online(obj):
    pass

update_online = _update_class_teacher_online


def _set_class_teacher_totals(cls):
    pass

set_totals = _set_class_teacher_totals


def _update_class_teacher_totals(obj):
    pass

update_totals = _update_class_teacher_totals


################################################################################
def set_class_noreport_heartbeat_ip(ip):
    key = 'class_noreport_heartbeat_ip'
    value = cache.get(key)

    if value:
        value = pickle.loads(value)
        if ip not in value:
            value.append(ip)
            # 如果有新IP要加入
            cache.delete(key)
    else:
        value = [ip]

    # 重生成新的CACHE
    if not cache.get(key):
        cache.set(key, pickle.dumps(value), get_timeout(key, 90))

    return value


def set_class_active_time(c, in_computerclass=False):
    '''
        实时概况->班班通全局数据，在线班级cache
    '''
    # 班级在线的条件:
    # * 该班级在本班级打开客户端或者
    # * 该班级在电脑教室登陆上课
    # 若在电脑教室登陆上课,则普通班级不能登陆上课(该流程中标记客户端在线)
    # 这种情况下需要对在普通班级和电脑教室都打开客户端的情况进行处理

    key = 'class-%s-active-time' % c.uuid
    if in_computerclass:
        # 电脑教室处理上课班级的缓存的时候,判断该班级的客户端的状态
        d = cache.get(key)
        if d and isinstance(d, str):
            d = json.loads(d)
        if d and isinstance(d, dict) and d.get('class_client_online', False):
            class_client_online = True
        else:
            class_client_online = False
    else:
        class_client_online = True

    value = json.dumps({
        'province': c.grade.term.school.parent.parent.parent.parent.uuid,
        'city': c.grade.term.school.parent.parent.parent.uuid,
        'country': c.grade.term.school.parent.parent.uuid,
        'town': c.grade.term.school.parent.uuid,
        'school': c.grade.term.school.uuid,
        'grade': c.grade.uuid,
        'class': c.uuid,
        'in_computerclass': in_computerclass,
        'class_client_online': class_client_online
    })
    cache.set(key, value, get_timeout(key, 90))
    return value


def set_teacher_active_time(obj, cc=None):
    '''
        实时概况->班班通全局数据，在线教师cache
    '''
    # obj是TeacherLoginLog
    in_computerclass = cc and True or False
    key = 'teacher-%s-active-time' % obj.teacher.uuid
    value = json.dumps({
        'province': obj.province.uuid,
        'city': obj.city.uuid,
        'country': obj.country.uuid,
        'town': obj.town.uuid,
        'school': obj.school.uuid,
        'grade': obj.grade.uuid,
        'class': obj.class_uuid.uuid,
        'in_computerclass': in_computerclass
    })

    cache.set(key, value, get_timeout(key, 90))
    if cc:
        key = 'computerclass-teacher-%s-active-time' % obj.teacher.uuid
        value = json.dumps({
            'province': obj.province.uuid,
            'city': obj.city.uuid,
            'country': obj.country.uuid,
            'town': obj.town.uuid,
            'school': obj.school.uuid,
            'grade': cc.grade.uuid,
            'class': cc.uuid,
            'in_computerclass': in_computerclass,
            'fake': True
        })
        cache.set(key, value, get_timeout(key, 90))
    return value


class Class(object):

    @staticmethod
    def get_names(uuids):
        # 批量获取Class.name
        k = 'class-all'
        v = cache.get(k)
        if not v:
            q = models.Class.objects.all()
            q = q.values('uuid', 'name', 'number', 'grade__uuid',
                         'teacher__uuid', 'last_active_time')
            v = cPickle.dumps(q, cPickle.HIGHEST_PROTOCOL)
            timeout = get_timeout(k, None)
            if timeout == 'null':
                cache.set(k, v, None)
            else:
                cache.set(k, v, timeout)
        classes = cPickle.loads(v)
        ret = {}
        for g in classes:
            if g['uuid'] in uuids:
                ret[g['uuid']] = g['name']
        return ret


class Grade(object):

    @staticmethod
    def get_names(uuids):
        # 批量获取Grade.name
        k = 'grade-all'
        v = cache.get(k)
        if not v:
            q = models.Grade.objects.all()
            q = q.values('uuid', 'name', 'number', 'term__uuid')
            v = cPickle.dumps(q, cPickle.HIGHEST_PROTOCOL)
            timeout = get_timeout(k, None)
            if timeout == 'null':
                cache.set(k, v, None)
            else:
                cache.set(k, v, timeout)
        grades = cPickle.loads(v)
        ret = {}
        for g in grades:
            if g['uuid'] in uuids:
                ret[g['uuid']] = g['name']
        return ret


class Group(object):

    @staticmethod
    def get(user):
        k = 'group-%s' % user.uuid
        v = cache.get(k)
        if v:
            data = cPickle.loads(v)
            data['cache'] = 'hit'
            return data
        data = {'group': [], 'grade': [], 'cache': 'miss'}
        server_type = models.Setting.getvalue('server_type')
        q = models.Group.objects.all()
        if server_type != 'school':
            if not is_admin(user):
                q = q.filter(uuid__in=user.permitted_groups.all())
        else:
            school = models.Group.objects.filter(group_type='school')
            terms = models.Term.get_current_term_list(school)
            grades = models.Grade.objects.filter(term__in=terms)
            grades = grades.values('uuid', 'name', 'term__school__uuid')
            data['grade'] = model_list_to_dict(grades)
        q = q.values('uuid', 'name', 'group_type', 'parent__uuid')
        data['group'] = model_list_to_dict(q)
        for d in data['group']:
            py = pypinyin.pinyin(d['name'], pypinyin.FIRST_LETTER)
            d['first_letter'] = ''.join([i[0] for i in py])
            py = ' '.join(pypinyin.lazy_pinyin(d['name'], pypinyin.TONE2))
            d['pinyin'] = py
        cache.set(k, cPickle.dumps(data, cPickle.HIGHEST_PROTOCOL), get_timeout(k, None))
        return data

    @staticmethod
    def get_names(uuids):
        # 批量获取Group.name
        k = 'group-all'
        v = cache.get(k)
        if not v:
            q = models.Group.objects.all()
            q = q.values('uuid', 'name', 'group_type', 'parent__uuid')
            v = cPickle.dumps(q, cPickle.HIGHEST_PROTOCOL)
            cache.set(k, v, get_timeout(k, None))
        groups = cPickle.loads(v)
        ret = {}
        for g in groups:
            if g['uuid'] in uuids:
                ret[g['uuid']] = g['name']
        return ret

    @staticmethod
    def reset(user):
        k = 'group-%s' % user.uuid
        cache.delete(k)
        Group.get(user)


class LessonSchedule(object):

    @staticmethod
    def get_current(c):
        # 从缓存里查找数据，如果没有缓存，就更新一下
        try:
            now = datetime.datetime.now()
            weekday = now.strftime('%a').lower()
            k = 'lessonschedule-%s-%s' % (c.uuid, weekday)
            v = cache.get(k)
            if not v:
                LessonSchedule.update_class_weekday(c.grade.name,
                                                    c.name,
                                                    weekday)
                v = cache.get(k)
            is_current = False
            ls = None
            for i in json.loads(v):
                s = parse_time(i['lesson_period__start_time'])
                e = parse_time(i['lesson_period__end_time'])
                if s <= now.time() <= e:
                    is_current = True
                    ls = i
                    break
            if not ls:
                for i in json.loads(v):
                    s = parse_time(i['lesson_period__start_time'])
                    e = parse_time(i['lesson_period__end_time'])
                    # if e < now.time():
                    if s >= now.time():
                        ls = i
                        break
            return is_current, ls
        except Exception as e:
            return False, None

    @staticmethod
    def update_class_weekday(grade_name, class_name, weekday):
        '''
        lessonschedule-class-week: [
            {
                'lesson_name__name': 'fdsfds',
                'lesson_period__sequence': 1,
                'lesson_period__start_time': 'hh:mm:ss',
                'lesson_period__end_time': 'hh:mm:ss',
            },
            {...}, {...},
        ]
        '''
        try:
            term = models.Term.get_current_term_list()[0]
        except:
            return
        try:
            c = models.Class.objects.get(grade__term=term,
                                         grade__name=grade_name,
                                         name=class_name)
        except:
            return
        q = models.LessonSchedule.objects.all()
        q = q.filter(class_uuid=c, weekday=weekday)
        k = 'lessonschedule-%s-%s' % (c.uuid, weekday)
        cache.delete(k)
        q = q.filter(weekday=weekday).values(
            'uuid',
            'lesson_name__name',
            'lesson_period__uuid',
            'lesson_period__sequence',
            'lesson_period__start_time',
            'lesson_period__end_time')
        q = q.order_by('lesson_period__sequence')
        v = json.dumps(model_list_to_dict(q), cls=RevisedDjangoJSONEncoder)
        cache.set(k, v, get_timeout(k, 60 * 60 * 24))

    @staticmethod
    def update_class(grade_name, class_name):
        '''校级服务器导入班级课程表之后刷新缓存'''
        weekdays = [i[0] for i in models.WEEK_KEYS]
        for weekday in weekdays:
            LessonSchedule.update_class_weekday(grade_name, class_name, weekday)


class LessonTeacher(object):

    @staticmethod
    def get_teachers_lessons(class_uuid):
        q = models.LessonTeacher.objects.filter(class_uuid=class_uuid)
        q = q.values('teacher__uuid', 'teacher__name', 'lesson_name__name')
        ret = model_list_to_dict(q)
        return ret

        key = 'simplecache_lesson_teacher_%s' % class_uuid.uuid
        c = cache.get(key)
        if c:
            ret = json.loads(c)
        else:
            q = models.LessonTeacher.objects.filter(class_uuid=class_uuid)
            q = q.values('teacher__uuid', 'teacher__name', 'lesson_name__name')
            ret = model_list_to_dict(q)
            cache.set(key, json.dumps(ret), get_timeout(key, None))
        return ret

    @staticmethod
    def update(class_uuid=None):
        def _update(uu):
            key = 'simplecache_lesson_teacher_%s' % uu
            cache.delete(key)
            q = models.LessonTeacher.objects.filter(class_uuid=uu)
            q = q.values('teacher__uuid', 'teacher__name', 'lesson_name__name')
            ret = model_list_to_dict(q)
            cache.set(key, json.dumps(ret), get_timeout(key, None))

        return
        if class_uuid:
            _update(class_uuid)
        else:
            q = models.LessonTeacher.objects.all()
            q = q.order_by().values_list('class_uuid', flat=True).distinct()
            for i in q:
                _update(i)


class Resource(object):

    @staticmethod
    def get():
        key = 'simplecache_resource'
        c = cache.get(key)
        if c:
            ret = json.loads(c)
        else:
            q = models.Resource.objects.values('resource_from').distinct()
            ret = model_list_to_dict(q)
            cache.set(key, json.dumps(ret), get_timeout(key, None))
        return ret

    @staticmethod
    def update():
        key = 'simplecache_resource'
        cache.delete(key)
        q = models.Resource.objects.values('resource_from').distinct()
        l = model_list_to_dict(q)
        cache.set(key, json.dumps(l), get_timeout(key, None))


class Term(object):

    @staticmethod
    def update_current(school=None):
        now = datetime.datetime.now()
        ret = []
        if school is None:
            school = models.Group.objects.filter(group_type='school')
        if isinstance(school, models.Group):
            q = Term.__class__filter(start_date__lte=now, end_date__gte=now,
                                     school=school)
            if q.exists():
                ret.append(q[0])
            else:
                q = Term.objects.filter(start_date__gt=now)
                if q.exists():
                    ret.append(q[0])
        elif isinstance(school, QuerySet):
            for i in school:
                ret.extend(Term.update_current(i))

    @staticmethod
    def get_current_term_list(node_uuid, school=None):
        # k = 'current-terms-for-uuid-%s' % node_uuid
        # v = cache.get(k)
        # if v:
        #     uuids = json.loads(v)
        #     return models.Term.objects.filter(uuid__in=uuids)
        # else:
        #     ret = models.Term.get_current_term_list(school)
        #     uuids = [i.uuid for i in ret]
        #     cache.set(k, json.dumps(uuids), 7200)
        #     return ret

        ret = models.Term.get_current_term_list(school)
        return ret
