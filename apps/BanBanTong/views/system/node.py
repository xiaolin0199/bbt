# coding=utf-8
import bz2
import datetime
import json
import logging
import os
import traceback
import uuid
from django.core import serializers
from django.core.urlresolvers import reverse
from django.db import connection
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.db import utils as db_utils
from BanBanTong.forms.node import NodeForm
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import get_page_info
from BanBanTong.utils import model_to_dict
from BanBanTong.utils import simplecache
from machine_time_used import models as newmodels
from activation.decorator import activation_required
from django.db.models import Case, When


logger = logging.getLogger(__name__)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_node')
def list_current(request, *args, **kwargs):
    page_info = get_page_info(request)
    days_before = datetime.datetime.now() - datetime.timedelta(3)
    order = Case(*[
        When(sync_status__lt=0, then=0),
        When(last_active_time__isnull=True, sync_status=0, then=1),
        When(last_active_time__lte=days_before, sync_status=0, then=2),
        When(last_active_time__gte=days_before, sync_status=0, then=3)
    ])
    objs = models.Node.objects.all().order_by(order, 'sync_status', 'remark')
    page_data = db_utils.pagination(objs, **page_info)
    lst = [n.pk for n in page_data['records']]
    use_numbers = {n.pk: n.get_use_number() for n in objs.filter(pk__in=lst)}
    records = [n.to_dict() for n in page_data['records']]
    for n in records:
        n['use_number'] = use_numbers.get(n['id'])
    page_data['records'] = records
    return create_success_dict(data=page_data)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_node')
@activation_required
def add(request, *args, **kwargs):
    if request.method == 'POST':
        f = NodeForm(request.POST)
        if f.is_valid():
            node = f.save()
            return create_success_dict(msg='添加服务器成功！',
                                       data=model_to_dict(node))

        return create_failure_dict(msg='添加服务器失败！', errors=f.errors)


def _backup_data(uuids):
    data = ''
    count = 0
    logger.debug('restore --- data teachers')
    # teachers
    q = models.Teacher.objects.filter(school__in=uuids)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    # assets
    logger.debug('restore --- data assets')
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
    # term/grade/class
    logger.debug('restore --- data classes')
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
    # lessons
    logger.debug('restore --- data lessons')
    q = models.LessonName.objects.filter(school__in=uuids)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    # computerclass/lesson_range 注意:由于有外键约束存在,这里必须放在
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
    q = models.TeacherLoginLog.objects.filter(school__in=uuids,
                                              term__deleted=False)
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
        logger.debug('Table: TeacherLoginLogTag seems not exists')
        pass
    q = models.TeacherLoginTime.objects.filter(teacherloginlog__school__in=uuids,
                                               teacherloginlog__term__deleted=False)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    q = models.TeacherAbsentLog.objects.filter(school__in=uuids,
                                               term__deleted=False)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    # desktop-preview
    logger.debug('restore --- data desktop-preview')
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
        logger.exception('')
        logger.debug('Table: DesktopPicInfoTag seems not exists')
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
        logger.debug('Table: DesktopGlobalPreviewTag seems not exists')
        pass
    # courseware
    q = models.CourseWare.objects.filter(teacherloginlog__school__in=uuids)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    q = models.TeacherLoginLogCourseWare.objects.filter(teacherloginlog__school__in=uuids)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'
    q = models.TeacherLoginLogLessonContent.objects.filter(teacherloginlog__school__in=uuids)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'

    # machine-time-used
    q = newmodels.MachineTimeUsed.objects.filter(school__in=uuids)
    count += q.count()
    for obj in q:
        data += serializers.serialize('json', [obj, ]) + '\n'

    if models.Setting.getvalue('server_type') == 'country':
        q = models.ResourceFrom.objects.all()
        count += q.count()
        for obj in q:
            data += serializers.serialize('json', [obj, ]) + '\n'
        q = models.ResourceType.objects.all()
        count += q.count()
        for obj in q:
            data += serializers.serialize('json', [obj, ]) + '\n'

    # 几张New表对应的都是县级服务器,此处uuids都是校极UUID,所以需要单独处理一下
    elif models.Setting.getvalue('server_type') == 'city':
        # NewTerm
        town_uuids = set(models.Group.objects.filter(group_type='school', uuid__in=uuids).values_list('parent', flat=True))

        country_uuids = set(models.Group.objects.filter(group_type='town', uuid__in=town_uuids).values_list('parent', flat=True))

        q = models.NewTerm.objects.filter(country__in=country_uuids)
        count += q.count()
        for obj in q:
            data += serializers.serialize('json', [obj, ]) + '\n'

        # NewLessonType
        q = models.NewLessonType.objects.filter(country__in=country_uuids)
        count += q.count()
        for obj in q:
            data += serializers.serialize('json', [obj, ]) + '\n'

        # NewLessonName , NewLessonNameType
        q = models.NewLessonName.objects.filter(country__in=country_uuids)
        count += q.count()
        for obj in q:
            data += serializers.serialize('json', [obj, ]) + '\n'

        q = models.NewLessonNameType.objects.filter(newlessonname__country__in=country_uuids)
        count += q.count()
        for obj in q:
            data += serializers.serialize('json', [obj, ]) + '\n'

        # ResourceFrom , ResourceType
        q = models.ResourceFrom.objects.filter(country__in=country_uuids)
        count += q.count()
        for obj in q:
            data += serializers.serialize('json', [obj, ]) + '\n'
        q = models.ResourceType.objects.filter(country__in=country_uuids)
        count += q.count()
        for obj in q:
            data += serializers.serialize('json', [obj, ]) + '\n'

    return data, count


