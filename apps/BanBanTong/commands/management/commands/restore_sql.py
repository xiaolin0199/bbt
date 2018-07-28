#coding=utf-8
import hashlib
from django.core.management.base import BaseCommand
from BanBanTong.db import models


class Command(BaseCommand):
    '''
        用于处理手工导出的sql数据，生成SyncLog
    '''

    def run(self):
        province = models.Group.objects.get(group_type='province')
        city = models.Group.objects.get(group_type='city')
        country = models.Group.objects.get(group_type='country')
        town = models.Group.objects.get(group_type='town')
        school = models.Group.objects.get(group_type='school')
        for i in [province, city, country, town, school]:
            models.SyncLog.add_log(i, 'add')
        objs = [models.Teacher, models.AssetType, models.Term, models.Grade,
                models.Class, models.ClassMacV2, models.LessonName,
                models.LessonPeriod, models.LessonSchedule, models.LessonTeacher,
                models.TeacherLoginLog, #models.TeacherAbsentLog,
                models.TeacherLoginTime,
                models.DesktopPicInfo]
        for obj in objs:
            for i in obj.objects.all():
                models.SyncLog.add_log(i, 'add')
        models.Setting(name='province', value=province.name).save()
        models.Setting(name='city', value=city.name).save()
        models.Setting(name='country', value=country.name).save()
        models.Setting(name='town', value=town.name).save()
        models.Setting(name='school', value=school.name).save()
        models.Setting(name='installed', value=True).save()
        models.Setting(name='install_step', value='-1').save()
        models.Setting(name='migration_step', value='59').save()
        models.Setting(name='server_type', value='school').save()
        models.User.objects.create(username='admin',
                                   password=hashlib.sha1('admin').hexdigest(),
                                   sex='', status='active', level='school')

    def handle(self, *args, **options):
        self.run()
