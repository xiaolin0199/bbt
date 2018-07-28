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


def getnode_from_uuid(uuid):
    mac = uuid[-12:]
    return int(mac, base=16)


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
    nodes = tuple([int(i, base=16) for i in macs])
    towns = ('舞阳坝街道', '六角亭街道', '小渡船街道', '龙凤镇', '崔坝镇',
             '板桥镇', '三岔乡', '新塘乡', '红土乡', '沙地乡', '白杨坪乡',
             '太阳河乡', '屯堡乡', '白果乡', '芭蕉侗族乡', '盛家坝乡',
             '沐抚')

    def _create_admin(self):
        admin_username = settings.ADMIN_USERS[0]
        passhash = hashlib.sha1(admin_username).hexdigest()
        models.User(username=admin_username, password=passhash,
                    sex='', status='active', level='country').save()

    def _generate_school(self):
        '''生成80个学校'''
        province = models.Group(name='湖北省', group_type='province', parent=None)
        province.save()
        city = models.Group(name='恩施土家族苗族自治州', group_type='city', parent=province)
        city.save()
        country = models.Group(name='恩施市', group_type='country', parent=city)
        country.save()
        for town in self.towns:
            models.Group(name=town, group_type='town', parent=country).save()
        q = models.Group.objects.filter(group_type='town')
        l = []
        for i in range(5):
            l.extend(q)
        random.shuffle(l)
        for i in range(80):
            obj = models.Group(uuid=uuid.uuid1(self.nodes[i]),
                               name=u'学校%d' % i, group_type='school',
                               parent=l[i])
            obj.save()

    def _generate_setting(self):
        models.Setting(name='server_type', value='country').save()
        models.Setting(name='installed', value='True').save()
        models.Setting(name='install_step', value='-1').save()
        models.Setting(name='province', value='湖北省').save()
        models.Setting(name='city', value='恩施土家族苗族自治州').save()
        models.Setting(name='country', value='恩施市').save()

    def _generate_newterm(self):
        '''为县级服务器生成两个新学期'''
        country = models.Group.objects.get(group_type='country')
        models.NewTerm(school_year='2013-2014', term_type='春季学期',
                       start_date=parse_date('2014-2-1'),
                       end_date=parse_date('2014-6-30'),
                       country=country, deleted=False,
                       schedule_time=150).save()
        models.NewTerm(school_year='2014-2015', term_type='秋季学期',
                       start_date=parse_date('2014-8-1'),
                       end_date=parse_date('2015-1-30'),
                       country=country, deleted=False,
                       schedule_time=180).save()

    def _generate_term(self):
        '''每个学校两个学期'''
        q = models.Group.objects.filter(group_type='school')
        for school in q:
            obj = models.Term(uuid=uuid.uuid1(getnode_from_uuid(school.uuid)),
                              school_year='2013-2014',
                              term_type='春季学期',
                              start_date=parse_date('2014-2-1'),
                              end_date=parse_date('2014-6-30'),
                              school=school,
                              deleted=False,
                              schedule_time=150)
            obj.save()
            obj = models.Term(uuid=uuid.uuid1(getnode_from_uuid(school.uuid)),
                              school_year='2014-2015',
                              term_type='秋季学期',
                              start_date=parse_date('2014-8-1'),
                              end_date=parse_date('2015-1-30'),
                              school=school,
                              deleted=False,
                              schedule_time=180)
            obj.save()

    def _generate_grade(self):
        '''每个新学期9个年级'''
        q = models.Term.objects.filter(term_type='秋季学期')
        for term in q:
            for name in ('一', '二', '三', '四', '五', '六', '七', '八', '九'):
                obj = models.Grade(uuid=uuid.uuid1(getnode_from_uuid(term.uuid)),
                                   name=name, number=str_util.grade_name_to_number(name),
                                   term=term)
                obj.save()

    def _generate_teacher(self):
        q = models.Group.objects.filter(group_type='school')
        for school in q:
            for i in range(1, 51):
                obj = models.Teacher(uuid=uuid.uuid1(getnode_from_uuid(school.uuid)),
                                     sequence=i, name=u'教师%d' % i,
                                     password='0101', sex='male',
                                     edu_background='本科',
                                     birthday=parse_date('1980-1-1'),
                                     title='一级', school=school)
                obj.save()

    def _generate_class(self):
        '''每个年级两个班级'''
        q = models.Grade.objects.all()
        i = 0
        for grade in q:
            teachers = models.Teacher.objects.filter(school=grade.term.school)
            for name in ('1', '2'):
                obj = models.Class(uuid=uuid.uuid1(getnode_from_uuid(grade.uuid)),
                                   name=name,
                                   number=str_util.class_name_to_number(name),
                                   grade=grade,
                                   teacher=teachers[i])
                obj.save()
                i += 1
                if i > 49:
                    i = 0

    def _generate_newlessonname(self):
        '''40个课程'''
        country = models.Group.objects.get(group_type='country')
        for i in range(40):
            d = {'name': u'课程%d' % i, 'types': [u'小学', ]}
            form = NewLessonNameForm(d)
            if form.is_valid():
                obj = form.save()
                types = d.get('types')
                for t in types:
                    lt, c = models.NewLessonType.objects.get_or_create(country=country,
                                                                       name=t)
                    models.NewLessonNameType(newlessontype=lt,
                                             newlessonname=obj).save()

    def _generate_lessonname(self):
        '''每个学校40个课程'''
        q = models.Group.objects.filter(group_type='school')
        for school in q:
            for i in range(40):
                obj = models.LessonName(uuid=uuid.uuid1(getnode_from_uuid(school.uuid)),
                                        school=school,
                                        name=u'课程%d' % i, deleted=False)
                obj.save()

    def _generate_lessonperiod(self):
        '''每个学校每天20节课'''
        q = models.Term.objects.filter(term_type='秋季学期')
        for term in q:
            for i in range(1, 21):
                obj = models.LessonPeriod(uuid=uuid.uuid1(getnode_from_uuid(term.uuid)),
                                          term=term, sequence=i,
                                          start_time=parse_time('%d:00:00' % i),
                                          end_time=parse_time('%d:45:00' % i))
                obj.save()

    def _generate_lessonschedule(self):
        '''每个班级每天20节课，每周5天'''
        q = models.Class.objects.all()
        count = 0
        for c in q:
            print count
            lessons = []
            lessons.extend(models.LessonName.objects.filter(school=c.grade.term.school))
            lessons.extend(models.LessonName.objects.filter(school=c.grade.term.school))
            lessons.extend(models.LessonName.objects.filter(school=c.grade.term.school))
            random.shuffle(lessons)
            i = 0
            for weekday in ('mon', 'tue', 'wed', 'thu', 'fri'):
                for lp in models.LessonPeriod.objects.filter(term=c.grade.term):
                    obj = models.LessonSchedule(uuid=uuid.uuid1(getnode_from_uuid(c.uuid)),
                                                class_uuid=c, lesson_period=lp,
                                                weekday=weekday,
                                                lesson_name=lessons[i])
                    obj.save()
                    i += 1
                    count += 1

    def _generate_lessonteacher(self):
        '''每个班级的每个课程都安排一个老师'''
        q = models.Group.objects.filter(group_type='school')
        count = 0
        for school in q:
            print count
            teachers = models.Teacher.objects.filter(school=school)
            classes = models.Class.objects.filter(grade__term__school=school)
            i = 0
            for c in classes:
                lessons = c.lessonschedule_set.values_list('lesson_name', flat=True).distinct()
                lessons = models.LessonName.objects.filter(uuid__in=lessons)
                for lesson in lessons:
                    models.LessonTeacher(class_uuid=c, teacher=teachers[i],
                                         lesson_name=lesson,
                                         schedule_time=200,
                                         finished_time=0).save()
                    i += 1
                    if i >= 50:
                        i = 0
                    count += 1

    def _generate_resource(self):
        '''20个资源来源，20个资源类型'''
        country = models.Group.objects.get(group_type='country')
        for i in range(20):
            models.ResourceFrom(country=country, value=u'资源来源%d' % i).save()
            models.ResourceFrom(country=country, value=u'资源类型%d' % i).save()

    @transaction.atomic
    def _generate_teacherloginlog(self):
        '''每个工作日每个班级20节课'''
        t = models.NewTerm.objects.all()[1]
        delta = (t.end_date - t.start_date).days + 1
        l = [t.start_date + datetime.timedelta(days=i) for i in range(0, delta)]
        days = [i for i in l if i.weekday() not in (5, 6)][:70]
        classes = models.Class.objects.all()
        weekday_l = ['mon', 'tue', 'wed', 'thu', 'fri']
        counter = 0
        days = days[:1]
        for day in days:
            weekday = weekday_l[day.weekday()]
            for sequence in range(1, 21):
                for c in classes:
                    print counter
                    lp = models.LessonPeriod.objects.get(term=c.grade.term,
                                                         sequence=sequence)
                    created_at = datetime.datetime.combine(day, lp.start_time)
                    created_at += datetime.timedelta(seconds=random.randint(0, 300))
                    ls = models.LessonSchedule.objects.get(class_uuid=c,
                                                           lesson_period=lp,
                                                           weekday=weekday)
                    lt = models.LessonTeacher.objects.get(class_uuid=c,
                                                          lesson_name=ls.lesson_name)
                    obj = models.TeacherLoginLog(teacher_name=lt.teacher.name,
                                                 lesson_name=lt.lesson_name.name,
                                                 province_name=c.grade.term.school.parent.parent.parent.parent.name,
                                                 city_name=c.grade.term.school.parent.parent.parent.name,
                                                 country_name=c.grade.term.school.parent.parent.name,
                                                 town_name=c.grade.term.school.parent.name,
                                                 school_name=c.grade.term.school.name,
                                                 term_school_year=c.grade.term.school_year,
                                                 term_type=c.grade.term.term_type,
                                                 term_start_date=c.grade.term.start_date,
                                                 term_end_date=c.grade.term.end_date,
                                                 grade_name=c.grade.name,
                                                 class_name=c.name,
                                                 lesson_period_sequence=lp.sequence,
                                                 lesson_period_start_time=lp.start_time,
                                                 lesson_period_end_time=lp.end_time,
                                                 weekday=weekday,
                                                 teacher=lt.teacher,
                                                 province=c.grade.term.school.parent.parent.parent.parent,
                                                 city=c.grade.term.school.parent.parent.parent,
                                                 country=c.grade.term.school.parent.parent,
                                                 town=c.grade.term.school.parent,
                                                 school=c.grade.term.school,
                                                 term=c.grade.term,
                                                 grade=c.grade,
                                                 class_uuid=c,
                                                 lesson_period=lp,
                                                 lesson_teacher=lt,
                                                 created_at=created_at)
                    obj.save()
                    counter += 1

    def _calculate_finished_time(self):
        '''计算教师授课次数，更新LessonTeacher'''
        q = models.LessonTeacher.objects.all()
        counter = 0
        for i in q:
            print counter
            t = models.TeacherLoginLog.objects.all()
            t = t.filter(teacher=i.teacher,
                         class_uuid=i.class_uuid,
                         lesson_name=i.lesson_name.name)
            n = t.count()
            if n != i.finished_time:
                i.finished_time = n
                i.save()
            counter += 1

    def _generate_teacherlogintime(self):
        '''采样teacherloginlog，生成一部分teacherlogintime数据'''
        q = models.TeacherLoginLog.objects.all()[760000:800000]
        counter = 0
        for i in q:
            print counter
            counter += 1
            if random.choice((True, False, False, False)) is False:
                continue
            t = int(math.ceil((45 - abs(random.gauss(0, 4))) * 60))
            obj = models.TeacherLoginTime(uuid=uuid.uuid1(getnode_from_uuid(i.uuid)),
                                          teacherloginlog=i,
                                          login_time=t)
            obj.save()

    def handle(self, *args, **options):
        cursor = connection.cursor()
        cursor.execute('SET unique_checks=0')
        cursor.execute('SET foreign_key_checks=0')
        # self._create_admin()
        # self._generate_school()
        # self._generate_setting()
        # self._generate_newterm()
        # self._generate_term()
        # self._generate_grade()
        # self._generate_teacher()
        # self._generate_class()
        # self._generate_newlessonname()
        # self._generate_lessonname()
        # self._generate_lessonperiod()
        # self._generate_lessonschedule()
        self._generate_lessonteacher()
        self._generate_resource()
        # self._generate_teacherloginlog()
        # self._calculate_finished_time()
        # self._generate_teacherlogintime()
        cursor.execute('SET unique_checks=1')
        cursor.execute('SET foreign_key_checks=1')
