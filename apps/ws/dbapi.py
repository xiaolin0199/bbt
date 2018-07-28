#!/usr/bin/env python
# coding=utf-8
import os
import time
import logging
import datetime
import json

from django.core import serializers
import django_mysqlpool
from django.db.models import Q
from BanBanTong import constants
from BanBanTong.db import models
import machine_time_used.models
from BanBanTong.utils import str_util
'''
    用于下级服务器回传
    打包目标服务器的基础数据
    基础数据: Group, Term, Teacher, Setting
    资产管理: AssetType, Asset, AssetLog, AssetRepairLog
    资源管理: ResourceFrom, ResourceType
    教材大纲: CourseWare, TeacherLoginLogCourseWare, TeacherLoginLogLessonContent
    年级班级: Class, ComputerClass, Grade, ClassMacV2, ClassTime
    课程数据: LessonName, ComputerClassLessonRange, LessonPeriod, LessonSchedule, LessonTeacher
    登录日志: TeacherLoginLog, TeacherLoginLogTag, TeacherLoginTime
    截图数据: DesktopPicInfo, DesktopPicInfoTag, DesktopGlobalPreview, DesktopGlobalPreviewTag
    终端时长: MachineTimeUsed
    教学点  : 数据都在县级，不存在回传操作
'''

logger = logging.getLogger(__name__)


@django_mysqlpool.auto_close_db
def backup_group(uuids):
    data = ''
    count = 0
    schools = models.Group.objects.filter(uuid__in=uuids)
    for i in schools:
        while i.parent:
            i = i.parent
            uuids.append(i.uuid)
    towns = models.Group.objects.filter(uuid__in=uuids, group_type='town')
    countries = models.Group.objects.filter(uuid__in=uuids, group_type='country')
    cities = models.Group.objects.filter(uuid__in=uuids, group_type='city')
    provinces = models.Group.objects.filter(uuid__in=uuids, group_type='province')
    data += serializers.serialize('json', provinces) + '\n'
    data += serializers.serialize('json', cities) + '\n'
    data += serializers.serialize('json', countries) + '\n'
    data += serializers.serialize('json', towns) + '\n'
    data += serializers.serialize('json', schools) + '\n'
    count = schools.count() + towns.count() + countries.count() + cities.count() + provinces.count()
    return data, count


@django_mysqlpool.auto_close_db
def backup_teacher(uuids):
    data = ''
    count = 0
    q = models.Teacher.objects.filter(school__in=uuids)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    return data, count


@django_mysqlpool.auto_close_db
def backup_assets(uuids):
    data = ''
    count = 0
    q = models.AssetType.objects.filter(school__in=uuids)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    q = models.Asset.objects.filter(school__in=uuids)
    q = q.filter(related_asset__isnull=True)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    q = models.Asset.objects.filter(school__in=uuids)
    q = q.filter(related_asset__isnull=False)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    q = models.AssetLog.objects.filter(school__in=uuids)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    q = models.AssetRepairLog.objects.filter(school__in=uuids)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    return data, count


@django_mysqlpool.auto_close_db
def backup_class(uuids):
    data = ''
    count = 0
    #q = models.Term.objects.filter(school__in=uuids, deleted=False)
    # 回传的时候将县级服务器中该学校所有的Term数据都回传，避免校级从县级NewTerm拉学年
    # 学期数据的时候再次将deleted=1的数据拉回来，传给县级造成县成Term表拥有重复数据
    q = models.Term.objects.filter(school__in=uuids, deleted=False)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    q = models.Grade.objects.filter(term__school__in=uuids, term__deleted=False)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    q = models.Class.objects.filter(grade__term__school__in=uuids,
                                    grade__term__deleted=False)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    # computerclass
    q = models.ComputerClass.objects.filter(class_bind_to__grade__term__school__in=uuids,
                                            class_bind_to__grade__term__deleted=False)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    q = models.ClassMacV2.objects.filter(class_uuid__grade__term__school__in=uuids,
                                         class_uuid__grade__term__deleted=False)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    q = models.ClassTime.objects.filter(class_uuid__grade__term__school__in=uuids)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    return data, count


