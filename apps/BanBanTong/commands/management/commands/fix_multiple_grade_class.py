# coding=utf-8
"""
    现象: 罗针田小学出现重复的年级
    原因分析: 待分析
    处理方法:
        合并同名的年级,将产生的的数据归并到一个年级下
        然后删除掉多余的年级.

"""
import logging
import datetime
from django.core.management.base import BaseCommand
from BanBanTong import constants
from BanBanTong.db import models

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__()
        self.bad_items = []
        self.grade_names = (
            u'一', u'二', u'三',
            u'四', u'五',  u'六',
            u'七', u'八', u'九',
            u'十', u'十一', u'十二',
            u'电脑教室',
        )

    def walker(self, *args, **kwargs):
        for grade_name in self.grade_names:
            grades = models.Grade.objects.filter(name=grade_name)
            if grades.count() > 1:
                self.bad_items.append(grades)

    def fix_items(self, *args, **kwargs):
        if not self.bad_items:
            print 'no bad items found.'
            return

        for item in self.bad_items:
            remain = item[0]
            others = item[1:]
            print 'Fix Grade:', remain.name

            uuids = others and map(lambda i: i.pk, others) or []
            grades = models.Grade.objects.filter(pk__in=uuids)
            a = models.TeacherAbsentLog.objects.filter(grade__in=grades)
            b = models.TeacherLoginLog.objects.filter(grade__in=grades) #
            c = models.Class.objects.filter(grade__in=grades) #
            d = models.DesktopPicInfo.objects.filter(grade__in=grades)
            e = models.TeacherLoginTimeCache.objects.filter(grade__in=grades)

            changed_items = a.count() + b.count() + c.count() + d.count() + e.count()
            for objs in (a, b, c, d, e):
                for o in objs:
                    o.grade = remain
                    o.save()

            print '%s items\' been changed' % changed_items

            klass = models.Class.objects.filter(grade=remain)
            uuids = [i.pk for i in klass]
            objs = models.Statistic.objects.filter(key__in=uuids)
            for o in objs:
                o.update_on_change(True) # debug=True

            for g in others:
                if g.class_set.count() == 0:
                    g.delete()

    def handle(self, *args, **options):
        server_type = models.Setting.getvalue('server_type')
        if server_type != 'school':
            print 'This Script Is Just For School'
            return

        self.walker()
        self.fix_items()


