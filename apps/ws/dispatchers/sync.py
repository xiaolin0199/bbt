# coding=utf-8
import os
import bz2
import base64
import hashlib
import traceback
import json
import logging
import datetime
from twisted.internet import threads
from django.core import serializers
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q
from BanBanTong.db import models
from BanBanTong import constants
from BanBanTong.utils.get_cache_timeout import get_timeout
from BanBanTong.utils import str_util
from activation.decorator import has_activate
import ws.dbapi
import ws.cache
from ws.dispatchers import DISPATCHERS, DispatcherBase

try:
    import django_rq
except ImportError:
    # django_rq 仅在县级服务器使用, windows操作系统下面不支持
    django_rq = None


logger = logging.getLogger(__name__)


def save_data_into_db(node_id, records):
    # 任务执行过程中不允许新加入任务
    ws.cache.set_sync(node_id)
    row = None
    node = models.Node.objects.get(pk=node_id)
    last_upload_id = node.last_upload_id
    try:
        for row in records:
            models.SyncLogPack.unpack_log(row['operation_type'], row['operation_content'])
            node.last_upload_id = row['created_at']
    except Exception as e:
        logger.exception('node_id=%s, err=%s\nrow=%s', node_id, e, row)
    finally:
        ws.cache.unset_sync(node_id)
        if last_upload_id != node.last_upload_id:
            node.save()


def generaotr_node_setting_files(node):
    setting_path = os.path.join(constants.CACHE_TMP_ROOT, '%s.setting' % node.pk)
    node_path = os.path.join(constants.CACHE_TMP_ROOT, '%s.node' % node.pk)
    server_types = ['province', 'city', 'country', 'school']
    server_type = models.Setting.getvalue('server_type')
    if server_types[-1] == server_type:
        return
    child_type = server_types[server_types.index(server_type) + 1]
    obj = models.Group.objects.get(name=node.name, group_type=child_type)
    school_uuid = obj.pk

    if not os.path.exists(setting_path):
        content = []
        settings = [
            {"pk": models._make_uuid(), "model": "db.setting", "fields": {"name": 'server_type', "value": child_type}},
            {"pk": models._make_uuid(), "model": "db.setting", "fields": {"name": 'install_step', "value": -1}},
            {"pk": models._make_uuid(), "model": "db.setting", "fields": {"name": 'installed', "value": True}}
        ]
        while obj:
            settings.append({"pk": obj.pk, "model": "db.setting", "fields": {"name": obj.group_type, "value": obj.name}})
            obj = obj.parent
        users = [{
            "pk": models._make_uuid(), "model": "db.user", "fields": {
                "username": "admin", "qq": "", "remark": u"系统管理员",
                "realname": "", "level": "school", "mobile": "",
                "created_at": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "sex": "", "status": "active", "role": None, "email": "",
                "password": str(hashlib.sha1('admin').hexdigest())
            }}, {
            "pk": models._make_uuid(), "model": "db.user", "fields": {
                "username": "oseasy", "qq": "", "remark": u"系统管理员",
                "realname": "", "level": "school", "mobile": "",
                "created_at": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "sex": "", "status": "active", "role": None, "email": "",
                "password": str(hashlib.sha1('0512').hexdigest())
            }
        }]

        content.append(json.dumps(settings))
        content.append(json.dumps(users))
        content.append(serializers.serialize('json', [node]))
        content = '\n'.join(content)
        logger.info('generaotr_node_setting_files: path=%s, content:%s', setting_path, content)
        with open(setting_path, 'w') as f:
            f.write(content)

    if not os.path.exists(node_path):
        logger.info('generaotr_node_setting_files: path=%s, content:%s', node_path, school_uuid)
        with open(node_path, 'w') as f:
            f.write(str(school_uuid))


N = 0


def rebuild_synclog():
    from BanBanTong.db import models as m1
    from machine_time_used import models as m2
    from django.db import connection

    def fix_info():
        term = m1.Term.get_current_term_list()[0]
        teacherlogintime = m1.TeacherLoginTime.objects.filter(school_year=term.school_year, term_type=term.term_type)
        for obj in teacherlogintime:
            if obj.login_time != obj.teacherloginlog.login_time:
                obj.teacherloginlog.login_time = obj.login_time
                obj.teacherloginlog.save()

    def add_synclog(obj, operation_type='add'):
        m1.SyncLog.add_log(obj, operation_type)
        global N
        N += 1
        if N % 500 == 0:
            logger.debug(u'重建SyncLog: %s', N)

    server_type = m1.Setting.getvalue('server_type')
    if server_type != 'school':
        raise ValueError('Wrong Sserver Type: %s' % server_type)

    fix_info()
    cursor = connection.cursor()
    cursor.execute('TRUNCATE TABLE synclog')

    term = m1.Term.get_current_term_list()[0]
    add_synclog(term, 'update')

    school = m1.Group.objects.get(group_type='school')
    add_synclog(school, 'update')

    lessons = m1.LessonName.objects.filter(school=school)
    for obj in lessons:
        add_synclog(obj, 'update')

    teachers = m1.Teacher.objects.filter(school=school)
    for obj in teachers:
        add_synclog(obj, 'update')

    grades = m1.Grade.objects.filter(term=term)
    for obj in grades:
        add_synclog(obj, 'update')

    classes = m1.Class.objects.filter(grade__in=grades)
    for obj in classes:
        add_synclog(obj, 'update')

    macs = m1.ClassMacV2.objects.filter(class_uuid__in=classes)
    for obj in macs:
        add_synclog(obj, 'update')

    classtimes = m1.ClassTime.objects.filter(class_uuid__in=classes)
    for obj in classtimes:
        add_synclog(obj, 'update')

    computerclasses = m1.ComputerClass.objects.filter(class_bind_to__in=classes)
    for obj in computerclasses:
        add_synclog(obj, 'update')

    computerclass_lessonranges = m1.ComputerClassLessonRange.objects.filter(computerclass__in=computerclasses)
    for obj in computerclass_lessonranges:
        add_synclog(obj, 'update')

    lessonperiod = m1.LessonPeriod.objects.filter(term=term)
    for obj in lessonperiod:
        add_synclog(obj, 'update')
    lessonschedule = m1.LessonSchedule.objects.filter(class_uuid__in=classes)
    for obj in lessonschedule:
        add_synclog(obj, 'update')
    lessonteacher = m1.LessonTeacher.objects.filter(class_uuid__in=classes)
    for obj in lessonteacher:
        add_synclog(obj, 'update')

    teacherloginlog = m1.TeacherLoginLog.objects.filter(term=term)
    for obj in teacherloginlog:
        add_synclog(obj)

    teacherlogintime = m1.TeacherLoginTime.objects.filter(school_year=term.school_year, term_type=term.term_type)
    for obj in teacherlogintime:
        add_synclog(obj)

    teacherloginlogtag = m1.TeacherLoginLogTag.objects.filter(created_at__in=classes)
    for obj in teacherloginlogtag:
        add_synclog(obj)

    teacherloginlogcourseware = m1.TeacherLoginLogCourseWare.objects.filter(school_year=term.school_year, term_type=term.term_type)
    for obj in teacherloginlogcourseware:
        add_synclog(obj.courseware)
        add_synclog(obj)

    desktoppicinfo = m1.DesktopPicInfo.objects.filter(school_year=term.school_year, term_type=term.term_type)
    for obj in desktoppicinfo:
        add_synclog(obj)

    desktoppicinfotag = m1.DesktopPicInfoTag.objects.filter(created_by__in=classes)
    for obj in desktoppicinfotag:
        add_synclog(obj)

    assettype = m1.AssetType.objects.filter(school=school)
    for obj in assettype:
        add_synclog(obj)
    asset = m1.Asset.objects.filter(school=school)
    for obj in asset:
        add_synclog(obj)
    assetlog = m1.AssetLog.objects.filter(school=school)
    for obj in assetlog:
        add_synclog(obj)
    assetrepairlog = m1.AssetRepairLog.objects.filter(school=school)
    for obj in assetrepairlog:
        add_synclog(obj)

    machinetimeused = m2.MachineTimeUsed.objects.filter(term_school_year=term.school_year, term_type=term.term_type)
    for obj in machinetimeused:
        add_synclog(obj)


