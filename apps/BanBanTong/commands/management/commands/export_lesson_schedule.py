# coding=utf-8
import os
import uuid
from django.core.management.base import BaseCommand

from BanBanTong.db import models
import xlwt
from BanBanTong import constants


class Command(BaseCommand):
    '''
        导出当前学期的所有班级的课程表
    '''

    def cerate_xls(self, title, lesson_schedule_objs):
        xls = xlwt.Workbook(encoding='utf8')
        sheet = xls.add_sheet(title)
        header = (
            u'节次', u'周一', u'周二', u'周三',
            u'周四', u'周五', u'周六', u'周日'
        )
        weekday = (u'mon', u'tue', u'wed', u'thu', u'fri', u'sat', u'sun')
        for i in range(len(header)):
            sheet.write(0, i, header[i])
        row = 1
        objs = lesson_schedule_objs.values(
            'lesson_period__sequence',
            'weekday',
            'lesson_name__name',
        )

        for i in objs:
            row = int(i['lesson_period__sequence'])
            column = weekday.index(i['weekday']) + 1
            try:
                sheet.write(row, 0, row)
            except:
                pass
            sheet.write(row, column, i['lesson_name__name'])

        tmp_file = os.path.join(constants.CACHE_TMP_ROOT, 'export', title)
        xls.save(tmp_file)

    def export(self, *args, **kwargs):
        terms = models.Term.get_current_term_list()
        for term in terms:
            school = term.school.name
            klass = models.Class.objects.filter(grade__term=term).exclude(grade__number=13)

            if not klass.exists():
                print 'no class exists'
                return
            for cls in klass:
                title = u'%s%s年级%s班课程表.xls' % (school, cls.grade.name, cls.name)
                objs = models.LessonSchedule.objects.filter(class_uuid=cls)
                self.cerate_xls(title, objs)

    def handle(self, *args, **options):
        print 'begin to export'
        self.export()
        dir = os.path.join(constants.CACHE_TMP_ROOT, 'export')
        print 'finished, please check files under', dir
