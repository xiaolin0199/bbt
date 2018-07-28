# coding=utf-8
import os
import time
import random
import logging
import datetime
import ConfigParser
from django.conf import settings
from django.core import serializers
from django.core.cache import cache
from django.db.models import Max
from django.db import connections
from BanBanTong.db import models
from activation.decorator import get_use_activate

logger = logging.getLogger(__name__)


def periodical_sync_data(client):
    if not client['connect'] or cache.get('periodical_sync_data'):
        return
    try:
        cache.set('periodical_sync_data', True, 3600 * 4)
        client['connect'].sendMessage({'category': 'sync', 'operation': 'query-id'})
        client['status'] = 'query-id'
    except Exception as e:
        logger.exception(e)
    finally:
        cache.delete('periodical_sync_data')


def periodical_sync_cache(client):
    if not client['connect'] or cache.get('periodical_sync_cache'):
        return
    try:
        cache.set('periodical_sync_cache', True, 600)
        message = {'category': 'sync', 'operation': 'sync-cache', 'data': {}}
        terms = models.Term.get_current_term_list()
        q = models.Class.objects.filter(grade__term__in=terms)
        q = q.values_list('uuid', flat=True)
        for uu in q:
            k = 'class-%s-active-time' % uu
            v = cache.get(k)
            if v:
                message['data'][k] = v
            k = 'class-%s-teacherlogintime' % uu
            v = cache.get(k)
            if v:
                message['data'][k] = v

        q = models.Teacher.objects.all().values_list('uuid', flat=True)
        for uu in q:
            k = 'teacher-%s-active-time' % uu
            v = cache.get(k)
            if v:
                message['data'][k] = v
            k = 'computerclass-teacher-%s-active-time' % uu
            v = cache.get(k)
            if v:
                message['data'][k] = v
        if message['data']:
            client['connect'].sendMessage(message)
    except Exception as e:
        logger.exception(e)
    finally:
        cache.delete('periodical_sync_cache')


def periodical_sync_misc(client):
    if not client['connect']:
        return
    if not cache.get('periodical_sync_misc'):
        try:
            cache.set('periodical_sync_misc', True, 3600 * 4)
            now = datetime.datetime.now()
            if client['sync-misc'] is None or (now - client['sync-misc']).total_seconds() > 3600:
                message = {'category': 'sync', 'operation': 'sync-misc', 'data': {
                    'Node': '',
                    'Role': '',
                    'RolePrivilege': '',
                    'Setting': '',
                    'UsbkeyTeacher': '',
                    'User': '',
                    'school-uuids': ''
                }}
                objs = models.Node.objects.all()
                message['data']['Node'] = serializers.serialize('json', objs)
                objs = models.Role.objects.all()
                message['data']['Role'] = serializers.serialize('json', objs)
                objs = models.RolePrivilege.objects.all()
                message['data']['RolePrivilege'] = serializers.serialize('json', objs)
                names = ['server_type', 'install_step', 'province', 'city', 'country', 'town', 'school', 'installed']
                objs = models.Setting.objects.filter(name__in=names)
                message['data']['Setting'] = serializers.serialize('json', objs)
                objs = models.UsbkeyTeacher.objects.all()
                message['data']['UsbkeyTeacher'] = serializers.serialize('json', objs)
                objs = models.User.objects.all()
                message['data']['User'] = serializers.serialize('json', objs)
                objs = models.Group.objects.filter(group_type='school')
                uuids = ','.join(list(objs.values_list('uuid', flat=True)))
                message['data']['school-uuids'] = uuids
                client['connect'].sendMessage(message)
                client['sync-misc'] = now
        except Exception as e:
            logger.exception(e)
        finally:
            cache.delete('periodical_sync_misc')


def periodical_close_old_connections():
    # 每隔一段时间检查一次数据库连接健康状态, 关闭失效的连接
    for conn in connections.all():
        # conn.close_if_unusable_or_obsolete
        # django.db.backends.base.base.BaseDatabaseWrapper.close_if_unusable_or_obsolete
        if conn.connection is not None:
            # If the application didn't restore the original autocommit setting,
            # don't take chances, drop the connection.
            if conn.get_autocommit() != conn.settings_dict['AUTOCOMMIT']:
                logger.info('close_old_connections: reason=conn.get_autocommit() != %s, conn=%s', conn.settings_dict['AUTOCOMMIT'], conn)
                conn.close()
                continue

            # If an exception other than DataError or IntegrityError occurred
            # since the last commit / rollback, check if the connection works.
            if conn.errors_occurred:
                if conn.is_usable():
                    conn.errors_occurred = False
                else:
                    logger.info('close_old_connections: reason=errors_occurred, conn=%s', conn)
                    conn.close()
                    continue

            if conn.close_at is not None and time.time() >= conn.close_at:
                logger.info('close_old_connections: reason=time.time() >= conn.close_at, close_at=%s, conn=%s', conn.close_at, conn)
                conn.close()
                continue
    time.sleep(random.random())


def login(client):
    """发送登录指令"""
    if not client['factory']:
        return
    if models.Setting.getvalue('installed') != 'True':
        client['connect'].sendClose()
        return

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
    server_type = models.Setting.getvalue('server_type')
    g = models.Group.objects.get(group_type=server_type)
    maxid = models.SyncLog.objects.aggregate(x=Max('created_at'))['x']
    client['connect'].sendMessage({'category': 'sync', 'operation': 'login', 'data': {
        'key': client['key'],
        'uuid': g.uuid,
        'name': g.name,
        'db_version': db_version,
        'server_type': server_type,
        'synclog_max_id': maxid,
        'used_quota': get_use_activate(),
        'parent': {'group_type': g.parent.group_type, 'name': g.parent.name, 'uuid': g.parent.uuid}
    }})
    client['status'] = 'login'
