# coding=utf-8
import os
import bz2
import base64
import datetime
import ConfigParser
from django.conf import settings
from django.core.cache import cache
from twisted.internet import threads
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.views.system.install import _modify_update_path
from BanBanTong.views.system.install import _package_client_file
from BanBanTong.views.system.install import _truncate_tables
from BanBanTong.views.system.remote import _restore_syllabus
from ws.dispatchers import DISPATCHERS, DispatcherBase


@DISPATCHERS.register
class LocalserverDispather(DispatcherBase):
    name = 'LocalserverDispather'
    slug = '/ws/localserver'
    allowed_categories = ['localserver']
    allowed_server_types = ['', 'school', 'country', 'city', 'province']
    properties = {'key': None, 'log_datetime': None, 'node': None}
    all_nodes = None

    def dispatch(self, connect, connects, server, msgdict):
        self.log = server['factory'].log
        if 'operation' not in msgdict:
            return {'ret': 1001, 'msg': u'错误的指令格式'}

        else:
            d = {
                'restore': self.process_restore,
                'nodeinfo': self.process_nodeinfo,
                'ping': self.process_ping,
            }
            try:
                ret = d[msgdict['operation']](connect, connects, server, msgdict)
            except KeyError:
                return {'ret': 1001, 'msg': u'错误的指令格式(operation)'}
            except Exception as e:
                self.log.exception(e)
                ret = None

        if isinstance(ret, dict) and not ret.get('slug'):
            ret['slug'] = self.slug
        return ret

    def process_restore(self, connect, connects, server, msgdict):
        """数据回传：把数据写回本地数据库"""
        try:
            # 0.解包
            data = bz2.decompress(base64.b64decode(msgdict['data']['data']))
            syllabus = bz2.decompress(base64.b64decode(msgdict['data']['syllabus']))
            key = msgdict['data']['key']
            connect['properties']['key'] = key
            connect['properties']['log_datetime'] = datetime.datetime.now()
            lines = data.split('\n')
            total = len(lines)

            with open(os.path.join(constants.LOG_PATH, 'restore.log'), 'w') as f:
                f.write(syllabus + '\n')
                f.write(data)

            # 1.清空本地旧数据(保留必要数据)
            def _step_1_truncate():
                def _worker():
                    msg = u'本地处理：1. 清空旧数据'
                    self.log.info(msg)
                    connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'finished': False, 'progress': msg})
                    _truncate_tables()
                return threads.deferToThread(_worker)

            # 2.处理教学大纲数据
            def _step_2_syllabus(*args):
                def _worker():
                    msg = u'本地处理：2. 教学大纲'
                    self.log.info(msg)
                    connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'finished': False, 'progress': msg})
                    _restore_syllabus(syllabus)
                return threads.deferToThread(_worker)

            # 3.处理单条数据
            def _step_3_data(ignored, i):
                def _worker():
                    try:
                        if (datetime.datetime.now() - connect['properties']['log_datetime']).total_seconds() > 8 or settings.DEBUG:
                            msg = u'本地处理：3. 保存(%d/%d)' % (i + 1, total)
                            self.log.info(msg)
                            connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'finished': False, 'progress': msg})
                            connect['properties']['log_datetime'] = datetime.datetime.now()
                    except KeyError:
                        pass
                    except Exception as e:
                        self.log.exception(e)
                    if len(lines[i]) > 2:
                        # self.log.debug('unpack_log: %s', lines[i])
                        models.SyncLogPack.unpack_log('add', lines[i])
                return threads.deferToThread(_worker)

            # 4.更新校级连接密钥
            def _step_4_newkey(*args):
                def _worker():
                    msg = u'本地处理：4. 更新密钥'
                    self.log.info(msg)
                    connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'finished': False, 'progress': msg})
                    models.Setting.objects.filter(name='sync_server_key').delete()
                    models.Setting(name='sync_server_key', value=key).save()
                return threads.deferToThread(_worker)

            # 5.更新升级路径
            def _step_5_ini(*args):
                def _worker():
                    msg = u'本地处理：5. 更新升级路径'
                    self.log.info(msg)
                    connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'finished': False, 'progress': msg})
                    province = models.Group.objects.get(group_type='province').name
                    city = ''
                    country = ''
                    server_type = models.Setting.getvalue('server_type')
                    if server_type != 'province':
                        city = models.Group.objects.get(group_type='city').name
                        if server_type != 'city':
                            country = models.Group.objects.get(group_type='country').name
                    _modify_update_path(province, city, country)
                return threads.deferToThread(_worker)

            # 6.更新授课缓存
            def _step_6_lessonteacher(*args):
                def _worker():
                    msg = u'本地处理：6. 授课缓存'
                    self.log.info(msg)
                    connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'finished': False, 'progress': msg})
                    for obj in models.LessonTeacher.objects.all():
                        models.LessonTeacher.calculate_total_teachers(obj)
                return threads.deferToThread(_worker)

            # 7.处理客户端配置参数
            def _step_7_client(*args):
                def _worker():
                    server_type = models.Setting.getvalue('server_type')
                    if server_type != 'school':
                        return
                    msg = u'本地处理：7. 客户端'
                    self.log.info(msg)
                    connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'finished': False, 'progress': msg})
                    try:
                        obj = models.Setting.objects.get(name='host_new')
                        obj2 = models.Setting.objects.get(name='host')
                        obj2.value = obj.value
                        obj2.save()
                        obj.delete()
                    except:
                        pass
                    try:
                        _package_client_file()
                    except:
                        pass
                return threads.deferToThread(_worker)

            # 8.检查Setting表
            def _step_8_check(*args):
                models.Setting.objects.get_or_create(
                    name='installed',
                    value=True
                )
                migration_step = models.Setting.getvalue('migration_step')
                if not migration_step:
                    db_version = models.Setting.getvalue('migration_step')
                    version_file = os.path.join(settings.BASE_DIR, 'version.ini')
                    if not db_version and os.path.exists(version_file):
                        config = ConfigParser.SafeConfigParser()
                        config.read(version_file)
                        version_number = config.get('Version', 'Version number').strip().replace('.', '').replace('V', '')
                        db_version = version_number + config.get('Version', 'svn')
                    try:
                        db_version = int(db_version)
                    except:
                        db_version = 999
                    self.log.info(u'8. 获取数据库版本信息失败,置为%s.', db_version)

                    models.Setting.objects.get_or_create(
                        name='migration_step',
                        value=db_version
                    )

                activate = models.Setting.getval('activation')
                if not activate:
                    self.log.info(u'8. 软件尚未授权或获取授权信息失败.')

            def _step_999_finish(*args):
                def _worker():
                    self.log.info(u'999. 本地处理完成！.')
                    connect['connect'].sendMessage({'ret': 0, 'operation': 'progress', 'finished': True, 'progress': ''})
                return threads.deferToThread(_worker)

            d = _step_1_truncate()
            d.addCallback(_step_2_syllabus)
            for i in range(total):
                d.addCallback(_step_3_data, i)
            d.addCallback(_step_4_newkey)
            d.addCallback(_step_5_ini)
            d.addCallback(_step_6_lessonteacher)
            d.addCallback(_step_7_client)
            d.addCallback(_step_8_check)
            d.addCallback(_step_999_finish)
        except Exception as e:
            connect['connect'].sendMessage({'ret': 1, 'operation': 'progress', 'finished': False, 'progress': str(e)})
            self.log.exception(e)

    def process_nodeinfo(self, connect, connects, server, msgdict):
        if cache.get('node_newly_add') or not self.all_nodes:
            self.all_nodes = list(models.Node.objects.all().values_list('id', flat=True))
        cache_keys = ['node-sync-online:%s' % i for i in self.all_nodes]
        d = cache.get_many(cache_keys)
        return {'ret': 0, 'operation': 'nodeinfo-ret', 'data': {
            'records': d.values(),
        }}

    def process_ping(self, connect, connects, server, msgdict):
        return {'ret': 0, 'operation': 'pong'}

    def _all_nodes(self):
        if cache.get('node_newly_add') or not self.all_nodes:
            self.all_nodes = list(models.Node.objects.all().values_list('id', flat=True))
        return self.all_nodes
