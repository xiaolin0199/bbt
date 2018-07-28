#coding=utf-8
import datetime
import logging
import traceback
from django.core.management.base import BaseCommand
from BanBanTong.db import models
from django.conf import settings
DEBUG = settings.DEBUG
del settings


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''
        学年学期的设定规则改变过后,ActiveTeachers表中的数据
        active_date school_year term_type三者对应的就有点问题了
        这里用该脚本手动修复
        原则:
            根据activate_date重新获取term数据,修改条目的学年学期字段
    '''

    def modify_items(self, term_base, debug=False):
        objs = models.ActiveTeachers.objects.all()
        # objs = objs.filter(school_year='2014-2015', term_type='春季学期', town_name='白杨坪镇')
        # for term in term_base:
        #     obj = objs.filter(active_date__range=(term.start_date, term.end_date))
        #     for i in obj:
        #         i.school_year = term.school_year
        #         i.term_type = term.term_type
        #         i.save()
        #         if DEBUG:
        #             print 'modify_items:', i.pk
        # 

        for o in objs:
            term = term_base.filter(start_date__lte=o.active_date, end_date__gte=o.active_date)
            if term.exists():
                o.school_year = term[0].school_year
                o.term_type = term[0].term_type
                o.save()
                if DEBUG:
                    print 'modify_items:', o.pk
            else:
                if DEBUG:
                    print 'no term find'
                # o.delete()

    def handle(self, *args, **options):
        debug = False
        if 'debug' in options:
            debug = True
        if DEBUG or debug:
            print 'begin'
        if models.Setting.getvalue('installed') != 'True':
            return
        server_type = models.Setting.getvalue('server_type')
        if server_type == 'school':
            term_base = models.Term.objects.all()
        else:
            term_base = models.NewTerm.objects.all()
        self.modify_items(term_base, debug)
        if DEBUG or debug:
            print 'finished'
