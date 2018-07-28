#!/usr/bin/env python
# coding=utf-8
import datetime
import hashlib
import math
import random
import uuid
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.db import transaction
from django.utils.dateparse import parse_date
from django.utils.dateparse import parse_time
from BanBanTong.db import models
from BanBanTong.forms.new_lesson_name import NewLessonNameForm
from BanBanTong.utils import str_util


class Command(BaseCommand):
    macs = ('50E549B81E51', '050509001C91', '6CAE8B238015', 'ECA86BC584E4',
            'E03F49784485', '00B93F2B82F3', '002564E6B69B', 'C03FD509A6A7',
            '7427EAA967FE', 'C03FD50611A2', '4437E64E24EC', '3640B588CAD1',
            'C03FD5708A4F', '94DE80E7549A', '80C16EF91BE7', '0014782DC118',
            '002185D7D867', 'A4BADBF70B04', '002564D0E71D', 'C89CDCE9A860',
            'F80F41FBD6D1', '94DE8040DAB3', 'BCAEC543E2CB', 'ECA86BC7280B',
            '002511482396', 'B8763F695248', 'ECA86BC585D3', '0505090019AC',
            '4061868FA4ED', 'EC888FE7404A', 'ECA86BC9C25A', '74D43521E896',
            '050509002253', '4487FC7BA011', '1078D2749C16', '0018F3E42A9C',
            '006CA2E6CEB1', '6C626DEC499F', '4437E6500414', '050509001760',
            '001FC645A69B', '70F3950C53D3', 'ECA86BC9C04E', '001A64BF2658',
            'ECA86BC72609', '4487FCF0A78D', '00E081D30B40', '4437E64ECC5F',
            'C81F663C74F3', 'B8AC6FD821BE', '0025114ACAB6', '40618621D367',
            '40618626C7B6', '00247E069EDA', '001E900D7D12', '00297F45632F',
            'C03FD5362107', '050509001989', '1078D2CEBE80', '7427EAC10C4F',
            '4437E64F486B', '00262D024BAB', '0052D6AC01FF', 'ECA86BC9A614',
            'A4BADBE606EB', 'D43D7E1073A3', '4437E6AF78EF', '00503CFF93A2',
            '00D7F1334083', '00248186CBCF', '00503CFF917D', '4437E6AF7921',
            '7427EAE422C0', '001E671D406D', '00248C0E582C', '00503C002BE2',
            '7427EAEF8F7F', '00503CFF888A', '74D4355106C2', 'FA163E67B448')

    # 生成100个随机的MAC
    alnum = '0123456789ABCDEF'
    macs = [''.join(random.sample(alnum, 12)) for i in range(100)]

    # 节次
    #periods = [8, 9, 10, 11, 14, 15, 16, 17]
    periods = [i for i in range(0, 24)]  # 0 ~ 23
    times = ((5, 25), (35, 55),)

    # 年级
    grades = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']

    # 班级
    classes = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    # 生成老师 (300个)
    def _generate_teacher(self):
        models.Teacher.objects.all().delete()
        q = models.Group.objects.filter(group_type='school')
        for school in q:
            for i in range(1, 301):
                obj = models.Teacher(uuid=str(uuid.uuid1()).upper(),
                                     sequence=i, name=u'教师-%s' % (''.join(random.sample(self.alnum, 6))),
                                     password='0101', sex='male',
                                     edu_background='本科',
                                     birthday=parse_date('1980-1-1'),
                                     title='一级', school=school)
                obj.save()

    # 生成作息表
    def _generate_lessonperiod(self):
        models.LessonPeriod.objects.all().delete()
        q = models.Term.get_current_term_list()
        seq = 1
        for term in q:
            for j in self.periods:
                for v in self.times:
                    obj = models.LessonPeriod(uuid=str(uuid.uuid1()).upper(),
                                              term=term, sequence=seq,
                                              start_time=parse_time('%d:%d:00' % (j, v[0])),
                                              end_time=parse_time('%d:%d:00' % (j, v[1])))
                    obj.save()
                    seq += 1

    # 生成年级 (一 ~ 十)
    def _generate_grade(self):
        models.Grade.objects.all().delete()
        q = models.Term.get_current_term_list()
        for term in q:
            for name in self.grades:
                obj = models.Grade(uuid=str(uuid.uuid1()).upper(),
                                   name=name, number=str_util.grade_name_to_number(name),
                                   term=term)
                obj.save()

    # 生成班级 (1 ~ 10)
    def _generate_class(self):
        models.Class.objects.all().delete()
        q = models.Grade.objects.all()
        i = 0
        for grade in q:
            teachers = models.Teacher.objects.all()
            # for name in ['1', '2', '3', '4', '5', '6', '7', '8']:
            for name in self.classes:
                name = str(name)
                obj = models.Class(uuid=str(uuid.uuid1()).upper(),
                                   name=name,
                                   number=str_util.class_name_to_number(name),
                                   grade=grade,
                                   teacher=teachers[i])
                obj.save()
                i += 1
                if i >= teachers.count():
                    i = 0

    # 生成课程表
    def _generate_lessonschedule(self):
        models.LessonSchedule.objects.all().delete()
        q = models.Class.objects.all().order_by('?')
        for c in q:
            lessons = []
            lessons.extend(models.LessonName.objects.filter(school=c.grade.term.school))
            lessons.extend(models.LessonName.objects.filter(school=c.grade.term.school))
            lessons.extend(models.LessonName.objects.filter(school=c.grade.term.school))
            random.shuffle(lessons)
            i = 0
            for weekday in ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'):
                for lp in models.LessonPeriod.objects.filter(term=c.grade.term):
                    obj = models.LessonSchedule(uuid=str(uuid.uuid1()).upper(),
                                                class_uuid=c, lesson_period=lp,
                                                weekday=weekday,
                                                lesson_name=lessons[i])
                    obj.save()
                    i += 1
                    if i >= len(lessons):
                        i = 0

    # 生成课程对应老师
    def _generate_lessonteacher(self):
        models.LessonTeacher.objects.all().delete()
        q = models.Group.objects.filter(group_type='school')
        for school in q:
            teachers = models.Teacher.objects.filter(school=school).order_by('?')
            classes = models.Class.objects.filter(grade__term__school=school)
            i = 0
            for c in classes:
                lessons = c.lessonschedule_set.values_list('lesson_name', flat=True).distinct()
                lessons = models.LessonName.objects.filter(uuid__in=lessons)
                for lesson in lessons:
                    models.LessonTeacher(uuid=str(uuid.uuid1()).upper(),
                                         class_uuid=c,
                                         teacher=teachers[i],
                                         lesson_name=lesson,
                                         schedule_time=200,
                                         finished_time=0).save()
                    i += 1
                    if i >= len(teachers):
                        i = 0

    # 为班级绑定MAC
    def _generate_classmacv2(self):
        models.ClassMacV2.objects.all().delete()
        q = models.Group.objects.filter(group_type='school')
        for school in q:
            classes = models.Class.objects.filter(grade__term__school=school)
            for mac, c in zip(self.macs, classes):
                new_mac = []
                k = 1
                for i in mac:
                    new_mac.append(i)
                    if k % 2 == 0 and k < 12:
                        new_mac.append('-')
                    k += 1
                mac = ''.join(new_mac)

                models.ClassMacV2(uuid=str(uuid.uuid1()).upper(),
                                  mac=mac,
                                  class_uuid=c).save()

    def handle(self, *args, **options):
        cursor = connection.cursor()
        cursor.execute('SET unique_checks=0')
        cursor.execute('SET foreign_key_checks=0')

        self._generate_teacher()
        self._generate_lessonperiod()
        self._generate_grade()
        self._generate_class()
        self._generate_lessonschedule()
        self._generate_lessonteacher()
        self._generate_classmacv2()

        cursor.execute('SET unique_checks=1')
        cursor.execute('SET foreign_key_checks=1')
