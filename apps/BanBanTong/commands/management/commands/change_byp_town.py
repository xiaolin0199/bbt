#!/usr/bin/env python
# coding=utf-8
import datetime
import hashlib
import math
import random
import MySQLdb
import traceback

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import F

from BanBanTong.db import models
from machine_time_used import models as m_models
from edu_point import models as e_models

'''
    1. 白杨坪镇
        鲁竹坝小学
        白杨坪初级中学
    2. 白杨坪乡
        白杨坪镇中心小学
        董家店村小学
        熊家岩小学
        熊家初中

    *  将白杨坪乡下属学校的town改为白杨坪镇
    *  取消白杨坪乡

    需要涉及修改的表(分四类)

    * Group (学校对应的TOWN切换) *

    1. 流水表
        AssetLog (town__uuid , town_name)
        AssetRepairLog (town__uuid , town_name)
        ActiveTeachers  (town_name)
        TeacherLoginLog (town__uuid , town_name)
        TeacherAbsentLog (town__uuid , town_name)
        TeacherLoginTimeCache (town__uuid)
        TeacherLoginCountWeekly (town_name)
        TeacherLoginTimeWeekly  (town_name)
    2. 统计表
        TotalTeachersTown (town_name)
        TotalTeachersSchool (town_name)
        TotalTeachersLesson (town_name)
        TotalTeachersGrade (town_name)
        TotalTeachersLessonGrade (town_name)
    3. 暂未使用的新功能表
        MachineTimeUsed (town_name)
        EduPoint (town_name)
        EduPointDetailDesktopViewLog (town_name)
        EduPointMachineTimeUsed (town_name)
        EduPointResourceReceLog (town_name)
    4. synclog里的日志数据
        Synclog

县级
    第一步:  处理流水表
      遍历 ->  查找所有town__uuid或town_name为白杨坪乡的改为对应的白杨坪镇UUID及name
    第二步:  处理统计表
      除了TotalTeachersTown表需要将白杨坪乡的统计合并到白杨坪镇
      其他的与流水表处理相同
    第三步:  新功能表
      处理同流水表
    第四步:  synclog (暂不处理)

    ** 将parent_uuid为白杨坪乡的学校改为白杨坪镇的uuid (等所有数据表全部修改完后再删除白杨坪乡)

校级:
    校服务器不涉及uuid的修改，只需要将所有出现'白杨坪乡' -> '白杨坪镇'即可;
    * synclog里operation_content	里 u'白杨坪乡' -> u'白杨坪镇' (unicode)，也可暂不处理 *
'''


