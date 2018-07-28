#!/usr/bin/env python
# coding=utf-8
import cPickle
import datetime
import json
import logging
from django.core.cache import cache
from BanBanTong.db import models
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import is_admin
from BanBanTong.utils import simplecache
from BanBanTong.utils.get_cache_timeout import get_timeout

logger = logging.getLogger(__name__)


'''
    班班通全局数据相关缓存设定
    普通教室和电脑教室在线
    'class-[uuid]-active-time'
    普通班级教师和电脑教室教师在线
    teacher-[uuid]-active-time
    computerclass-teacher-[uuid]-active-time

'''
'''
    TODO 对于校级，用uuid遍历cache；对于县级，由每个学校计算出总数、在线数、离线数并定期上传
    校级：
        type=province/city/country/town，饼图回应学校的整体数据，柱状图回应一条（学校总体）
        type=school，饼图回应学校整体，柱状图回应每个年级
        type=grade，饼图回应这个年级，柱状体回应每个班级
    县级：
        type=province/city，饼图回应县级整体，柱状图回应县级整体
        type=country，饼图回应县级整体，柱状图回应每个街道
        type=town，饼图回应这个街道，柱状图回应每个学校
        type=school，饼图回应这个学校，柱状图回应每个年级
    cache的实现：
    对于校级：没有改变。
    对于县级：每个学校上传如下cache供县级使用：
        school-[uuid]-class-total: 这个学校的班级总数，永不过期，只会被更新的数据覆盖
        school-[uuid]-class-online: 这个学校的在线班级总数，一分钟
        school-[uuid]-teacher-total: 这个学校的教师总数，永不过期
        school-[uuid]-teacher-online: 在线教师总数，一分钟
        以及下属每个年级的在线数，用于type=school时的柱状图
            grade-[uuid]-class-online，一分钟
            grade-[uuid]-teacher-online，一分钟
        (电脑教室暂时略过，以后由胡海来做)
'''


def _get_schools(node_uuid, node_type, request):
    if node_type == 'province':
        schools = models.Group.objects.filter(group_type='school',
                                              parent__parent__parent__parent__uuid=node_uuid)
    elif node_type == 'city':
        schools = models.Group.objects.filter(group_type='school',
                                              parent__parent__parent__uuid=node_uuid)
    elif node_type == 'country':
        schools = models.Group.objects.filter(group_type='school',
                                              parent__parent__uuid=node_uuid)
    elif node_type == 'town':
        schools = models.Group.objects.filter(group_type='school',
                                              parent__uuid=node_uuid)
    elif node_type == 'school':
        schools = models.Group.objects.filter(group_type='school',
                                              uuid=node_uuid)
    else:
        return []

    if not is_admin(request.current_user):
        permitted_groups = request.current_user.permitted_groups.all()
        schools = schools.filter(uuid__in=permitted_groups)
    return schools


def _get_teacher_uuids(node_uuid, node_type, classes):
    k = 'teacher-uuids-for-node-%s' % node_uuid
    v = cache.get(k)
    if v:
        return cPickle.loads(v)
    else:
        teachers = models.Teacher.objects.all()
        teachers = teachers.filter(lessonteacher__class_uuid__in=classes,
                                   deleted=False).distinct()
        uuids = teachers.values_list('uuid', flat=True)
        v = cPickle.dumps(uuids, cPickle.HIGHEST_PROTOCOL)
        cache.set(k, v, get_timeout(k, 60 * 60))  # 缓存一小时应该可以吧
        return uuids


def _get_classes_teachers(node_uuid, node_type, request):
    timelog = []
    if node_type == 'grade':
        # 该年级的所有班级和教师
        g = models.Grade.is_computerclass(node_uuid)
        if g:
            node_uuid = g.term.school.uuid
            classes = models.Class.objects.filter(grade__term__school=node_uuid)
        else:
            classes = models.Class.objects.filter(grade__uuid=node_uuid)
        timelog.append({'4-11': str(datetime.datetime.now())})
        if not is_admin(request.current_user):
            groups = request.current_user.permitted_groups.all()
            timelog.append({'4-12': str(datetime.datetime.now())})
            classes = classes.filter(grade__term__school__in=groups)
            timelog.append({'4-13': str(datetime.datetime.now())})
    else:
        # 该级别的所有班级和教师
        schools = _get_schools(node_uuid, node_type, request)
        timelog.append({'4-21': str(datetime.datetime.now())})
        terms = simplecache.Term.get_current_term_list(node_uuid, schools)
        timelog.append({'4-22': str(datetime.datetime.now())})
        classes = models.Class.objects.filter(grade__term__in=terms)
        timelog.append({'4-23': str(datetime.datetime.now())})
    teachers = _get_teacher_uuids(node_uuid, node_type, classes)
    if node_type == 'grade' and g:
        # TODO 数据筛选真坑啊... 这些处理果断得重写.
        classes = classes.filter(grade__number=13)
    timelog.append({'4-4': str(datetime.datetime.now())})
    return classes, teachers, timelog


