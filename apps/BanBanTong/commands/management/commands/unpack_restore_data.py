# coding=utf-8
import os
import bz2
import base64
# import traceback
from django.core.management.base import BaseCommand
from BanBanTong.db import models
import datetime

from BanBanTong import constants
from BanBanTong.views.system.install import _modify_update_path
# from BanBanTong.views.system.install import _package_client_file
from BanBanTong.views.system.install import _truncate_tables
from BanBanTong.views.system.remote import _restore_syllabus


class Command(BaseCommand):
    '''
        用于从县级导出的restore.log(回传的文件)恢复校级数据库
    '''

    def add_arguments(self, parser):
        parser.add_argument('key', help=u'连接密钥.')

    def run(self, data, syllabus):
        print 0
        data = bz2.decompress(base64.b64decode(data))
        syllabus = bz2.decompress(base64.b64decode(syllabus))

        print 1, '_truncate_tables'
        _truncate_tables()

        print 2, '_restore_syllabus'
        _restore_syllabus(syllabus)

        lines = data.split('\n')
        total = len(lines)
        print 3, 'handle lines total:', total
        for i in range(total):
            if i % 1000 == 0:
                print i
                print str(lines[i])[:100]
            if not lines[i]:
                continue
            models.SyncLogPack.unpack_log('add', lines[i])

        print 4, 'conf Setting'
        models.Setting.objects.filter(name='sync_server_key').delete()

        print 5, 'conf Group'
        province = models.Group.objects.get(group_type='province').name
        city = ''
        country = ''
        server_type = models.Setting.getvalue('server_type')
        if server_type != 'province':
            city = models.Group.objects.get(group_type='city').name
            if server_type != 'city':
                country = models.Group.objects.get(group_type='country').name
        _modify_update_path(province, city, country)

        print 6, 'LessonTeacher'
        for obj in models.LessonTeacher.objects.all():
            models.LessonTeacher.calculate_total_teachers(obj)

        print 7, 'Setting'
        try:
            obj = models.Setting.objects.get(name='host_new')
            obj2 = models.Setting.objects.get(name='host')
            obj2.value = obj.value
            obj2.save()
            obj.delete()
        except:
            pass
            # traceback.print_exc()

        print 8
        models.Setting.objects.get_or_create(
            name='installed',
            value=True
        )
        migration_step = models.Setting.getvalue('migration_step')
        if not migration_step:
            print u'\nWarning:获取数据库版本信息失败,置为999.\n'
            models.Setting.objects.get_or_create(
                name='migration_step',
                value=999
            )

        print 9
        activate = models.Setting.getval('activation')
        if not activate:
            print u'\nWarning:软件尚未授权或获取授权信息失败.\n'

    def handle(self, *args, **options):
        key = options.pop('key')
        t = datetime.datetime.now().strftime('%Y%m%d')
        filepath = os.path.abspath(os.path.join(constants.CACHE_TMP_ROOT, t + '-' + key + '.bak'))
        with open(filepath, 'r') as f:
            data = eval(f.read())

        self.run(data['data'], data['syllabus'])