@DISPATCHERS.register
class SyncDispather(DispatcherBase):
    name = 'SyncDispather'
    slug = '/ws/sync'
    allowed_categories = ['sync']
    allowed_server_types = ['school', 'country', 'city', 'province']
    properties = {'key': None, 'log_datetime': None, 'node': None, 'sync-data-length': 256}

    def dispatch(self, connect, connects, server, msgdict):
        self.log = server['factory'].log
        if 'operation' not in msgdict:
            return {'ret': 1001, 'msg': '错误的指令格式'}

        elif msgdict['operation'] == 'login':
            ret = self.process_login(connect, connects, server, msgdict)

        # 不需要登录的指令
        elif msgdict['operation'] == 'remote-data':
            ret = self.process_remote_data(connect, connects, server, msgdict)

        elif msgdict['operation'] == 'reset-last-upload-id':
            ret = self.process_reset_lastuploadid(connect, connects, server, msgdict)

        elif msgdict['operation'] == 'reset-synclog':
            ret = self.process_reset_synclog(connect, connects, server, msgdict)

        # 需要登录的指令
        else:
            if connect['login'] is not True:
                connect['should_close'] = True
                return {'ret': 1000, 'msg': '客户端未登录或登录状态获取失败'}
            else:
                d = {
                    'query-id': self.process_query_id,
                    'sync-cache': self.process_sync_cache,
                    'sync-data': self.process_sync_data,
                    'sync-misc': self.process_sync_misc,
                }
                try:
                    ret = d[msgdict['operation']](connect, connects, server, msgdict)
                except KeyError:
                    return {'ret': 1001, 'msg': '错误的指令格式(operation)'}
                except Exception as e:
                    self.log.exception(e)
                    ret = None

        if isinstance(ret, dict) and not ret.get('slug'):
            ret['slug'] = self.slug
        return ret

    def verify_node(self, key, connect, **kw):
        node_name = kw.get('group_name')
        node = None
        try:
            node = models.Node.objects.get(communicate_key=key)
        except models.Node.DoesNotExist:
            connect['should_close'] = True
            objs = models.Node.objects.filter(name=node_name)
            now = datetime.datetime.now()
            if objs.count() == 1:
                node = objs.first()
                # 离线超过3天的节点给出提示
                if node.last_active_time and (now - node.last_active_time).days > 3 or settings.DEBUG:
                    self.log.warning(u'KEY: %s\t服务器: %s 密钥校验失败\n', key, node_name)
                    node.last_active_time = datetime.datetime.combine(now, datetime.time.min)
                    node.sync_status = -2
                    node.save()

            elif objs.exists():
                self.log.error(u'KEY: %s\t服务器: %s 密钥校验失败, 发现重名节点.\n', key, node_name)

            else:
                self.log.debug(u'KEY: %s\t服务器: %s 密钥校验失败\n', key, node_name)

            return False, node, {'ret': 1002, 'msg': u'错误的连接密钥'}

        except Exception as e:
            self.log.exception(e)
            return False, node, {'ret': 1002, 'msg': u'Internal Server Error: %s' % e}

        else:
            return True, node, None

    def verify_connect(self, node, key, connect, connects):
        # 检测密钥连接
        dispatchs = {k: v for k, v in connects.items() if isinstance(v['dispatch'], self.__class__) and k != connect['sessionno']}
        conn_sum = 1
        for d in dispatchs.values():
            if d['properties']['key'] == key and d['properties']['node'].pk != node.pk:
                connect['should_close'] = True
                connect['key'] = key
                self.log.warning(
                    u'KEY: %s\t'
                    u'异常原因: 已有连接使用同样的密钥登录\n'
                    u'服务器: %s 连接密钥冲突\n'
                    u'当前连接服务器ID: %s', key, node.name, d['properties']['node'].pk)
                return False, {'ret': 1002, 'msg': u'已有连接使用同样的密钥登录.'}

            elif d['properties']['key'] == key:
                conn_sum += 1

        # 回传的时候服务器可能还建立了一个连接, 所以最大连接数可能为2
        if conn_sum > 2:
            connect['should_close'] = True
            connect['key'] = key
            self.log.warning(
                u'KEY: %s\t'
                u'异常原因: 已有连接使用同样的密钥登录, 当前连接数: %s\n'
                u'服务器: %s 连接数异常\n'
                u'当前连接服务器ID: %s', key, conn_sum, node.name, connect['properties']['node'])
            return False, {'ret': 1002, 'msg': u'连接数异常.'}
        return True, None

    def check_servertype(self, connect, allowed_types=None):
        try:
            server_type = models.Setting.objects.get(name='server_type').value
        except models.Setting.DoesNotExist:
            connect['should_close'] = True
            self.log.warning(u'服务器配置缺失(SERVER_TYPE).')
            return False, {'ret': 1002, 'msg': u'服务器配置缺失(SERVER_TYPE)'}
        except Exception as e:
            self.log.exception(e)
            return False, {'ret': 1002, 'msg': u'Internal Server Error: %s' % e}
        else:
            allowed_types = allowed_types or self.allowed_server_types
            if server_type not in allowed_types:
                return False, {'ret': 1002, 'msg': u'服务器配置异常(SERVER_TYPE), 或连接了错误的服务器.'}
            return True, None

    def process_login(self, connect, connects, server, msgdict):
        try:
            key = msgdict['data']['key']
            uuid = msgdict['data']['uuid']
            # parent_uuid = msgdict['data']['parent']['uuid']
            used_quota = msgdict['data']['used_quota']
            server_type = msgdict['data']['server_type']
            synclog_max_id = msgdict['data']['synclog_max_id']
            db_version = msgdict['data']['db_version']
            group_name = msgdict['data'].get('name', '')
        except KeyError as e:
            connect['should_close'] = True
            self.log.exception(u'KeyError: %s', e)
            return {'ret': 1001, 'msg': u'错误的指令格式'}

        # 检测密钥
        ok, node, err_msg = self.verify_node(key, connect, group_name=group_name)
        if not ok:
            return err_msg

        # 1.1 更新最后连接时间
        node.last_active_time = datetime.datetime.now()
        node.save()

        # 检测密钥连接
        ok, err_msg = self.verify_connect(node, key, connect, connects)
        if not ok:
            return err_msg

        # 检测激活信息
        is_active, active_status, info = has_activate()
        # 1 配额自动恢复
        if node.sync_status == -6 and used_quota <= node.activation_number:
            node.sync_status = 0
            node.save()
            self.log.info(u'服务器: %s 配额恢复正常, 同步状态恢复为0', node.name)

        # 激活状态自动恢复
        elif node.sync_status == -7 and (is_active and active_status == 'on'):
            node.sync_status = 0
            node.save()
            self.log.info(u'服务器: %s 已激活, 同步状态恢复为0', node.name)

        # 4.0 检测节点状态
        if node.sync_status not in (-2, -8, -9, 0):
            connect['should_close'] = True
            self.log.debug(
                u'KEY: %s\t异常原因: 服务器同步状态异常 %s\n'
                u'服务器: %s 状态异常: %s\n'
                u'连接信息: %s\n', key, node.sync_status, node.name, node.sync_status, connect['properties'])
            return {'ret': 1002, 'msg': u'服务器同步状态校验失败(%s).' % node.sync_status}

        # 4.1 检测GROUP_UUID
        # 下级发送的uuid与上级Setting.node_%d_school_uuid已有记录不一致
        obj, is_new = models.Setting.objects.get_or_create(name='node_%d_school_uuid' % node.id)
        if is_new:
            obj.value = uuid
            obj.save()

        elif obj.value != uuid:
            node.sync_status = -1
            node.save()
            connect['should_close'] = True
            self.log.warning(
                u'KEY: %s\t'
                u'异常原因: 下级发送的UUID与上级Setting.node_UUID_school_uuid已有记录不一致\n'
                u'服务器: %s 状态异常: -1\n'
                u'数据库保存的值: %s\n'
                u'下级服务器传值: %s\n'
                u'可能原因: 下级服务器未通过回传重装/使用了错误的连接密钥/回传安装失败.\n', key, node.name, obj.value, uuid)
            return {'ret': 1002, 'msg': u'服务器UUID校验失败.'}

        # 4.3 检测SERVER_TYPE
        server_types = ['client', 'school', 'country', 'city', 'province']
        if server_types.index(server_type) + 1 != server_types.index(server['server_type']):
            node.sync_status = -3
            node.save()
            connect['should_close'] = True
            self.log.warning(
                u'KEY: %s\t'
                u'异常原因: 服务器级别不匹配.\n'
                u'服务器: %s 状态异常: %s\n'
                u'上级服务器级别: %s\n'
                u'下级服务器传值: %s\n', key, node.name, node.sync_status, server['server_type'], server_type
            )
            return {'ret': 1002, 'msg': u'服务器级别校验失败.'}

        # 4.5 下级同步ID
        if synclog_max_id < node.last_upload_id:
            # node.sync_status = -5
            # node.save()
            # connect['should_close'] = True
            self.log.warning(
                u'KEY: %s\t'
                u'异常原因: 下级synclog_max_id比上级last_upload_id小.\n'
                u'服务器: %s 状态异常: %s\n'
                u'上级服务器保存的值: %s\n'
                u'下级服务器传值: %s\n', key, node.name, node.sync_status, node.last_upload_id, synclog_max_id
            )
            # return {'ret': 1002, 'msg': u'服务器同步ID校验失败.'}

        # 4.6 检测配额
        if used_quota > node.activation_number:
            node.sync_status = -6
            node.save()
            connect['properties']['used_quota'] = used_quota
            connect['should_close'] = True
            self.log.warning(
                u'KEY: %s\t'
                u'异常原因: 校级分配点数小于实际使用量.\n'
                u'服务器: %s 状态异常: %s\n'
                u'上级服务器保存的值: %s\n'
                u'下级服务器传值: %s\n', key, node.name, node.sync_status, node.activation_number, used_quota
            )
            return {'ret': 1002, 'msg': u'服务器配额设置不足(%s, %s).' % (node.activation_number, used_quota)}

        # 4.7 检测激活状态
        if not (is_active and active_status == 'on'):
            node.sync_status = -7
            node.save()
            connect['should_close'] = True
            self.log.warning(
                u'KEY: %s\t'
                u'异常原因: 县级服务器尚未激活或激活已过期.\n'
                u'服务器: %s 状态异常: %s\n', key, node.name, node.sync_status
            )
            return {'ret': 1002, 'msg': u'县级服务器尚未激活或激活已过期.'}

        # 4.8 重置同步ID
        if node.sync_status == -8:
            self.log.warning(
                u'KEY: %s\t'
                u'服务器: %s 状态异常: %s 异常原因: 下级服务器同步异常, 需要重置同步ID到一个合理的值.\n', key, node.name, node.sync_status
            )
            return {'ret': 0, 'category': 'sync', 'operation': 'refresh-synclogid'}

        if node.sync_status == -9:
            self.log.warning(
                u'KEY: %s\t'
                u'服务器: %s 状态异常: %s 异常原因: 下级服务器同步异常, 可能存在多个学期数据, 需要重建SyncLog表.\n', key, node.name, node.sync_status
            )
            return {'ret': 0, 'category': 'sync', 'operation': 'rebuild-synclog'}

        if node.sync_status == -2:
            node.sync_status = 0
            node.save()
            self.log.info(u'服务器: %s 连接密钥已修正, 同步状态恢复为0', node.name)

        connect['login'] = True
        connect['properties']['key'] = key
        connect['properties']['node'] = node
        connect['properties']['group_name'] = group_name
        node.db_version = db_version
        node.save()
        return {'ret': 0, 'operation': 'login-ret'}

    def process_query_id(self, connect, connects, server, msgdict):
        if not connect['login']:
            return
        node = connect['properties']['node']
        ws.cache.set_online(node.pk)
        # 调试模式
        if ws.cache.server_in_debug_mode() and node.pk not in ws.cache.server_allow_nodes():
            return

        # 线程正在处理同步的数据
        if ws.cache.get_sync(node.pk):
            self.log.debug('node-sync-in-progress:%s', node.pk)
            return
        try:
            node = models.Node.objects.get(pk=node.pk)
        except models.Node.DoesNotExist:
            connect['should_close'] = True
        except Exception as e:
            self.log.exception(e)
        connect['properties']['node'] = node
        return {'ret': 0, 'operation': 'query-id-ret', 'last_upload_id': node.last_upload_id}

    def process_sync_cache(self, connect, connects, server, msgdict):
        if not connect['login']:
            return
        node = connect['properties']['node']
        ws.cache.set_online(node.pk)
        is_active, active_status, info = has_activate()
        # 县级没有激活,所有的连接停止同步
        if not (is_active and active_status == 'on'):
            node.sync_status = -7
            node.save()
            return
        elif node.sync_status == -7:
            node.sync_status = 0
            node.save()

        for k in msgdict['data']:
            timeout = get_timeout(k, 'null')
            if timeout == 'null':
                cache.set(k, msgdict['data'][k])
            else:
                cache.set(k, msgdict['data'][k], timeout)

    def process_sync_data(self, connect, connects, server, msgdict):
        """上级服务器处理同步数据"""
        if not connect['login']:
            return
        node = connect['properties']['node']
        ws.cache.set_online(node.pk)
        if ws.cache.server_in_debug_mode() and node.pk not in ws.cache.server_allow_nodes():
            return

        try:
            node = models.Node.objects.get(pk=node.pk)
        except models.Node.DoesNotExist:
            connect['should_close'] = True
        except Exception as e:
            self.log.exception(e)
        else:
            is_active, active_status, info = has_activate()
            # 县级没有激活,所有的连接停止同步
            if not (is_active and active_status == 'on'):
                node.sync_status = -7
                node.save()
                return
            elif node.sync_status == -7:
                node.sync_status = 0
                node.save()
            if django_rq is None:
                raise ImportError('No module named django_rq')
            if not ws.cache.get_sync(node.pk):
                self.log.debug('enqueue: node=%s, records=%s', node.name, len(msgdict['data']['records']))
                ws.cache.set_sync(node.id)
                try:
                    node.last_upload_time = datetime.datetime.now()
                    node.save()
                except Exception as e:
                    self.log.exception(e)
                django_rq.enqueue(save_data_into_db, node.pk, msgdict['data']['records'])

    def process_sync_misc(self, connect, connects, server, msgdict):
        if not connect['login']:
            return
        try:
            node = connect['properties']['node']
            items = [
                msgdict['data']['Setting'],
                msgdict['data']['Role'],
                msgdict['data']['RolePrivilege'],
                msgdict['data']['User'],
                msgdict['data']['UsbkeyTeacher'],
                msgdict['data']['Node']
            ]
            with open(os.path.join(constants.CACHE_TMP_ROOT, '%s.setting' % node.id), 'w') as f:
                f.write('\n'.join(items))

            with open(os.path.join(constants.CACHE_TMP_ROOT, '%s.node' % node.id), 'w') as f:
                for uu in msgdict['data']['school-uuids'].split(','):
                    f.write(uu + '\n')
        except Exception as e:
            self.log.exception(e)

    def process_remote_data(self, connect, connects, server, msgdict):
        '''
            0. 服务器收到这个指令时，首先检查当前连接的所有客户端是否有使用这个key的连接
            1. 首先检查是否存在已打包或正在打包的操作
            2. 如果有已打包的数据，就直接回复给客户端
            3. 如果正在打包，就忽略，等到打包完成时程序会自己回调发送数据
            4. 如果没有打包，就开始进行打包操作
                1) 打包是耗时操作，放在很多个Deferred里做，避免长时间阻塞服务器
            5. 打包完成后，如果客户端连接还在，就直接发送数据
            6. 如果客户端已断线，就把数据放在内存里等下次连上来再发送
            cache结构：
                '密钥': {
                    'status': 1（正在打包） 2（打包完成）,
                    'datetime': 生成打包数据的时间,
                    'data': data数据,
                    'syllabus': syllabus数据,
                }
        '''
        try:
            key = msgdict['data']['key']
        except KeyError as e:
            connect['should_close'] = True
            self.log.exception(u'KeyError: %s, msgdict=%s', e, msgdict)
            return {'ret': 1001, 'msg': u'错误的指令格式'}
        except Exception as e:
            self.log.exception('msgdict=%s, e=%s', msgdict, e)
            return {'ret': 1001, 'msg': u'Internal Server Error: %s' % e}

        if cache.get('server_statys') == 'maintain':
            msg = cache.get('server_statys_msg')
            self.log.warning(u'KEY: %s\t收到回传请求: 但是服务器处于维护状态 %s', key)
            return {'ret': 503, 'msg': msg or u'服务器维护中.'}

        # 检测密钥
        ok, node, err_msg = self.verify_node(key, connect, group_name=connect['properties'].get('group_name'))
        if not ok:
            err_msg.update({'ret': 1002, 'operation': 'remote-data-ret'})
            return err_msg

        # 检测密钥连接
        ok, err_msg = self.verify_connect(node, key, connect, connects)
        if not ok:
            err_msg.update({'ret': 1005, 'operation': 'remote-data-ret'})
            return err_msg

        # 检测服务器级别连接
        ok, err_msg = self.check_servertype(connect, allowed_types=['country', 'city', 'province'])
        if not ok:
            err_msg.update({'ret': 1005, 'operation': 'remote-data-ret'})
            return err_msg

        connect['properties']['node'] = node
        try:
            # 2 获取县服务器下保存的学校的配置信息
            generaotr_node_setting_files(node)
            fpath = os.path.join(constants.CACHE_TMP_ROOT, '%s.node' % node.id)
            if not os.path.exists(fpath):
                self.log.warning(
                    u'KEY: %s\t'
                    u'回传异常: 获取节点的.NODE文件失败\n'
                    u'服务器名: %s\n'
                    u'文件路径: %s', key, node.name, fpath
                )
                return {'ret': 1001, 'msg': u'上级服务器没有.node文件'}
            with open(fpath) as f:
                uuids = [line.strip('\r\n') for line in f]
                school = models.Group.objects.get(group_type='school', name=node.name)
                uuids.append(school.pk)
        except IOError as e:
            connect['should_close'] = True
            self.log.error(e)
            return {'ret': 1001, 'msg': u'NODE文件读取失败'}
        except Exception as e:
            self.log.exception(e)
            return {'ret': 1001, 'msg': u'内部服务器错误'}

        try:
            # 3.1 如果是新装,那么先初始化一下缓存为打包基础信息作准备
            if key not in server['caches']['restore-data']:
                server['caches']['restore-data'][key] = {
                    'status': 0, 'datetime': datetime.datetime.now(),
                    'data': '', 'count': 0, 'syllabus': '',
                }

            # 3.2 如果是回传,那么判断一下数据打包的状态
            else:
                if server['caches']['restore-data'][key]['status'] == 999:
                    # 打包完成: 直接发送, 将学校的同步id置1, 变更同步密钥
                    new_key = str_util.generate_node_key()
                    data = {'ret': 0, 'data': {
                        'data': server['caches']['restore-data'][key]['data'],
                        'syllabus': server['caches']['restore-data'][key]['syllabus'],
                        'key': new_key
                    }}
                    # if 'callback' in msgdict:
                    #    data['callback'] = msgdict['callback']
                    try:
                        connect['connect'].sendMessage(data)
                    except Exception as e:
                        self.log.warning(u'缓存里有数据，直接发送, 出现异常. e=%s', e)
                        self.log.exception(e)
                    else:
                        self.log.info(u'数据发送完成. 更新节点连接密钥: %s --> %s', node.communicate_key, new_key)
                        node.communicate_key = new_key
                        node.last_upload_id = 1
                        node.save()
                        server['caches']['restore-data'][new_key] = server['caches']['restore-data'][key]
                    return
                else:
                    # 正在打包: 继续...
                    # print '打包已在进行中，完成后将发送数据。这里不再重复打包'
                    # msg = u'等待上级服务器继续打包'
                    # connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'progress': msg})

                    msg = u'等待上级服务器继续打包'
                    self.log.debug(msg)
                    connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'progress': msg})
                    return

            # 新装或者正在打包,那么就走下面的流程.
            # 4.0 初始化deferToThread
            def _init_defertothread():
                def _worker():
                    try:
                        if server['caches']['restore-data'][key]['status'] > 0:
                            return
                        msg = u'上级打包：0. 初始化deferToThread'
                        self.log.info(msg)
                        connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'progress': msg})
                    except Exception as e:
                        logger.exception(e)
                        raise

                return threads.deferToThread(_worker)

            # 4.1 打包学校的Group表数据
            def _step_1_group(*args):
                def _worker():
                    try:
                        if server['caches']['restore-data'][key]['status'] >= 1:
                            return
                        msg = u'上级打包：1. Group'
                        self.log.info(msg)
                        connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'progress': msg})

                        data, count = ws.dbapi.backup_group(uuids)
                        server['caches']['restore-data'][key]['status'] = 1
                        server['caches']['restore-data'][key]['datetime'] = datetime.datetime.now()
                        server['caches']['restore-data'][key]['data'] = data
                        server['caches']['restore-data'][key]['count'] = count
                    except Exception as e:
                        logger.exception(e)
                        raise

                return threads.deferToThread(_worker)

            # 4.2 打包学校的授课教师数据
            def _step_2_teacher(*args):
                def _worker():
                    try:
                        if server['caches']['restore-data'][key]['status'] >= 2:
                            return
                        msg = u'上级打包：2. Teacher'
                        self.log.info(msg)
                        connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'progress': msg})

                        data, count = ws.dbapi.backup_teacher(uuids)
                        server['caches']['restore-data'][key]['status'] = 2
                        server['caches']['restore-data'][key]['datetime'] = datetime.datetime.now()
                        server['caches']['restore-data'][key]['data'] += data
                        server['caches']['restore-data'][key]['count'] += count
                    except Exception as e:
                        logger.exception(e)
                        raise
                return threads.deferToThread(_worker)

            # 4.3 打包学校的资产管理部分的数据
            def _step_3_assets(*args):
                def _worker():
                    try:
                        if server['caches']['restore-data'][key]['status'] >= 3:
                            return
                        msg = u'上级打包：3. Assets'
                        self.log.info(msg)
                        connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'progress': msg})

                        data, count = ws.dbapi.backup_assets(uuids)
                        server['caches']['restore-data'][key]['status'] = 3
                        server['caches']['restore-data'][key]['datetime'] = datetime.datetime.now()
                        server['caches']['restore-data'][key]['data'] += data
                        server['caches']['restore-data'][key]['count'] += count
                    except Exception as e:
                        logger.exception(e)
                        raise
                return threads.deferToThread(_worker)

            # 4.4 打包学校的年级班级的数据
            def _step_4_class(*args):
                def _worker():
                    try:
                        # Term/Grade/Class/ComputerClass/ClassMacV2/ClassTime
                        if server['caches']['restore-data'][key]['status'] >= 4:
                            return
                        msg = u'上级打包：4. Class'
                        self.log.info(msg)
                        connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'progress': msg})

                        data, count = ws.dbapi.backup_class(uuids)
                        server['caches']['restore-data'][key]['status'] = 4
                        server['caches']['restore-data'][key]['datetime'] = datetime.datetime.now()
                        server['caches']['restore-data'][key]['data'] += data
                        server['caches']['restore-data'][key]['count'] += count
                    except Exception as e:
                        logger.exception(e)
                        raise
                return threads.deferToThread(_worker)

            # 4.5 打包学校的课程/节次/课表的数据
            def _step_5_lesson(*args):
                def _worker():
                    try:
                        # LessonName/ComputerClassLessonRange/LessonPeriod/LessonSchedule/LessonTeacher
                        if server['caches']['restore-data'][key]['status'] >= 5:
                            return
                        msg = u'上级打包：5. Lesson'
                        self.log.info(msg)
                        connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'progress': msg})

                        data, count = ws.dbapi.backup_lesson(uuids)
                        server['caches']['restore-data'][key]['status'] = 5
                        server['caches']['restore-data'][key]['datetime'] = datetime.datetime.now()
                        server['caches']['restore-data'][key]['data'] += data
                        server['caches']['restore-data'][key]['count'] += count
                    except Exception as e:
                        logger.exception(e)
                        raise
                return threads.deferToThread(_worker)

            # 4.6 打包学校的教师登录日志
            def _step_6_loginlog(*args):
                def _worker():
                    try:
                        # TeacherLoginLog/TeacherLoginLogTag/TeacherLoginTime
                        if server['caches']['restore-data'][key]['status'] >= 6:
                            return
                        msg = u'上级打包：6. 登录日志'
                        self.log.info(msg)
                        connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'progress': msg})

                        data, count = ws.dbapi.backup_loginlog(uuids)
                        server['caches']['restore-data'][key]['status'] = 6
                        server['caches']['restore-data'][key]['datetime'] = datetime.datetime.now()
                        server['caches']['restore-data'][key]['data'] += data
                        server['caches']['restore-data'][key]['count'] += count
                    except Exception as e:
                        logger.exception(e)
                        raise
                return threads.deferToThread(_worker)

            # 4.7 打包学校的未登录日志
            def _step_7_absentlog(*args):
                def _worker():
                    try:
                        # TeacherAbsentLog
                        if server['caches']['restore-data'][key]['status'] >= 7:
                            return
                        msg = u'上级打包：7. 未登录日志'
                        self.log.info(msg)
                        connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'progress': msg})

                        data, count = ws.dbapi.backup_absentlog(uuids)
                        server['caches']['restore-data'][key]['status'] = 7
                        server['caches']['restore-data'][key]['datetime'] = datetime.datetime.now()
                        server['caches']['restore-data'][key]['data'] += data
                        server['caches']['restore-data'][key]['count'] += count
                    except Exception as e:
                        logger.exception(e)
                        raise
                return threads.deferToThread(_worker)

            # 4.8 打包学校的桌面截图日志
            def _step_8_desktoppic(*args):
                def _worker():
                    try:
                        # DesktopPicInfo/DesktopPicInfoTag/DesktopGlobalPreview/DesktopGlobalPreviewTag
                        if server['caches']['restore-data'][key]['status'] >= 8:
                            return
                        msg = u'上级打包：8. 桌面截图'
                        self.log.info(msg)
                        connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'progress': msg})

                        data, count = ws.dbapi.backup_desktoppic(uuids)
                        server['caches']['restore-data'][key]['status'] = 8
                        server['caches']['restore-data'][key]['datetime'] = datetime.datetime.now()
                        server['caches']['restore-data'][key]['data'] += data
                        server['caches']['restore-data'][key]['count'] += count
                    except Exception as e:
                        logger.exception(e)
                        raise
                return threads.deferToThread(_worker)

            # 4.9 打包学校的教材大纲数据
            def _step_9_courseware(*args):
                def _worker():
                    try:
                        # CourseWare/TeacherLoginLogCourseWare/TeacherLoginLogLessonContent
                        if server['caches']['restore-data'][key]['status'] >= 9:
                            return
                        msg = u'上级打包：9. courseware'
                        self.log.info(msg)
                        connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'progress': msg})

                        data, count = ws.dbapi.backup_courseware(uuids)
                        server['caches']['restore-data'][key]['status'] = 9
                        server['caches']['restore-data'][key]['datetime'] = datetime.datetime.now()
                        server['caches']['restore-data'][key]['data'] += data
                        server['caches']['restore-data'][key]['count'] += count
                    except Exception as e:
                        logger.exception(e)
                        raise
                return threads.deferToThread(_worker)

            # 4.10 打包学校的课程资源数据
            def _step_10_resource(*args):
                def _worker():
                    try:
                        # ResourceFrom/ResourceType
                        if server['caches']['restore-data'][key]['status'] >= 10:
                            return
                        msg = u'上级打包：10. resource'
                        self.log.info(msg)
                        connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'progress': msg})

                        data, count = ws.dbapi.backup_resource(uuids)
                        server['caches']['restore-data'][key]['status'] = 10
                        server['caches']['restore-data'][key]['datetime'] = datetime.datetime.now()
                        server['caches']['restore-data'][key]['data'] += data
                        server['caches']['restore-data'][key]['count'] += count
                    except Exception as e:
                        logger.exception(e)
                        raise
                return threads.deferToThread(_worker)

            # 4.11 打包学校的服务器配置数据
            def _step_11_setting(*args):
                def _worker():
                    try:
                        # Setting/User/Role/RolePrivilege/Node/UsbkeyTeacher
                        if server['caches']['restore-data'][key]['status'] >= 11:
                            return
                        msg = u'上级打包：11. setting'
                        self.log.info(msg)
                        connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'progress': msg})

                        data, count = ws.dbapi.backup_setting(node)
                        server['caches']['restore-data'][key]['status'] = 11
                        server['caches']['restore-data'][key]['datetime'] = datetime.datetime.now()
                        server['caches']['restore-data'][key]['data'] += data
                        server['caches']['restore-data'][key]['count'] += count
                    except Exception as e:
                        logger.exception(e)
                        raise
                return threads.deferToThread(_worker)

            # 4.12 打包同步数据
            def _step_12_syllabus(*args):
                def _worker():
                    try:
                        if server['caches']['restore-data'][key]['status'] >= 12:
                            return
                        msg = u'上级打包：12. syllabus'
                        self.log.info(msg)
                        connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'progress': msg})

                        syllabus = models.CountryToSchoolSyncLog.pack_all_data()
                        server['caches']['restore-data'][key]['status'] = 12
                        server['caches']['restore-data'][key]['datetime'] = datetime.datetime.now()
                        server['caches']['restore-data'][key]['syllabus'] = syllabus
                    except Exception as e:
                        logger.exception(e)
                        raise
                return threads.deferToThread(_worker)

            # 4.13 打包机器时长数据
            def _step_13_machinetimeused(*args):
                def _worker():
                    try:
                        if server['caches']['restore-data'][key]['status'] >= 13:
                            return
                        msg = u'上级打包：13. 终端时长'
                        self.log.info(msg)
                        connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'progress': msg})

                        data, count = ws.dbapi.backup_machinetimeused(uuids)
                        server['caches']['restore-data'][key]['status'] = 13
                        server['caches']['restore-data'][key]['datetime'] = datetime.datetime.now()
                        server['caches']['restore-data'][key]['data'] += data
                        server['caches']['restore-data'][key]['count'] += count
                    except Exception as e:
                        logger.exception(e)
                        raise
                return threads.deferToThread(_worker)

            # 4.13 打包学校的授权激活的配额信息
            def _step_14_activate_info(*args):
                def _worker():
                    msg = u'上级打包：14. 授权激活的配额'
                    self.log.info(msg)
                    try:
                        if server['caches']['restore-data'][key]['status'] >= 14:
                            return
                        connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'progress': msg})

                        data, count = ws.dbapi.backup_activate_quota(node)
                        server['caches']['restore-data'][key]['status'] = 14
                        server['caches']['restore-data'][key]['datetime'] = datetime.datetime.now()
                        server['caches']['restore-data'][key]['data'] += data
                        server['caches']['restore-data'][key]['count'] += count
                    except Exception as e:
                        logger.exception(e)
                        raise
                return threads.deferToThread(_worker)

            # 5 发送数据
            def _step_999_senddata(*args):
                # 注意这里打包完成成功发送数据包和修改连接密钥之间并没有直接的
                # 因果关系,这里的两个步骤实际上只是执行时间上的先后,
                # 所以可能出现的情况就是,打包完成,尝试发送数据给校级结果中途失败了.
                # 然而连接密钥依然是会被更新的,所以在校级尝试断线重连的时候
                # 就会出现 '错误的密钥' 的提示,
                # 当网络连接不稳定或者服务器性能状态差的时候可能会出现这个现象.
                # 这里记录在此.
                def _worker():
                    try:
                        # 发送数据
                        data = server['caches']['restore-data'][key]['data']
                        data = bz2.compress(data)
                        data = base64.b64encode(data)
                        server['caches']['restore-data'][key]['data'] = data
                        new_key = str_util.generate_node_key()
                        message = {'ret': 0, 'data': {
                            'data': data,
                            'syllabus': server['caches']['restore-data'][key]['syllabus'],
                            'key': new_key
                        }}

                        msg = u'打包完成, 请不要关闭浏览器. 数据传输中...'
                        self.log.info(msg)
                        connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'progress': msg})

                        try:
                            connect['connect'].sendMessage(message)
                        except Exception as e:
                            self.log.warning(u'打包完成，数据发送失败. e=%s', e)
                            self.log.exception(e)
                        else:
                            self.log.info(u'数据发送完成.\n更新节点连接密钥: %s --> %s', node.communicate_key, new_key)
                            node.communicate_key = new_key
                            node.last_upload_id = 1
                            node.save()
                            server['caches']['restore-data'][new_key] = server['caches']['restore-data'][key]

                        server['caches']['restore-data'][key]['status'] = 999
                        server['caches']['restore-data'][key]['datetime'] = datetime.datetime.now()
                    except Exception as e:
                        logger.exception(e)
                        raise
                return threads.deferToThread(_worker)

            def _failure(f):
                f.printTraceback()
                msg = u'出现异常，清除数据，下次重新打包'
                self.log.info(msg)
                del server['caches']['restore-data'][key]
                connect['connect'].sendClose()

            self.log.info(u'KEY: %s\tprocess_remote_data: 开始打包数据\n', key)
            d = _init_defertothread()
            d.addCallback(_step_1_group)
            d.addCallback(_step_2_teacher)
            d.addCallback(_step_3_assets)
            d.addCallback(_step_4_class)
            d.addCallback(_step_5_lesson)
            d.addCallback(_step_6_loginlog)
            # d.addCallback(_step_7_absentlog) # 锐哥说不要不要.
            d.addCallback(_step_8_desktoppic)
            d.addCallback(_step_9_courseware)
            d.addCallback(_step_10_resource)
            d.addCallback(_step_11_setting)
            d.addCallback(_step_12_syllabus)
            d.addCallback(_step_13_machinetimeused)
            d.addCallback(_step_14_activate_info)
            d.addCallback(_step_999_senddata)
            d.addErrback(_failure)

        except KeyError as e:
            self.log.warning(e)
            return {'ret': 1001, 'msg': '错误的指令'}
        except models.Node.DoesNotExist as e:
            self.log.warning(e)
            return {'ret': 1001, 'msg': '错误的密钥'}
        except IOError as e:
            self.log.warning(e)
            return {'ret': 1001, 'msg': '上级服务器没有.node文件'}
        except Exception as e:
            self.log.exception(e)
            return {'ret': 1001, 'msg': str(e)}

    def process_reset_lastuploadid(self, connect, connects, server, msgdict):
        created_at = msgdict['data'].get('created_at')
        key = msgdict['data'].get('key')
        if isinstance(created_at, int) and key:
            ok, node, err_msg = self.verify_node(key, connect)
            if not ok:
                return err_msg
            if node.sync_status == -8 and node.last_upload_id > created_at:
                old = node.last_upload_id
                self.log.warning(u'重置上级服务器同步ID: 服务器: %s, 学年学期: %s, 原值: %s, 新值: %s', node.name, msgdict['data'].get('term_id'), old, created_at)
                node.sync_status = 0
                node.last_upload_id = created_at
                node.save()
                connect['should_close'] = True
                return {'ret': 0, 'msg': u'重置上级服务器同步ID成功: 服务器: %s, 学年学期: %s, 原值: %s, 新值: %s' % (node.name, msgdict['data'].get('term_id'), old, created_at)}
            else:
                node.sync_status = 0
                node.save()
                connect['should_close'] = True
        else:
            self.log.warning(
                u'下级服务器获取同步ID失败: 服务器: %s, 学年学期: %s, 异常原因: %s\nmsgdict=%s',
                msgdict['data'].get('school'),
                msgdict['data'].get('term_id'),
                msgdict['data'].get('err'),
                msgdict
            )

    def process_reset_synclog(self, connect, connects, server, msgdict):
        school = msgdict['data'].get('school')
        key = msgdict['data'].get('key')
        ok = msgdict['data'].get('ok')
        self.log.debug('process_reset_synclog: school=%s, key=%s, ok=%s', school, key, ok)
        if ok:
            try:
                node = models.Node.objects.get(communicate_key=key)
            except models.Node.DoesNotExist:
                connect['should_close'] = True
                objs = models.Node.objects.filter(name=school)
                now = datetime.datetime.now()
                if objs.count() == 1:
                    node = objs.first()
                    # 离线超过3天的节点给出提示
                    if node.last_active_time and (now - node.last_active_time).days > 3 or settings.DEBUG:
                        self.log.warning(u'KEY: %s\t服务器: %s 密钥校验失败\n', key, school)
                        node.last_active_time = datetime.datetime.combine(now, datetime.time.min)
                        node.sync_status = -2
                        node.save()
            else:
                self.log.warning(u'下级服务器重置SyncLog表成功: 服务器: %s', school)
                connect['should_close'] = True
                node.sync_status = 0
                node.last_upload_id = 1
                node.save()

        else:
            self.log.warning(u'下级服务器重置SyncLog表失败: 服务器: %s, 密钥: %s, 异常原因: %s', school, key, msgdict['data'].get('err'))

    def consume(self, protocol, client, msgdict):
        self.log = protocol.factory.log
        self.log.debug('SyncDispather.consume: msgdict=%s', msgdict)
        d = {
            'login-ret': self.process_login_ret,
            'query-id-ret': self.process_update_data,
            'refresh-properties': self.process_update_properties,
            'refresh-synclogid': self.process_update_synclogid,
            'rebuild-synclog': self.process_rebuild_synclog,
        }
        try:
            return d[msgdict['operation']](protocol, client, msgdict)
        except:
            pass

    # 服务器登录成功
    def process_login_ret(self, protocol, client, msgdict):
        if msgdict['ret'] == 0:
            self.log.debug('WsClient.%s.login successfully.', client['properties']['node'])
            client['login'] = True
        else:
            client['login'] = False

    # 服务器打包上传数据
    def process_update_data(self, protocol, client, msgdict):
        if msgdict['ret'] == 0:
            last_upload_id = msgdict['last_upload_id']
            objs = models.SyncLog.objects.filter(created_at__gt=last_upload_id)
            if objs.exists():
                items = objs[:self.properties['sync-data-length']].values('created_at', 'operation_type', 'operation_content')
                records = [{
                    'created_at': i['created_at'],
                    'operation_type': i['operation_type'],
                    'operation_content': i['operation_content']
                } for i in items]
                return {'category': 'sync', 'operation': 'sync-data', 'data': {'records': records}}

    # 服务器更新配置
    def process_update_properties(self, protocol, client, msgdict):
        if msgdict['ret'] == 0:
            for k, v in msgdict['data'].items():
                self.properties[k] = v

    # 校级服务器上传SyncLog偏移量
    def process_update_synclogid(self, protocol, client, msgdict):
        try:
            term_id = models.Term.get_current_term_list()[0].pk
        except:
            return {'category': 'sync', 'operation': 'reset-last-upload-id', 'data': {'term_id': None, 'err': traceback.format_exc()}}
        else:
            content = '"pk": "%s", "model": "db.term"' % term_id
            objs = models.SyncLog.objects.filter(Q(operation_type='add', operation_content__contains=content) | Q(operation_type='update', operation_content__contains=content))
            if objs.exists():
                communicate_key = models.Setting.getvalue('sync_server_key')
                return {'category': 'sync', 'operation': 'reset-last-upload-id', 'data': {'term_id': term_id, 'created_at': objs.first().created_at, 'key': communicate_key}}
            else:
                school = models.Setting.getvalue('school')
                return {'category': 'sync', 'operation': 'reset-last-upload-id', 'data': {'term_id': term_id, 'err': 'Not SyncLog Exist.', 'school': school}}

    # 校级服务器重置SyncLog表
    def process_rebuild_synclog(self, protocol, client, msgdict):
        self.log.warning(u'收到重建SyncLog表命令')
        communicate_key = models.Setting.getvalue('sync_server_key')
        school = models.Setting.getvalue('school')
        if ws.cache.get_cache('rebuild_synclog_inprogress'):
            self.log.debug(u'收到重建SyncLog表命令, 已经在进行重建SyncLog了.')
            return

        elif ws.cache.get_cache('rebuild_synclog_finished'):
            self.log.debug(u'收到重建SyncLog表命令, 重建已经完成.')
            return {'category': 'sync', 'operation': 'reset-synclog', 'data': {'ok': True, 'school': school, 'key': communicate_key}}

        ws.cache.set_status('maintain')
        ws.cache.set_cache('rebuild_synclog_inprogress', True, 3600 * 24)
        try:
            rebuild_synclog()
        except ValueError:
            ws.cache.delete_cache('rebuild_synclog_inprogress')
            return {'category': 'sync', 'operation': 'reset-synclog', 'data': {'err': traceback.format_exc(), 'school': school, 'key': communicate_key}}
        except Exception:
            ws.cache.delete_cache('rebuild_synclog_inprogress')
            return {'category': 'sync', 'operation': 'reset-synclog', 'data': {'err': traceback.format_exc(), 'school': school, 'key': communicate_key}}
        else:
            ws.cache.set_status(None)
            ws.cache.delete_cache('rebuild_synclog_inprogress')
            ws.cache.set_cache('rebuild_synclog_finished', True, 3600 * 24 * 5)
            return {'category': 'sync', 'operation': 'reset-synclog', 'data': {'ok': True, 'school': school, 'key': communicate_key}}
