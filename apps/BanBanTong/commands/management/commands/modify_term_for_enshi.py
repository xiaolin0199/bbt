#coding=utf-8
import datetime
import logging
import traceback
from django.core import serializers
from django.core.management.base import BaseCommand
from BanBanTong.db import models


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''
        恩施升级到746之后，需要对旧数据进行重整，让学期设置
        符合县级服务器的规范。思路是从校级服务器修改Term，然后
        同步到县级。主要问题有：
        2013-2014 秋季学期，没有关联数据，可以直接删除
        2014-2015 秋季学期，熊家初中设错了，应该改为 2013-2014 春季学期
        2014-2015 秋季学期，其他学校没问题
        2014-2015 春季学期，熊家初中删掉这个学期
        2014-2015 春季学期，有6所学校设错了，应该改为 2013-2014 春季学期
        2013-2014 春季学期，有的学校原始数据是错误的，从县级拉取Term设置之后
            多出了几个同样的学期，需要删掉
        删掉所有学校2014-03-14之前和2014-07-04之后的TeacherAbsentLog TeacherLoginLog
    '''

    def run1(self):
        '''删除2013-2014秋季学期'''
        logger.debug('run1 -- delete terms')
        models.Term.objects.filter(school_year='2013-2014', term_type='秋季学期').delete()

    def run2(self):
        '''熊家初中学期修改'''
        logger.debug('run2 ---')
        try:
            school = models.Group.objects.get(name='熊家初中')
        except:
            return
        try:
            t = models.Term.objects.get(school=school, school_year='2014-2015',
                                        term_type='秋季学期')
        except:
            s = traceback.format_exc()
            self.stdout.write(s)
            return
        t.school_year = '2013-2014'
        t.term_type = '春季学期'
        t.save()
        for i in models.TeacherLoginLog.objects.filter(school=school, term=t):
            i.term_school_year = '2013-2014'
            i.term_type = '春季学期'
            i.save()
        for i in models.TeacherAbsentLog.objects.filter(school=school, term=t):
            i.term_school_year = '2013-2014'
            i.term_type = '春季学期'
            i.save()
        models.Term.objects.get(school=school, school_year='2014-2015',
                                term_type='春季学期').delete()

    def run3(self):
        '''
            修改6所学校。这6所学校已经从县级拉取了2013-2014 春季学期，需要删掉，
            然后把2014-2015 春季学期改成2013-2014 春季学期。
        '''
        logger.debug('run3 ---')
        uuids = ('02953900-B882-11E3-B331-50E549B81E51',
                 'E845E1E2-B96B-11E3-AE8B-00248186CBCF',
                 'FEE44340-B481-11E3-A636-00503CFF888A',
                 '7E4C60A1-B94A-11E3-A226-1078D2749C16',
                 'BF16D7E1-B8BA-11E3-BD02-00297F45632F',
                 'C93B794F-B4E7-11E3-B75B-1078D2CEBE80')
        schools = models.Group.objects.filter(uuid__in=uuids)
        models.Term.objects.filter(school__in=schools, school_year='2013-2014',
                                   term_type='春季学期').delete()
        for i in models.Term.objects.filter(school__in=schools,
                                            school_year='2014-2015',
                                            term_type='春季学期'):
            i.school_year = '2013-2014'
            i.save()
        terms = models.Term.objects.filter(school__in=schools,
                                           school_year='2013-2014',
                                           term_type='春季学期')
        for i in models.TeacherLoginLog.objects.filter(school__in=schools,
                                                       term__in=terms):
            i.term_school_year = '2013-2014'
            i.term_type = '春季学期'
            i.save()
        for i in models.TeacherAbsentLog.objects.filter(school__in=schools,
                                                        term__in=terms):
            i.term_school_year = '2013-2014'
            i.term_type = '春季学期'
            i.save()

    def run4(self):
        '''删掉重复的2013-2014 春季学期'''
        logger.debug('run4 ---')
        try:
            q = models.Term.objects.filter(school_year='2013-2014',
                                           term_type='春季学期')
            logger.debug('run4: 2013-2014 春季学期 count %s', q.count())
            if q.count() > 1:
                q1 = models.TeacherLoginLog.objects.filter(term_school_year='2013-2014',
                                                           term_type='春季学期').order_by('created_at')
                if q1.count() > 0:
                    t = q1[0].term
                    q.exclude(uuid=t.uuid).delete()
                    logger.debug('run4: delete term with TeacherLoginLog')
                else:
                    q[1:].delete()
                    logger.debug('run4: delete term without TeacherLoginTime')
        except:
            logger.exception('')
        '''删掉2014-03-14之前和2014-07-04之后的两个流水'''
        try:
            term = models.Term.objects.get(school_year='2013-2014',
                                           term_type='春季学期')
        except:
            logger.exception('')
            return
        s = datetime.date(2014, 3, 14)
        e = datetime.date(2014, 7, 4)
        models.TeacherLoginLog.objects.filter(term=term).exclude(created_at__range=(s, e)).delete()
        models.TeacherAbsentLog.objects.filter(term=term).exclude(created_at__range=(s, e)).delete()

    def run5(self):
        '''遍历SyncLog，把误删除的2014-2015秋季学期的TeacherAbsentLog和TeacherLoginLog恢复出来'''
        try:
            term = models.Term.objects.get(school_year='2014-2015',
                                           term_type='秋季学期')
        except:
            return
        q = models.SyncLog.objects.filter(operation_type='delete',
                                          operation_content__contains='db.teacherloginlog')
        for i in q:
            for obj in serializers.deserialize('json', i.operation_content):
                if not isinstance(obj.object, models.TeacherLoginLog):
                    continue
                if obj.object.term == term:
                    if models.TeacherLoginLog.objects.filter(uuid=obj.object.uuid).exists():
                        continue
                    obj.object.save(force_insert=True)
        q = models.SyncLog.objects.filter(operation_type='delete',
                                          operation_content__contains='db.teacherabsentlog')
        for i in q:
            for obj in serializers.deserialize('json', i.operation_content):
                if not isinstance(obj.object, models.TeacherAbsentLog):
                    continue
                if obj.object.term == term:
                    if models.TeacherAbsentLog.objects.filter(uuid=obj.object.uuid).exists():
                        continue
                    obj.object.save(force_insert=True)
        q = models.SyncLog.objects.filter(operation_type='delete',
                                          operation_content__contains='db.teacherlogintime')
        for i in q:
            for obj in serializers.deserialize('json', i.operation_content):
                if not isinstance(obj.object, models.TeacherLoginTime):
                    continue
                if obj.object.teacherloginlog.term == term:
                    if models.TeacherLoginTime.objects.filter(uuid=obj.object.uuid).exists():
                        continue
                    obj.object.save(force_insert=True)

    def handle(self, *args, **options):
        if models.Setting.getvalue('server_type') != 'school':
            logger.debug('not school, quit')
            return
        if models.Setting.getvalue('country') != u'恩施市':
            logger.debug('not Enshi, quit')
            return
        if models.Setting.getvalue('migration_step') == '46':
            self.run1()
            self.run2()
            self.run3()
            self.run4()
            models.Setting.objects.filter(name='migration_step').update(value='47')
        if models.Setting.getvalue('migration_step') == '47':
            self.run5()
            models.Setting.objects.filter(name='migration_step').update(value='48')