def _aggregate(node_type):
    # node_type的下一级
    if node_type == 'province':
        key = 'city'
        cache_cls = simplecache.Group
        name_suffix = u''
    elif node_type == 'city':
        key = 'country'
        cache_cls = simplecache.Group
        name_suffix = u''
    elif node_type == 'country':
        key = 'town'
        cache_cls = simplecache.Group
        name_suffix = u''
    elif node_type == 'town':
        key = 'school'
        cache_cls = simplecache.Group
        name_suffix = u''
    elif node_type == 'school':
        key = 'grade'
        cache_cls = simplecache.Grade
        name_suffix = u'年级'
    elif node_type == 'grade':
        key = 'class'
        cache_cls = simplecache.Class
        name_suffix = u'班'
    return key, cache_cls, name_suffix


def _get_top5(node_type, active_uuids, top5_type):
    # 按区域汇总在线数
    timelog = []
    timelog.append({'t1': str(datetime.datetime.now())})
    key, cache_cls, name_suffix = _aggregate(node_type)
    timelog.append({'t2': str(datetime.datetime.now())})
    ret = {}
    keys = ['%s-%s-active-time' % (top5_type, uu) for uu in active_uuids]
    d = cache.get_many(keys)
    timelog.append({'t3': str(datetime.datetime.now())})
    for k, v in d.items():
        json_v = json.loads(v)
        top5_key = json_v[key]
        if top5_key not in ret:
            ret[top5_key] = 0
        ret[top5_key] += 1
    timelog.append({'t4': str(datetime.datetime.now())})
    # 排序top5
    ret1 = []
    names = cache_cls.get_names(ret.keys())
    ret1 = [{'name': v + name_suffix, 'num': ret[k]} if (v + name_suffix) != u'电脑教室年级'
            else {'name': v, 'num': ret[k]} for k, v in names.items()]
    timelog.append({'t5': str(datetime.datetime.now())})
    ret = sorted(ret1, lambda x, y: cmp(x['num'], y['num']), reverse=True)
    timelog.append({'t6': str(datetime.datetime.now())})
    return ret[:5], []


def _get_data(node_uuid, node_type, request):
    timelog = []
    data = {
        'class': {'online': 0, 'offline': 0, 'sum': 0, 'online_list': []},
        'teacher': {'online': 0, 'offline': 0, 'sum': 0, 'online_list': []},
        'computerclass': {'online': 0, 'offline': 0, 'sum': 0, 'online_list': [],
                          'login': 0, 'unlogin': 0, 'login_list': []},
    }
    classes = None
    computerclass = None
    teachers = None
    try:
        classes, teachers, l = _get_classes_teachers(node_uuid, node_type, request)
        computerclass = classes.filter(grade__number=13)
        timelog.extend(l)
    except Exception as e:
        logger.exception(e)
        # 对于异常，回应空数据
        return data, timelog

    if models.Setting.getvalue('server_type') != 'school':
        # 校级以外的服务器电脑教室的数据单独处理
        classes = classes.exclude(grade__number=13)
        del data['computerclass']

    timelog.append({'6': str(datetime.datetime.now())})
    data['class']['sum'] = classes.count()

    timelog.append({'7': str(datetime.datetime.now())})
    active_class_uuids = []
    keys = ['class-%s-active-time' % i for i in classes.values_list('uuid', flat=True)]
    ret = cache.get_many(keys)

    timelog.append({'7-1': str(datetime.datetime.now())})
    for k in ret:
        uu = k[6:-12]  # class_uuid
        active_class_uuids.append(uu)

    timelog.append({'8': str(datetime.datetime.now())})
    data['class']['online'] = len(active_class_uuids)
    data['class']['offline'] = data['class']['sum'] - data['class']['online']

    timelog.append({'9': str(datetime.datetime.now())})
    data['teacher']['sum'] = len(teachers)

    timelog.append({'10': str(datetime.datetime.now())})
    active_teacher_uuids = set()

    timelog.append({'10-1': str(datetime.datetime.now())})
    active_teachers_count = 0

    timelog.append({'10-2': str(datetime.datetime.now())})
    keys = ['teacher-%s-active-time' % i for i in teachers]

    timelog.append({'10-3': str(datetime.datetime.now())})
    ret = cache.get_many(keys)

    timelog.append({'10-4': str(datetime.datetime.now())})
    for k, v in ret.items():
        json_v = json.loads(v)
        if json_v:
            if json_v['class'] in active_class_uuids:
                active_teacher_uuids.add(k[8:-12])

    timelog.append({'10-5': str(datetime.datetime.now())})
    active_teachers_count = len(active_teacher_uuids)
    timelog.append({'11': str(datetime.datetime.now())})
    data['teacher']['online'] = active_teachers_count
    timelog.append({'12': str(datetime.datetime.now())})
    data['teacher']['offline'] = data['teacher']['sum'] - data['teacher']['online']
    timelog.append({'13': str(datetime.datetime.now())})
    data['class']['online_list'], t = _get_top5(node_type, active_class_uuids, 'class')
    timelog.extend(t)
    timelog.append({'14': str(datetime.datetime.now())})
    data['teacher']['online_list'], t = _get_top5(node_type, active_teacher_uuids, 'teacher')
    timelog.append({'15': str(datetime.datetime.now())})