def _backup_group(uu):
    data = ''
    count = 0
    schools = models.Group.objects.filter(uuid__in=uu)
    for i in schools:
        while i.parent:
            i = i.parent
            uu.append(i.uuid)
    towns = models.Group.objects.filter(uuid__in=uu, group_type='town')
    countries = models.Group.objects.filter(uuid__in=uu, group_type='country')
    cities = models.Group.objects.filter(uuid__in=uu, group_type='city')
    provinces = models.Group.objects.filter(uuid__in=uu, group_type='province')
    data += serializers.serialize('json', provinces) + '\n'
    data += serializers.serialize('json', cities) + '\n'
    data += serializers.serialize('json', countries) + '\n'
    data += serializers.serialize('json', towns) + '\n'
    data += serializers.serialize('json', schools) + '\n'
    count = schools.count() + towns.count() + countries.count() + cities.count() + provinces.count()
    return data, count


def _backup_meta(node):
    data = 'meta:'
    d = {}
    # node.last_upload_id用于下级SyncLog的AUTO_INCREMENT
    d['last_upload_id'] = node.last_upload_id
    data += json.dumps(d)
    return data + '\n'


def _backup_setting(node):
    try:
        ret = ''
        with open(os.path.join(constants.CACHE_TMP_ROOT, str(node.id) + '.setting')) as f:
            data = f.read()
            lines = data.split('\n')
            for line in lines:
                logger.debug('_backup_setting: %s', line)
                if '"model": "db.setting"' in line:
                    objs = [i.object for i in serializers.deserialize('json', line) if not i.object.name.startswith('sync_server_')]
                    setting_line = serializers.serialize('json', objs)
                    ret += setting_line + '\n'
                else:
                    ret += line + '\n'
        logger.debug('_backup_setting: ret %s', ret)
        return ret
    except:
        logger.exception('')
        return ''


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_node')
def backup(request, *args, **kwargs):
    if request.method == 'GET':
        node_id = request.GET.get('id')
        try:
            node = models.Node.objects.get(id=node_id)
        except:
            return create_failure_dict(msg='错误的id！')
    elif request.method == 'POST':
        key = request.POST.get('key')
        if not key:
            return create_failure_dict(msg='缺少参数！')
        try:
            node = models.Node.objects.get(communicate_key=key)
        except:
            return create_failure_dict(msg='错误的参数！')
    try:
        f = open(os.path.join(constants.CACHE_TMP_ROOT,
                              str(node.id) + '.node'))
        uuids = [line.strip('\n') for line in f]
        f.close()
        data = ''
        # Group
        s, count = _backup_group(uuids)
        data += s
        # all data
        s, count = _backup_data(uuids)
        data += s
        # Setting
        data += _backup_setting(node)
        # others
        data += _backup_meta(node)
        s = bz2.compress(data)
        cached_id = str(uuid.uuid1())
        tmp_file = os.path.join(constants.CACHE_TMP_ROOT, cached_id)
        f = open(tmp_file, 'w')
        f.write(s)
        f.close()
        filename = u'node-%d-%s.backup' % (node.id,
                                           str(datetime.date.today()))
        return create_success_dict(url=reverse('base:xls_download',
                                               kwargs={'cached_id': cached_id,
                                                       'name': filename}))
    except:
        logger.exception('')
        return create_failure_dict(msg='导出数据失败！')


