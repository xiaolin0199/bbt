#!/usr/bin/env python
# coding=utf-8
import datetime
import hashlib
import math
import random
import uuid
import MySQLdb
import threading

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.db import transaction
from django.utils.dateparse import parse_date
from django.utils.dateparse import parse_time
from BanBanTong.db import models
from BanBanTong.forms.new_lesson_name import NewLessonNameForm
from BanBanTong.utils import str_util

DEBUG = True


class Command(BaseCommand):

    global DEBUG
    # country obj
    country_obj = models.Group.objects.get(group_type='country')
    # city obj
    city_obj = models.Group.objects.get(group_type='city')
    # province obj
    province_obj = models.Group.objects.get(group_type='province')

    # 学校对象集合
    school_list = []
    # 新学年学期信息集合
    newterm_list = []
    # 上课课程信息集合
    newlessonname_list = []
    # 学校学年学期集合
    term_list = []

    # 学期数量  , 学年开始年份
    term_count = 2
    start_year = 2014

    # 学校数量
    school_count = 10

    # 上课课程数量
    lesson_count = 12

    # 老师数量
    teacher_count = 50

    # 打印数量
    print_count = 10000

    def init_newterm(self):
        '''
            1. 初始化 20个学年学期 ( 每年秋季3.01 ～ 6.30 ， 春季9.1 ～ 1.30 )
        '''
        print '--- newterm ---'

        term_type = [u'秋季学期', u'春季学期']
        term_type_detail = {u'秋季学期': [(3, 1), (6, 30)], u'春季学期': [(9, 1), (1, 30)]}

        for one in range(0, self.term_count):
            if one == 0:
                # 判断是哪个学期 (秋或春)
                type = term_type[0]
                # 计算每个学期的开始，截止日期
                detail = term_type_detail[type]
                start_date = datetime.date(self.start_year, detail[0][0], detail[0][1])
                end_date = datetime.date(self.start_year, detail[1][0], detail[1][1])

            else:
                mod = one % 2
                if mod == 0:
                    self.start_year += 1
                # 判断是哪个学期 (秋或春)
                type = term_type[mod]
                # 计算每个学期的开始，截止日期
                detail = term_type_detail[type]
                start_date = datetime.date(self.start_year, detail[0][0], detail[0][1])
                if mod == 0:  # 秋季学期 start_year不加1
                    end_date = datetime.date(self.start_year, detail[1][0], detail[1][1])
                else:
                    end_date = datetime.date(self.start_year + 1, detail[1][0], detail[1][1])

            # join
            self.newterm_list.append(['%s-%s' % (self.start_year, self.start_year + 1), type, start_date, end_date])

        # 插入数据库
        for one in self.newterm_list:
            obj, c = models.NewTerm.objects.get_or_create(
                school_year=one[0],
                term_type=one[1],
                start_date=one[2],
                end_date=one[3],
                country=self.country_obj,
                defaults={
                    'uuid': str(uuid.uuid1()).upper()
                }
            )

        if DEBUG:
            # for one in self.newterm_list:
            #    print one
            pass

    def init_newlessonname(self):
        '''
            2. 新建 30门开课课程 ；
        '''
        print '--- newlessonname ---'

        names = [u"语文", u"数学", u"英语", u"音乐", u"体育", u"品德与生活", u"体育与健康", u"信息技术", u"劳动和实用技术", u"化学", u"历史", u"品德与心理", u"品德与社会", u"团队活动", u"地理",
                 u"安全教育", u"少队活动", u"快乐体育", u"快乐数学", u"思想品德", u"校本课程", u"物理", u"班队活动", u"生物", u"研究性学习", u"社会实践", u"科学", u"科技文体活动", u"综合实践", u"美术"]

        self.newlessonname_list = names[:self.lesson_count]

        # 插入数据库
        for one in self.newlessonname_list:
            obj, c = models.NewLessonName.objects.get_or_create(
                name=one,
                country=self.country_obj,
                defaults={
                    'uuid': str(uuid.uuid1()).upper()
                }
            )

        if DEBUG:
            # for one in self.newlessonname_list:
            #    print one
            pass

    def init_node(self):
        '''
            3. 生成100个学校 (服务器汇聚管理)；
        '''
        print '--- node ---'

        node_list = []
        for one in range(1, self.school_count + 1):
            name = u'测试学校%03d' % one
            communicate_key = str_util.generate_node_key()

            node_list.append([name, communicate_key])

        # 插入数据库
        for one in node_list:
            obj, c = models.Node.objects.get_or_create(
                name=one[0],
                defaults={
                    'communicate_key': one[1],
                    'db_version': 100,
                    'last_upload_id': 1  # 可回传
                }
            )

        if DEBUG:
            # for one in node_list:
            #    print one
            pass

    def init_group(self):
        '''
            4. 生成Group 数据，包括每个学校的上级乡镇信息；
            5. 生成 Setting 数据 ，包括每个学校的Group uuid 值；
        '''
        print '--- school ---'

        nodes = models.Node.objects.all()
        for index, node in enumerate(nodes, 1):
            school_name = node.name
            # town_name
            town_name = u'测试街道%02d' % (index % 15)

            # 插入group数据库，先插town,再插school
            town, c = models.Group.objects.get_or_create(
                group_type='town',
                name=town_name,
                parent=self.country_obj,
                defaults={
                    'uuid': str(uuid.uuid1()).upper()
                }
            )

            school, c = models.Group.objects.get_or_create(
                group_type='school',
                name=school_name,
                parent=town,
                defaults={
                    'uuid': str(uuid.uuid1()).upper()
                }
            )

            # 备用
            self.school_list.append(school)

            # 生成setting数据表数据
            node_id = node.id
            setting_name = u'node_%s_school_uuid' % node_id
            setting_value = school.uuid

            s, c = models.Setting.objects.get_or_create(
                name=setting_name,
                value=setting_value,
                defaults={
                    'uuid': str(uuid.uuid1()).upper()
                }
            )

        if DEBUG:
            # for one in self.school_list:
            #    print one
            pass

    def init_base(self):
        '''
            1. 新建 20个学年学期 ( 每年秋季3.01 ～ 6.30 ， 春季9.1 ～ 1.30 )

            2. 新建 30门开课课程 ；

            3. 生成100个学校 (服务器汇聚管理)；

            4. 生成Group 数据，包括每个学校的上级乡镇信息；

            5. 生成 Setting 数据 ，包括每个学校的Group uuid 值；
        '''
        # ONE: 自动创建NewTerm学年学期
        self.init_newterm()

        # TWO: 自动创建NewLessonName上课课程
        self.init_newlessonname()

        # THREE: 自动创建Node（100个学校）
        self.init_node()

        # FOUR: 自动创建Group(100个学校，及其上级街道乡镇)
        # FIVE: 自动创建Setting数据
        self.init_group()

    def create_term(self):
        '''
            6.  根据学校数据，生成对应的term ( 100 * 20 = 2000 )
        '''
        print '--- term ---'

        for one in self.newterm_list:
            for school in self.school_list:
                obj, c = models.Term.objects.get_or_create(
                    school=school,
                    school_year=one[0],
                    term_type=one[1],
                    start_date=one[2],
                    end_date=one[3],
                    defaults={
                        'schedule_time': 180,
                        'uuid': str(uuid.uuid1()).upper()
                    }
                )

                self.term_list.append(obj)

        if DEBUG:
            # for one in self.term_list:
            #    print one
            pass

    def create_lessonname(self):
        '''
            6.  根据学校数据，生成对应的lessonname ( 100 * 30 = 3000 )
        '''
        print '--- lessonname ---'

        for school in self.school_list:
            for lessonname in self.newlessonname_list:
                obj, c = models.LessonName.objects.get_or_create(
                    school=school,
                    name=lessonname,
                    defaults={
                        'uuid': str(uuid.uuid1()).upper()
                    }
                )

        if DEBUG:
            pass

    def create_teacher(self):
        '''
            6.  根据学校数据，生成对应的teacher ( 100 * 50 = 5000 )
        '''
        print '--- teacher ---'
        for school in self.school_list:
            for one in range(1, self.teacher_count + 1):
                name = u'测试老师%03d' % one
                birthday = datetime.date(1980, 1, 1)
                obj, c = models.Teacher.objects.get_or_create(
                    school=school,
                    name=name,
                    birthday=birthday,
                    defaults={
                        'uuid': str(uuid.uuid1()).upper(),
                        'password': '0101',
                        'edu_background': u'本科'
                    }
                )

        if DEBUG:
            pass

    def create_grade_class(self):
        '''
            7. 生成 Grade 年级基础数据 ， 需要用到 term ( 70%学校有6个年级，30%学校有3个年级 ， 按100个学校算，总共510 个年级 ， 20个学期即 510 * 20 = 10200 )；
            8. 生成 Class 班级基础数据，需要用到 grade ，teacher ( 平均每个年级5个班 ， 按100个学校，总共2550个班级 ， 20个学期即 2550 * 20 = 51000 ) ；
        '''
        print '--- grade & class ---'
        now_start = datetime.datetime.now()
        print 'start date: ', now_start

        class_print_count = 0
        # 所有学校
        schools = models.Group.objects.filter(group_type='school')
        school_count = schools.count()

        # 70% 的学校有6个年级，其他的 有3个年级
        school_count_6 = int(school_count * 0.7)

        detail_dict = {}
        school_6 = schools[0: school_count_6]  # 有6个年级的学校
        for school in school_6:
            detail_dict.update({school: [(u'一', 1), (u'二', 2), (u'三', 3), (u'四', 4), (u'五', 5), (u'六', 6)]})
        school_3 = schools[school_count_6: school_count]  # 有3个年级的学校
        for school in school_3:
            detail_dict.update({school: [(u'一', 1), (u'二', 2), (u'三', 3)]})

        # 生成数据
        # 1. 哪个学校分别是几个年级
        for school, value in detail_dict.iteritems():
            # 2. 为该学校的所有学期添加上年级
            terms = models.Term.objects.filter(school=school)
            for term in terms:
                for name, number in value:
                    # 添加年级
                    grade, c = models.Grade.objects.get_or_create(
                        term=term,
                        name=name,
                        number=number,
                        defaults={
                            'uuid': str(uuid.uuid1()).upper()
                        }
                    )

                    # 添加班级 (平均5个)
                    for class_name in range(1, 6):
                        teacher = school.school_teacher_set.all()[class_name - 1: class_name][0]
                        obj, c = models.Class.objects.get_or_create(
                            grade=grade,
                            teacher=teacher,
                            name=class_name,
                            number=class_name,
                            defaults={
                                'uuid': str(uuid.uuid1()).upper()
                            }
                        )

                        class_print_count += 1

                        if class_print_count % self.print_count == 0:
                            print 'class adding: ', class_print_count

        if DEBUG:
            pass

        print 'total use: ', datetime.datetime.now() - now_start

    def create_lessonperiod(self):
        '''
            9. 生成 LessonPeriod 作息班基础数据，需要用到 term （统一按6个作息上课， 20个学期100个学校即 12000）；
        '''
        print '--- lessonperiod ---'

        # 节次
        periods = [8, 9, 10, 14, 15, 16]
        times = ((10, 50),)
        for term in self.term_list:
            seq = 1
            for j in periods:
                for start, end in times:
                    period, c = models.LessonPeriod.objects.get_or_create(
                        term=term,
                        sequence=seq,
                        start_time=datetime.time(j, start),
                        end_time=datetime.time(j, end),
                        defaults={
                            'uuid': str(uuid.uuid1()).upper()
                        }
                    )

                    seq += 1

        if DEBUG:
            pass

    """
    #@transaction.commit_manually
    def create_lessonschedule_lessonteacher(self):
        '''
            10. 生成 LessonSchedule 课程表基础数据，需要用到 class，lessonperiod，lessonname ( 20个学期即 51000 * 5 * 6 = 1530000)；
            11. 生成LessonTeacher 授课老师基础数据，需要用到 class ， lessonname ， teacher ( 20个学期即 51000 * 5 * 6 = 1530000 )；
        '''
        print '--- lessonschedule & lessonteacher ---'
        now_start = datetime.datetime.now()
        print 'start date: ' , now_start

        lessonschedule_print_count = 0

        classes = models.Class.objects.all()
        for c in classes.iterator():
            lessons = c.grade.term.school.lessonname_set.all()
            lessons_count = lessons.count()
            teachers = c.grade.term.school.school_teacher_set.all()
            teachers_count = teachers.count()

            i = 0
            j = 0

            for weekday in ('mon', 'tue', 'wed', 'thu', 'fri'):
                #sid = transaction.savepoint()
                #sid_count = 0
                for lp in models.LessonPeriod.objects.filter(term=c.grade.term):
                    # 添加课程表
                    s , create = models.LessonSchedule.objects.get_or_create(
                        class_uuid = c,
                        lesson_period = lp,
                        weekday = weekday,
                        lesson_name = lessons[i],
                        defaults = {
                            'uuid': str(uuid.uuid1()).upper()
                        }
                    )

                    lessonschedule_print_count += 1

                    if lessonschedule_print_count % (self.print_count / 10) == 0:
                        print 'lessonschedule_print_count adding: ' , lessonschedule_print_count

                    #为该课程添加老师
                    t , create = models.LessonTeacher.objects.get_or_create(
                        class_uuid=c,
                        lesson_name=lessons[i],
                        defaults = {
                            'teacher': teachers[j],
                            'schedule_time': 200,
                            'uuid': str(uuid.uuid1()).upper()
                        }
                    )

                    i += 1
                    j += 1
                    if i >= lessons_count:
                        i = 0
                    if j>= teachers_count:
                        j = 0

                    #sid_count += 1
                    #if sid_count % 200 == 0: # 这个是最合适的
                    #    transaction.savepoint_commit(sid)
                    #    transaction.commit()

                #transaction.commit()

        if DEBUG:
            pass

        print 'total use: ' , datetime.datetime.now() - now_start
    """

    def create_lessonschedule(self):
        '''
            10. 生成 LessonSchedule 课程表基础数据，需要用到 class，lessonperiod，lessonname ( 20个学期即 51000 * 5 * 6 = 1530000)；
        '''
        print '--- lessonschedule ---'
        now_start = datetime.datetime.now()
        print 'start date: ', now_start

        lessonschedule_print_count = 0

        grades = models.Grade.objects.select_related().all()
        for grade in grades.iterator():
            querylist_schedule = []
            for c in grade.class_set.select_related().all().iterator():
                lessons = []
                lessons.extend(models.LessonName.objects.filter(school=grade.term.school))
                random.shuffle(lessons)
                i = 0
                for weekday in ('mon', 'tue', 'wed', 'thu', 'fri'):
                    for lp in models.LessonPeriod.objects.filter(term=grade.term):
                        obj = models.LessonSchedule(uuid=str(uuid.uuid1()).upper(),
                                                    class_uuid=c, lesson_period=lp,
                                                    weekday=weekday,
                                                    lesson_name=lessons[i])
                        # obj.save()
                        querylist_schedule.append(obj)
                        i += 1
                        if i >= len(lessons):
                            i = 0

                        lessonschedule_print_count += 1

                        if lessonschedule_print_count % (self.print_count / 10) == 0:
                            print 'lessonschedule_print_count adding: ', lessonschedule_print_count

            models.LessonSchedule.objects.bulk_create(querylist_schedule)

        print 'total use: ', datetime.datetime.now() - now_start

    def create_lessonteacher(self):
        '''
            11. 生成LessonTeacher 授课老师基础数据，需要用到 class ， lessonname ， teacher ( 20个学期即 51000 * 5 * 6 = 1530000 )；
        '''
        print '--- lessonteacher ---'
        now_start = datetime.datetime.now()
        print 'start date: ', now_start

        lessonteacher_print_count = 0

        q = models.Group.objects.filter(group_type='school')
        for school in q:
            teachers = models.Teacher.objects.filter(school=school)
            grades = models.Grade.objects.select_related().filter(term__school=school)
            for grade in grades.iterator():
                classes = grade.class_set.select_related().all()
                i = 0
                querylist_lessonteacher = []
                for c in classes.iterator():
                    lessons = c.lessonschedule_set.values_list('lesson_name', flat=True).distinct()
                    lessons = models.LessonName.objects.filter(uuid__in=lessons)
                    for lesson in lessons:
                        obj = models.LessonTeacher(uuid=str(uuid.uuid1()).upper(),
                                                   class_uuid=c,
                                                   teacher=teachers[i],
                                                   lesson_name=lesson,
                                                   schedule_time=200,
                                                   finished_time=0)

                        querylist_lessonteacher.append(obj)

                        i += 1
                        if i >= len(teachers):
                            i = 0

                        lessonteacher_print_count += 1

                        if lessonteacher_print_count % (self.print_count / 10) == 0:
                            print 'lessonteacher_print_count adding: ', lessonteacher_print_count

                models.LessonTeacher.objects.bulk_create(querylist_lessonteacher)

        print 'total use: ', datetime.datetime.now() - now_start

    def create_base(self):
        '''
            6.  根据学校数据，生成对应的term ( 100 * 20 = 2000 ) ， lessonname ( 100 * 30 = 3000 ) ， teacher ( 100 * 50 = 5000 ) 表数据 ；

            7. 生成 Grade 年级基础数据 ， 需要用到 term ( 70个学校有6个年级，30个学校有3个年级 ， 总共510 个年级 ， 20个学期即 510 * 20 = 10200 )；

            8. 生成 Class 班级基础数据，需要用到 grade ，teacher (平均每个年级5个班 ， 总共2550个班级 ， 20个学期即 2550 * 20 = 51000 ) ；

            9. 生成 LessonPeriod 作息班基础数据，需要用到 term （统一按6个作息上课， 20个学期100个学校即 12000）；

            10. 生成 LessonSchedule 课程表基础数据，需要用到 class，lessonperiod，lessonname ( 20个学期即 51000 * 5 * 6 = 1530000)；

            11. 生成LessonTeacher 授课老师基础数据，需要用到 class ， lessonname ， teacher ( 20个学期即 51000 * 5 * 6 = 1530000 )；
        '''

        # SIX: 生成对应的term
        self.create_term()

        # SIX: 生成对应的lessonname
        self.create_lessonname()

        # SIX: 生成对应的teacher
        self.create_teacher()

        # SEVER & EIGHT: 生成 Grade & class 年级班级基础数据
        self.create_grade_class()

        # NINE: 生成 lessonperiod 作息班基础数据
        self.create_lessonperiod()

        # TEN: 生成 lessonschedule 课程表基础数据
        # ELEVEN: 生成 lessonteacher 授课老师基础数据
        # self.create_lessonschedule_lessonteacher()
        self.create_lessonschedule()

        self.create_lessonteacher()

    def handle(self, *args, **options):
        cursor = connection.cursor()
        cursor.execute('SET unique_checks=0')
        cursor.execute('SET foreign_key_checks=0')

        #

        # 县级服务预先初始化的数据，
        # NewTerm, NewLessonName
        # Node ,  Group ,  Setting数据
        self.init_base()

        # 生成基础数据，包括
        # term, lessonname, teacher, grade, class
        # lessonperiod, lessonschedule, lessonteacher
        self.create_base()

        cursor.execute('SET unique_checks=1')
        cursor.execute('SET foreign_key_checks=1')
