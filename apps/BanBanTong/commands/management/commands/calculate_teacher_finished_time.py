#coding=utf-8
import logging
import datetime
from django.core.management.base import BaseCommand
from django.db.models import Sum

from BanBanTong.db import models


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''
        重新计算G表的教师已授课时 和  授课时长
    '''

    def handle(self, *args, **options):
        if models.Setting.getvalue('server_type') not in ('school', 'country'):
            logger.debug('not school/country, quit')
            return
        terms = models.Term.get_current_term_list() # 默认当前学年学期
        if args:
            if 'update-old-terms' in args: # 所有学年学期
                lst = terms and map(lambda i: i.pk, terms) or []
                terms = models.Term.objects.exclude(pk__in=lst)
            else: # 指定学年学期
                term_uuid , = args
                terms = [models.Term.objects.get(uuid=term_uuid)]        
                
        start_date = datetime.datetime.now()
        print 'start: ' , start_date        

        q = models.LessonTeacher.objects.filter(class_uuid__grade__term__in=terms)
        for o in q.iterator():
            
            logs = o.teacherloginlog_set.all().values_list('teacherlogintime__login_time', flat=True)
            # 已授课时
            o.finished_time = logs.count()
            # 总授课时长
            o.login_time = sum(logs)
            
            o.save(force_update=True)
            
            #print o.lesson_name , o.teacher  , o.finished_time , o.login_time

        print 'finished: ' , datetime.datetime.now() - start_date