@django_mysqlpool.auto_close_db
def backup_lesson(uuids):
    data = ''
    count = 0
    q = models.LessonName.objects.filter(school__in=uuids)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    # computerclasslesson_range 注意:由于有外键约束存在,这里必须放在
    # ComputerClass和LessonName后面
    q = models.ComputerClassLessonRange.objects.filter(
        computerclass__class_bind_to__grade__term__school__in=uuids,
        computerclass__class_bind_to__grade__term__deleted=False)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    q = models.LessonPeriod.objects.filter(term__school__in=uuids,
                                           term__deleted=False)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    q = models.LessonSchedule.objects.filter(class_uuid__grade__term__school__in=uuids,
                                             class_uuid__grade__term__deleted=False)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    q = models.LessonTeacher.objects.filter(class_uuid__grade__term__school__in=uuids,
                                            class_uuid__grade__term__deleted=False)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    return data, count


@django_mysqlpool.auto_close_db
def backup_loginlog(uuids):
    data = ''
    count = 0
    term = models.NewTerm.get_current_term()
    if not term:
        return data, count
    q = models.TeacherLoginLog.objects.filter(school__in=uuids, term_school_year=term.school_years, term_type=term.term_types)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    # TeacherLoginLogTag
    try:
        q = models.TeacherLoginLogTag.objects.filter(bind_to__school__in=uuids,
                                                     bind_to__term__deleted=False)
        count += q.count()
        for obj in q:
            data += serializers.serialize('json', [obj, ]) + '\n'
    except:
        pass
    q = models.TeacherLoginTime.objects.filter(teacherloginlog__school__in=uuids,
                                               teacherloginlog__term__deleted=False)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    return data, count


@django_mysqlpool.auto_close_db
def backup_absentlog(uuids):
    data = ''
    count = 0
    q = models.TeacherAbsentLog.objects.filter(school__in=uuids,
                                               term__deleted=False)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    return data, count


@django_mysqlpool.auto_close_db
def backup_desktoppic(uuids):
    data = ''
    count = 0
    q = models.DesktopPicInfo.objects.filter(school__in=uuids,
                                             grade__term__deleted=False)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    # DesktopPicInfoTag
    try:
        q = models.DesktopPicInfoTag.objects.filter(bind_to__school__in=uuids,
                                                    bind_to__grade__term__deleted=False)
        count += q.count()
        for obj in q:
            data += serializers.serialize('json', [obj, ]) + '\n'
    except:
        pass
    # DesktopGlobalPreview
    q = models.DesktopGlobalPreview.objects.filter(pic__school__in=uuids,
                                                   pic__grade__term__deleted=False)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    # DesktopGlobalPreviewTag
    try:
        q = models.DesktopGlobalPreviewTag.objects.filter(bind_to__pic__school__in=uuids,
                                                          bind_to__pic__grade__term__deleted=False)
        count += q.count()
        for obj in q:
            data += serializers.serialize('json', [obj, ]) + '\n'
    except:
        pass
    return data, count


@django_mysqlpool.auto_close_db
def backup_courseware(uuids):
    data = ''
    count = 0
    # courseware
    q = models.CourseWare.objects.filter(teacherloginlog__school__in=uuids)
    q = q.filter(teacherloginlog__term__deleted=False)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    q = models.TeacherLoginLogCourseWare.objects.filter(teacherloginlog__school__in=uuids)
    q = q.filter(teacherloginlog__term__deleted=False)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    q = models.TeacherLoginLogLessonContent.objects.filter(teacherloginlog__school__in=uuids)
    q = q.filter(teacherloginlog__term__deleted=False)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    return data, count


@django_mysqlpool.auto_close_db
def backup_resource(uuids):
    data = ''
    count = 0
    q = models.ResourceFrom.objects.all()
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    q = models.ResourceType.objects.all()
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    return data, count