# ---------------------------------------------------------------------------- #
    if models.Setting.getvalue('server_type') == 'school':
        active_computerclass_uuids = []
        keys = ['class-%s-active-time' % i for i in computerclass.values_list('uuid', flat=True)]
        ret = cache.get_many(keys)
        for k in ret:
            uu = k[6:-12]
            active_computerclass_uuids.append(uu)

        data['computerclass']['sum'] = computerclass.count()
        data['computerclass']['online'] = len(active_computerclass_uuids)
        data['computerclass']['offline'] = data['computerclass']['sum'] - data['computerclass']['online']
        data['computerclass']['online_list'], t = _get_top5(node_type,
                                                            active_computerclass_uuids, 'class')

        keys = ['computerclass-teacher-%s-active-time' % i for i in teachers]
        ret = cache.get_many(keys)
        active_computerclass_teacher_uuids = set()
        for k, v in ret.items():
            json_v = json.loads(v)
            if json_v:
                if json_v['class'] in active_computerclass_uuids:
                    active_computerclass_teacher_uuids.add(k[22:-12])

        data['computerclass']['login'] = len(active_computerclass_teacher_uuids)
        data['computerclass']['unlogin'] = data['computerclass']['sum'] - data['computerclass']['login']
        data['computerclass']['login_list'], t = _get_top5(node_type, active_computerclass_teacher_uuids, 'computerclass-teacher')

        if models.Grade.is_computerclass(node_uuid):
            data['teacher']['online_list'] = data['computerclass']['login_list']
        if models.Grade.is_computerclass(node_uuid):
            # 校级服务器选择电脑教室年级的时候,需要特殊处理
            d = _get_data_computerclass(node_uuid, node_type, request)
            data['class']['online'] = d['computerclass']['online']
            data['class']['offline'] = d['computerclass']['offline']
            # data['class']['online_list'] = d['computerclass']['online_list']
            data['teacher']['online'] = d['computerclass']['login']
            ##data['teacher']['offline'] = d['computerclass']['unlogin']
            lr = models.ComputerClassLessonRange.objects.all()
            lr = lr.values_list('lessonname', flat=True)
            teachers = models.LessonTeacher.objects.filter(lesson_name__in=lr)
            teachers = set(teachers.values_list('teacher', flat=True))
            data['teacher']['offline'] = len(teachers) - data['teacher']['online']
            # data['teacher']['online_list'] = d['computerclass']['login_list']
            del data['computerclass']

    return data, timelog


