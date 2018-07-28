# coding=utf-8
import os
import codecs
import datetime
import logging
from django.core.management.base import BaseCommand
# from django.db import connection

from BanBanTong.db import models
from BanBanTong.db.models import _make_uuid
from BanBanTong import constants

logger = logging.getLogger(__name__)


def create_new_obj(obj, **fk_fields):
    old_pk = obj.pk
    obj.pk = None
    obj.uuid = _make_uuid()
    for k, v in fk_fields.items():
        if isinstance(v, dict):
            value = v[getattr(obj, k).pk]
        else:
            value = v
        setattr(obj, k, value)
    obj.save()
    assert old_pk != obj.pk
    return obj


def inherit_school_info(oldterm, newterm, school, log_fd):
    term_map = {}
    period_map = {}
    grade_map = {}
    class_map = {}
    computerclass_map = {}
    classmac_map = {}
    classtime_map = {}
    lessonteacher_map = {}
    lessonschedule_map = {}

    old_schoolterms = models.Term.objects.filter(
        school=school,
        school_year=oldterm.school_year,
        term_type=oldterm.term_type
    )
    new_schoolterm, is_new = models.Term.objects.get_or_create(
        school=school,
        school_year=newterm.school_year,
        term_type=newterm.term_type,
        defaults={
            'start_date': newterm.start_date,
            'end_date': newterm.end_date,
            'schedule_time': newterm.schedule_time,
            'deleted': newterm.deleted
        })
    if not old_schoolterms.exists():
        log_fd.write('EXC old_schoolterm:            %s\n' % old_schoolterms.count())
        return
    old_schoolterm = old_schoolterms.first()
    term_map[old_schoolterm.pk] = new_schoolterm
    old_periods = models.LessonPeriod.objects.filter(term=old_schoolterm)
    old_grades = models.Grade.objects.filter(term=old_schoolterm)
    old_classes = models.Class.objects.filter(grade__in=old_grades)
    old_computerclasses = models.ComputerClass.objects.filter(class_bind_to__grade__in=old_grades)
    old_classmac = models.ClassMacV2.objects.filter(class_uuid__in=old_classes)
    old_classtime = models.ClassTime.objects.filter(class_uuid__in=old_classes)
    old_lessonteachers = models.LessonTeacher.objects.filter(class_uuid__in=old_classes)
    old_lessonschedules = models.LessonSchedule.objects.filter(class_uuid__in=old_classes)

    old_periods = models.LessonPeriod.objects.filter(term=new_schoolterm)
    new_grades = models.Grade.objects.filter(term=new_schoolterm)
    new_classes = models.Class.objects.filter(grade__in=new_grades)
    new_computerclasses = models.ComputerClass.objects.filter(class_bind_to__grade__in=new_grades)
    new_classmac = models.ClassMacV2.objects.filter(class_uuid__in=new_classes)
    new_classtime = models.ClassTime.objects.filter(class_uuid__in=new_classes)
    new_lessonteachers = models.LessonTeacher.objects.filter(class_uuid__in=new_classes)
    new_lessonschedules = models.LessonSchedule.objects.filter(class_uuid__in=new_classes)

    # period_map
    for old in old_periods:
        oid = old.pk
        new_objs = old_periods.filter(sequence=old.sequence)
        if new_objs.exists():
            new = new_objs.first()
        else:
            new = create_new_obj(old, term=new_schoolterm)

        period_map[oid] = new

    # grade_map
    for old in old_grades:
        oid = old.pk
        new_objs = new_grades.filter(name=old.name)
        if new_objs.exists():
            new = new_objs.first()
        else:
            # new = models.Grade.objects.create(name=old.name, number=old.number, term=new_schoolterm)
            new = create_new_obj(old, term=new_schoolterm)
        grade_map[oid] = new

    # class_map
    for old in old_classes:
        oid = old.pk
        new_objs = new_classes.filter(name=old.name, grade__name=old.grade.name)
        if new_objs.exists():
            new = new_objs.first()
        else:
            new = create_new_obj(old, grade=grade_map, teacher=None, last_active_time=None)
        class_map[oid] = new

    # computer_class_map
    for old in old_computerclasses:
        oid = old.pk
        new_objs = new_computerclasses.filter(class_bind_to__name=old.name, class_bind_to__grade__name=old.grade.name)
        if new_objs.exists():
            new = new_objs.first()
        else:
            new = create_new_obj(old)
        computerclass_map[oid] = new

    # classmac_map
    for old in old_classmac:
        oid = old.pk
        new_objs = new_classmac.filter(mac=old.mac)
        if new_objs.exists():
            new = new_objs.first()
        else:
            new = create_new_obj(old, class_uuid=class_map)
        classmac_map[oid] = new

    # classtime_map
    for old in old_classtime:
        oid = old.pk
        new_objs = new_classtime.filter(class_uuid__name=old.class_uuid.name,
                                        class_uuid__grade__name=old.class_uuid.grade.name)
        if new_objs.exists():
            new = new_objs.first()
        else:
            new = create_new_obj(old, class_uuid=class_map)
        classtime_map[oid] = new

    # lessonteacher_map
    for old in old_lessonteachers:
        oid = old.pk
        try:
            new_objs = new_lessonteachers.filter(class_uuid__name=old.class_uuid.name, class_uuid__grade__name=old.class_uuid.grade.name,
                                                 teacher=old.teacher, lesson_name=old.lesson_name)
        except Exception as e:
            log_fd.write('EXC lessonteachers:            %s\n' % str(e))
            continue
        if new_objs.exists():
            new = new_objs.first()
        else:
            new = create_new_obj(old, class_uuid=class_map)
        lessonteacher_map[oid] = new

    # lessonschedule_map
    for old in old_lessonschedules:
        oid = old.pk
        new_objs = new_lessonschedules.filter(class_uuid__name=old.class_uuid.name, class_uuid__grade__name=old.class_uuid.grade.name,
                                              lesson_period__sequence=old.lesson_period.sequence)
        if new_objs.exists():
            new = new_objs.first()
        else:
            new = create_new_obj(old, class_uuid=class_map)
        lessonschedule_map[oid] = new

    log_fd.write('school:            %s\n' % school)
    log_fd.write('term_map:          %s\n' % term_map)
    log_fd.write('period_map:        %s\n' % period_map)
    log_fd.write('grade_map:         %s\n' % grade_map)
    log_fd.write('class_map:         %s\n' % class_map)
    log_fd.write('computerclass_map: %s\n' % computerclass_map)
    log_fd.write('class2mac_map:     %s\n' % classmac_map)
    log_fd.write('classtime:         %s\n' % classtime_map)
    log_fd.write('lessonteacher_map: %s\n' % lessonteacher_map)
    log_fd.write('schedule_map:      %s\n\n' % lessonschedule_map)

    print u'处理学期信息:', len(term_map.keys())
    print u'处理作息时间信息:', len(period_map.keys())
    print u'处理年级信息:', len(grade_map.keys())
    print u'处理班级信息:', len(class_map.keys())
    print u'处理电脑教室信息:', len(computerclass_map.keys())
    print u'处理班级绑定信息:', len(classmac_map.keys())
    print u'处理班级时长信息:', len(classtime_map.keys())
    print u'处理授课教师信息:', len(lessonteacher_map.keys())
    print u'处理课程表信息:', len(lessonschedule_map.keys()), '\n'


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('-o', dest='oldterm', help='oldterm')
        parser.add_argument('-n', dest='newterm', help='newterm')
        parser.add_argument('-s', dest='school', help='newterm')

    def handle(self, *args, **options):
        # cursor = connection.cursor()
        # cursor.execute('SET unique_checks=0')
        # cursor.execute('SET foreign_key_checks=0')
        server_type = models.Setting.getvalue('server_type')
        if server_type not in ['country']:
            print u'错误的服务器级别: %s', server_type
            return

        # if models.NewTerm.get_current_term():
        #     print u'当前学期尚未结束'
        #     return

        newterm = models.NewTerm.get_current_or_next_term()
        if not newterm:
            # yes = raw_input(y'数据库中尚未创建新学期, 是否创建[Y/n]:')
            # if yes.lower() == 'y':
            print u'数据库中尚未创建新学期'
            return
        oldterm = models.NewTerm.get_previous_term(term=newterm)

        if options['school']:
            schools = models.Group.objects.filter(group_type='school', uuid__in=[options['school']])
            if not schools.exists():
                print u'错误的学校UUID'
                return
        else:
            schools = models.Group.objects.filter(group_type='school')

        print u'旧学期:%s\n新学期:%s\n学校:%s\n' % (oldterm, newterm, ' '.join(list(schools.values_list('name', flat=True))))
        begin = raw_input(u'开始处理[Y/n]?')
        if not begin.lower() == 'y':
            return

        now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        tmp_file = os.path.join(constants.BANBANTONG_BASE_PATH, 'files', 'tmp', 'backup', 'init_next_term_%s.info' % now)
        with codecs.open(tmp_file, 'ab') as f:
            for school in schools:
                # raw_input('continue: %s' % school)
                print u'开始处理: %s' % school
                inherit_school_info(oldterm, newterm, school, f)

        # cursor.execute('SET unique_checks=1')
        # cursor.execute('SET foreign_key_checks=1')