def _delete_node_data(node_id):
    tmp_file = os.path.join(constants.CACHE_TMP_ROOT,
                            str(node_id) + '.node')

    try:
        with open(tmp_file, 'r') as f:
            uuids = [line.strip('\n') for line in f]
        os.remove(tmp_file)
    except Exception:
        str_node_id = u'node_%s_school_uuid' % (node_id)
        uuids = [i.value for i in models.Setting.objects.filter(name=str_node_id)]

    cursor = connection.cursor()
    cursor.execute('SET FOREIGN_KEY_CHECKS=0')

    models.AssetRepairLog.objects.filter(school__uuid__in=uuids).delete()
    models.Asset.objects.filter(school__uuid__in=uuids).delete()
    models.AssetLog.objects.filter(school__uuid__in=uuids).delete()
    models.AssetType.objects.filter(school__uuid__in=uuids).delete()
    models.TeacherLoginLog.objects.filter(school__uuid__in=uuids).delete()
    models.TeacherAbsentLog.objects.filter(school__uuid__in=uuids).delete()
    models.LessonName.objects.filter(school__uuid__in=uuids).delete()
    models.LessonSchedule.objects.filter(class_uuid__grade__term__school__uuid__in=uuids).delete()
    models.LessonPeriod.objects.filter(term__school__uuid__in=uuids).delete()
    models.LessonTeacher.objects.filter(class_uuid__grade__term__school__uuid__in=uuids).delete()
    models.Teacher.objects.filter(school__uuid__in=uuids).delete()
    models.ClassMacV2.objects.filter(class_uuid__grade__term__school__uuid__in=uuids).delete()
    models.Class.objects.filter(grade__term__school__uuid__in=uuids).delete()
    models.Grade.objects.filter(term__school__uuid__in=uuids).delete()
    models.Term.objects.filter(school__uuid__in=uuids).delete()
    models.Group.objects.filter(uuid__in=uuids).delete()

    cursor.execute('SET FOREIGN_KEY_CHECKS=1')
    cursor.close()

    tmp_file = os.path.join(constants.CACHE_TMP_ROOT,
                            str(node_id) + '.setting')

    try:
        with open(tmp_file, 'r') as f:
            os.remove(tmp_file)
    except Exception:
        pass


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_node')
def delete(request, *args, **kwargs):
    if request.method == 'POST':
        pk = request.POST.get('id')
        if pk:
            try:
                node = models.Node.objects.get(id=pk)
                node.delete()
                _delete_node_data(pk)
                simplecache.Group.reset(request.current_user)
                return create_success_dict(msg='删除服务器成功！')
            except Exception as e:
                traceback.print_exc()
                return create_failure_dict(msg='删除服务器失败！', errors=[[str(e)]])


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_node')
#@activation_required
def edit(request, *args, **kwargs):
    if request.method == 'POST':
        try:
            pk = request.POST.get('id')
            node = models.Node.objects.get(id=pk)
            f = NodeForm(request.POST, instance=node)
            if f.is_valid():
                node = f.save()
                return create_success_dict(msg=u'编辑成功！', data=model_to_dict(node))
            return create_failure_dict(msg=u'操作失败', errors=f.errors)
        except Exception as e:
            return create_failure_dict(msg='操作失败', debug=str(e))


def get_node_id(request):
    '''
        返回校服务器的NODE ID
    '''
    if request.method == 'POST':
        if models.Setting.getvalue('server_type') == 'school':
            return
        key = request.POST.get('key')
        try:
            node = models.Node.objects.get(communicate_key=key)
            return create_success_dict(data={'node_id': node.id})
        except:
            logger.exception('')
            return create_failure_dict(data={'node_id': None})


def what_is_the_meaning_of(request, *args, **kwargs):

    MEANING = {
        '0': u'一切正常',
        '-1': u'校级服务器身份验证失败(下级发送的uuid与上级Setting.node_%d_school_uuid已有记录不一致)',
        '-2': u'校级服务器身份验证失败(node.name不一致)',
        '-3': u'错误的服务器级别',
        '-4': u'不在同一个行政区域内',
        '-5': u'下级同步id比上级小',
        '-6': u'校级使用点数大于县级当前分配数额',
        '-7': u'县级服务器尚未激活或激活已过期(激活后状态自动恢复正常)'
    }
    status_code = kwargs.get('status', None)
    foo = kwargs.get('foo', 1)
    if status_code:
        status = int(status_code) * foo
    return create_success_dict(meaning=MEANING.get(str(status), u'搞不清楚啥问题'))