def _get_data_computerclass(node_uuid, node_type, request):
    """获取电脑教室的全局数据"""
    data = {'computerclass': {
            'online': 0, 'offline': 0, 'sum': 0, 'online_list': [],
            'login': 0, 'unlogin': 0, 'login_list': []}}
    classes = None
    computerclass = None
    teachers = None
    try:
        if models.Grade.is_computerclass(node_uuid):
            # 这一步用于校级服务器将电脑教室年级转换为学校,县级最小节点是校级
            node_uuid = models.Grade.objects.get(uuid=node_uuid).term.school.uuid
            node_type = 'school'
        classes, teachers, l = _get_classes_teachers(node_uuid, node_type, request)
        try:
            computerclass = classes.filter(grade__number=13)
        except:
            pass
    except Exception as e:
        logger.exception(e)
        return data, None

    active_class_uuids = []
    keys = ['class-%s-active-time' % i for i in classes.values_list('uuid', flat=True)]
    ret = cache.get_many(keys)
    for k in ret:
        uu = k[6:-12]  # class_uuid
        active_class_uuids.append(uu)

    active_computerclass_uuids = []
    keys = ['class-%s-active-time' % i for i in computerclass.values_list('uuid', flat=True)]
    ret = cache.get_many(keys)
    for k in ret:
        uu = k[6:-12]  # computerclass_uuid
        active_computerclass_uuids.append(uu)

    data['computerclass']['sum'] = computerclass.count()
    data['computerclass']['online'] = len(active_computerclass_uuids)
    data['computerclass']['offline'] = data['computerclass']['sum'] - data['computerclass']['online']
    data['computerclass']['online_list'], t = _get_top5(node_type, active_computerclass_uuids, 'class')

    active_computerclass_teacher_uuids = set()
    keys = ['computerclass-teacher-%s-active-time' % i for i in teachers]
    ret = cache.get_many(keys)
    for k, v in ret.items():
        json_v = json.loads(v)
        if json_v:
            if json_v['class'] in active_computerclass_uuids:
                active_computerclass_teacher_uuids.add(k[22:-12])

    data['computerclass']['login'] = len(active_computerclass_teacher_uuids)
    data['computerclass']['unlogin'] = data['computerclass']['sum'] - data['computerclass']['login']
    data['computerclass']['login_list'], t = _get_top5(node_type, active_computerclass_teacher_uuids, 'computerclass-teacher')
    return data


@decorator.authorized_user_with_redirect
def global_statistic(request, *args, **kwargs):
    """实时概况>全局数据"""
    timelog = []
    timelog.append({'start': str(datetime.datetime.now())})
    uuid = request.GET.get('uuid')
    node_type = request.GET.get('type')
    timelog.append({'2': str(datetime.datetime.now())})
    if not node_type:
        return create_failure_dict(msg='参数node_type不能为空')
    if not uuid:
        # 只有type没有uuid，是默认界面的url
        if models.Setting.getvalue('server_type') != node_type:
            return create_failure_dict(msg='错误的node_type %s' % node_type)
        try:
            obj = models.Group.objects.get(group_type=node_type)
        except:
            return create_failure_dict(msg='查找服务器节点时出错')
        uuid = obj.uuid
    else:
        # 既有type又有uuid，需要验证数据合法性
        if node_type in ('province', 'city', 'country', 'town', 'school'):
            try:
                obj = models.Group.objects.get(group_type=node_type, uuid=uuid)
            except:
                return create_failure_dict(msg='错误的node_type和uuid')
        elif node_type == 'grade':
            try:
                obj = models.Grade.objects.get(uuid=uuid)
            except:
                return create_failure_dict(msg='错误的年级uuid')
        else:
            return create_failure_dict(msg='错误的node_type')

    timelog.append({'3': str(datetime.datetime.now()),
                    'node_uuid': uuid,
                    'node_type': node_type})

    data, l = _get_data(uuid, node_type, request)
    timelog.extend(l)
    timelog.append({'end': str(datetime.datetime.now())})

    return create_success_dict(data=data)  # , timelog=timelog)


@decorator.authorized_user_with_redirect
def global_statistic_computerclass(request, *args, **kwargs):
    """实时概况>电脑教室全局数据"""
    uuid = request.GET.get('uuid')
    node_type = request.GET.get('type')
    if not node_type:
        return create_failure_dict(msg='参数node_type不能为空')
    if not uuid:
        if models.Setting.getvalue('server_type') != node_type:
            return create_failure_dict(msg='错误的node_type %s' % node_type)
        try:
            obj = models.Group.objects.get(group_type=node_type)
        except:
            return create_failure_dict(msg='查找服务器节点时出错')
        uuid = obj.uuid
    else:
        if node_type in ('province', 'city', 'country', 'town', 'school'):
            try:
                obj = models.Group.objects.get(group_type=node_type, uuid=uuid)
            except:
                return create_failure_dict(msg='错误的node_type和uuid')
        elif node_type == 'grade':
            try:
                obj = models.Grade.objects.get(uuid=uuid)
            except:
                return create_failure_dict(msg='错误的年级uuid')
        else:
            return create_failure_dict(msg='错误的node_type')

    data = _get_data_computerclass(uuid, node_type, request)
    return create_success_dict(data=data)