def backup_setting(node):
    data = ''
    count = 0
    user_line = ''
    with open(os.path.join(constants.CACHE_TMP_ROOT, str(node.id) + '.setting')) as f:
        lines = f.read().split('\n')
        count = len(lines)
        for line in lines:
            if '"model": "db.setting"' in line:
                objs = []
                for i in serializers.deserialize('json', line):
                    if i.object.name.startswith('sync_server_'):
                        continue
                    if i.object.name in ['host', 'port']:
                        continue
                    objs.append(i.object)
                setting_line = serializers.serialize('json', objs)
                data += setting_line + '\n'
            elif '"model": "db.user"' in line:
                user_line += line + '\n'
            else:
                data += line + '\n'
    if user_line:
        data += user_line
    return data, count


@django_mysqlpool.auto_close_db
def backup_machinetimeused(uuids):
    data = ''
    count = 0
    # 只打包未结转的学期
    terms = list(models.NewTerm.objects.filter(deleted=False))
    if not terms:
        # 没有新的学年学期的时候返回空
        logger.debug('no term')
        return data, count
    for term in terms:
        logger.debug('term:%s', term)
        if terms.index(term) == 0:
            cond = Q(term_school_year=term.school_year,
                     term_type=term.term_type)
        else:
            cond |= Q(term_school_year=term.school_year,
                      term_type=term.term_type)
    q = machine_time_used.models.MachineTimeUsed.objects.filter(school__in=uuids)
    q = q.filter(cond)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    return data, count


@django_mysqlpool.auto_close_db
def backup_activate_quota(node):
    # 这一部分也可以放到 backup_setting 中进行,考虑到其独立性,单独的摘出来.
    # 为学校准备的配额数据中包含以下内容
    # 分配点数-到期时间(让校级知道是因为配额不足还是软件到期导致操作失败)
    # Node表中只存了分配点数的参数(node并没有区分学年学期)
    # 所以这里实际上返回的就只能是分配点数和到期时间
    # 可能产生的问题就是校级改变本地时间到一个过去的点,能够创建更多的班级(好像没啥用)
    #
    ##
    # 分配点数-到期时间
    # 在到期时间内的时候,校级尝试新建班级的时候,允许创建的最大上限为该校的最大配额
    # 当激活时限到期的时候,校级连接上级的时候则给出授权到期的错误提示并断开连接
    # 这样处理的便捷之处在于,程序上不必去处理各学年学期时间段不同而增加的复杂度
    # 只需要简单的根据授权到期时间来判断程序的正常运作与否
    #
    ##
    # 县级界面展现上面则会依据自身的授权与否/到期与否/校级状态予以细致的展现
    # 及时的将软件运行状态呈现给用户,使其知道是否续期/修改学校配额
    # 需要注意的是,此处备份授权激活信息只是在新装/回传的时候使用
    # 由于县级的重复编辑引起的校级授权配额的变更则应当实时/及时更新到校级服务器
    d = models.Setting.getval('activation')
    if not d:
        return '', 0

    country = models.Group.objects.get(group_type='country')
    country_name = country.name
    city_name = country.parent.name
    province_name = country.parent.parent.name

    info = {
        'country_name': country_name,
        'city_name': city_name,
        'area': '%s %s %s' % (province_name, city_name, country_name),
        'quota': node.activation_number,
        'update_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'start_date': d['start_date'],
        'end_date': d['end_date'],
    }
    obj = {
        "pk": models._make_uuid(),
        "model": "db.setting",
        "fields": {
            "name": 'activation',
            "value": str_util.encode(json.dumps(info))[0]
        }
    }
    data = json.dumps([obj]) + '\n'
    count = 1
    return data, count


@django_mysqlpool.auto_close_db
def blocking_get_server_type():
    while True:
        server_type = models.Setting.getvalue('server_type')
        if server_type:
            return server_type
        else:
            logger.warning('server_type not set')
            return ''
            time.sleep(5)


@django_mysqlpool.auto_close_db
def blocking_get_sync_host_port_key():
    while True:
        host = models.Setting.getvalue('sync_server_host')
        port = models.Setting.getvalue('sync_server_port')
        key = models.Setting.getvalue('sync_server_key')
        if host and port and key:
            return host, port, key
        else:
            logger.warning('sync server not configured: host=%s, port=%s, key=%s', host, port, key)
            time.sleep(30)