class Command(BaseCommand):

    server_type = models.Setting.getvalue('server_type')
    tuple_names = [
        [u'白杨坪乡', u'白杨坪镇'],  # 白杨坪乡替换成白杨坪镇
    ]

    tuple_uuids = []

    only_change_name_models = [
        'models.ActiveTeachers',
        'models.TeacherLoginCountWeekly',
        'models.TeacherLoginTimeWeekly',
        'models.TotalTeachersSchool',
        'models.TotalTeachersLesson',
        'models.TotalTeachersGrade',
        'models.TotalTeachersLessonGrade',
        'm_models.MachineTimeUsed',
        'e_models.EduPoint',
        'e_models.EduPointDetailDesktopViewLog',
        'e_models.EduPointMachineTimeUsed',
        'e_models.EduPointResourceReceLog'
    ]

    only_change_uuid_models = [
        'models.TeacherLoginTimeCache'
    ]

    both_change_models = [
        'models.AssetLog',
        'models.AssetRepairLog',
        'models.TeacherLoginLog',
        'models.TeacherAbsentLog'
    ]

    another_models = [
        'models.TotalTeachersTown',
        'models.Setting',
        'models.Group',
        #'models.SyncLog'
    ]

    def _init(self):
        '''
            根据 tuple_names去数据库里查询，补全tuple_uuids
        '''
        msg = True
        if self.server_type == 'country':
            for old_name, new_name in self.tuple_names:
                try:
                    old_uuid = models.Group.objects.get(group_type='town', name=old_name).uuid
                except:
                    print u'%s已删除' % old_name
                    old_uuid = None
                    msg = False

                try:
                    new_uuid = models.Group.objects.get(group_type='town', name=new_name).uuid
                except:
                    print u'%s不存在' % new_name
                    new_uuid = None
                    msg = False

                if old_uuid and new_uuid:
                    self.tuple_uuids.append([old_uuid, new_uuid])

        return msg

    def change(self):
        ''''''
        # only name -- only_change_name_models
        for model in self.only_change_name_models:
            msg = 'OK'
            print 'model: ', model

            for old_name, new_name in self.tuple_names:
                try:
                    eval(model).objects.filter(town_name=old_name).update(town_name=new_name)
                except:
                    traceback.print_exc()
                    msg = 'ERROR'

            print 'change msg: ', msg

        # only uuid -- only_change_uuid_models
        for model in self.only_change_uuid_models:
            msg = 'OK'
            print 'model: ', model

            for old_uuid, new_uuid in self.tuple_uuids:
                try:
                    eval(model).objects.filter(town__uuid=old_uuid).update(town=new_uuid)
                except:
                    traceback.print_exc()
                    msg = 'ERROR'

            print 'change msg: ', msg

        # both -- both_change_models
        for model in self.both_change_models:
            msg = 'OK'
            print 'model: ', model

            if self.tuple_names and self.tuple_uuids:
                for old_name, new_name, old_uuid, new_uuid in [[i[0], i[1], j[0], j[1]] for i, j in zip(self.tuple_names, self.tuple_uuids)]:
                    try:
                        eval(model).objects.filter(town_name=old_name, town__uuid=old_uuid).update(town_name=new_name, town=new_uuid)
                    except:
                        traceback.print_exc()
                        msg = 'ERROR'
            else:
                for old_name, new_name in self.tuple_names:
                    try:
                        eval(model).objects.filter(town_name=old_name).update(town_name=new_name)
                    except:
                        traceback.print_exc()
                        msg = 'ERROR'

            print 'change msg: ', msg

        # another
        for model in self.another_models:
            if model == 'models.TotalTeachersTown':
                # old_name的统计数据  -> new_name的统计数据
                msg = 'OK'
                print 'model: ', model

                for old_name, new_name in self.tuple_names:
                    old_objs = eval(model).objects.filter(town_name=old_name)
                    for o in old_objs:
                        term = o.term
                        t = o.total
                        country_name = o.country_name
                        try:
                            eval(model).objects.filter(country_name=country_name, town_name=new_name, term=term).update(total=F('total') + t)
                            # delete
                            o.delete()
                        except:
                            traceback.print_exc()
                            msg = 'WARMING'

                print 'change msg: ', msg

            elif model == 'models.Setting':
                msg = 'OK'
                print 'model: ', model

                if self.server_type == 'school':
                    for old_name, new_name in self.tuple_names:
                        if eval(model).getvalue('town') == old_name:
                            try:
                                eval(model).objects.filter(name='town', value=old_name).update(value=new_name)
                            except:
                                traceback.print_exc()
                                msg = 'ERROR'

                print 'change msg: ', msg

            elif model == 'models.Group':
                msg = 'OK'
                print 'model: ', model

                # 校只修改一下town名字即可
                if self.server_type == 'school':
                    for old_name, new_name in self.tuple_names:
                        if eval(model).objects.get(group_type='town').name == old_name:
                            try:
                                eval(model).objects.filter(group_type='town').update(name=new_name)
                            except:
                                traceback.print_exc()
                                msg = 'ERROR'
                # 县级则是需要将old_town的下属学校parent改为new_town下，同时删除old_name
                elif self.server_type == 'country':
                    for old_name, new_name in self.tuple_names:
                        old_obj = eval(model).objects.get(group_type='town', name=old_name)
                        new_obj = eval(model).objects.get(group_type='town', name=new_name)
                        # change
                        try:
                            eval(model).objects.filter(parent=old_obj).update(parent=new_obj)
                        except:
                            traceback.print_exc()
                            msg = 'ERROR'
                        # TODO: 删除old_obj的时候必须最后, 如果有别的表用了这个对象做外键都不删除不成功
                        # old_obj.delete()

                print 'change msg: ', msg

    def handle(self, *args, **options):
        cursor = connection.cursor()
        cursor.execute('SET unique_checks=0')
        cursor.execute('SET foreign_key_checks=0')

        print '-------- start ----------'
        print '------ init ------'

        msg = self._init()

        print 'server_type: ', self.server_type
        print 'names: ', self.tuple_names
        print 'uuids: ', self.tuple_uuids

        if msg:
            print '------ change ------'

            self.change()

            print '--------- end -----------'

        cursor.execute('SET unique_checks=1')
        cursor.execute('SET foreign_key_checks=1')
