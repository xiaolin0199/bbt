#coding=utf-8
import datetime
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count
from django.db.models import Sum
from BanBanTong.db import models
from BanBanTong.utils import datetimeutil
from django.conf import settings
DEBUG = settings.DEBUG
del settings


class Command(BaseCommand):
    '''重新计算综合分析的次数和时长'''

    def calculate_lesson_count(self, term, week, s, e, debug=False):
        q = models.TeacherLoginLog.objects.filter(created_at__range=(s, e),
                                                  term=term)
        q = q.values(
            'term_school_year', 'term_type', 'town_name', 'school_name', 
            'grade_name', 'class_name'
        ).annotate(lesson_count=Count('pk'))

        querylist_count = []
        for i in q.iterator():
            ret = models.TeacherLoginCountWeekly(
                town_name=i['town_name'],
                school_name=i['school_name'],
                grade_name=i['grade_name'],
                class_name=i['class_name'],
                week=week,
                term=term,
                lesson_count = i['lesson_count'],
                school_year = i['term_school_year'],
                term_type = i['term_type'],
            )
            querylist_count.append(ret)

        models.TeacherLoginCountWeekly.objects.bulk_create(querylist_count)
            #term = models.Term.objects.get(uuid=i['term'])
            #func = models.TeacherLoginCountWeekly.objects.get_or_create
            #obj, c = func(town_name=i['town_name'], school_name=i['school_name'],
            #              term=term, grade_name=i['grade_name'],
            #              class_name=i['class_name'], week=week)
            #if obj.lesson_count != i['lesson_count']:
            #    if DEBUG or debug:
            #        print 'lesson_count changed:%s -> %s' % (obj.lesson_count, i['lesson_count'])
            #    obj.lesson_count = i['lesson_count']
            #    obj.save()
            # if DEBUG or debug:
            #     print 'lesson_count:', week, i['lesson_count']

    def calculate_weekly_time(self, term, week, s, e, debug=False):
        q = models.TeacherLoginTime.objects.all()
        q = q.filter(teacherloginlog__created_at__range=(s, e),
                     teacherloginlog__term=term)
        q = q.values(
            'teacherloginlog__term_school_year',
            'teacherloginlog__term_type',
            'teacherloginlog__town_name',
            'teacherloginlog__school_name',
            'teacherloginlog__term', 'teacherloginlog__grade_name',
            'teacherloginlog__class_name'
        )
        q = q.annotate(total_time=Sum('login_time'))

        querylist_time = []
        for i in q.iterator():
            town_name = i['teacherloginlog__town_name']
            school_name = i['teacherloginlog__school_name']
            #term = models.Term.objects.get(uuid=i['teacherloginlog__term'])
            grade_name = i['teacherloginlog__grade_name']
            class_name = i['teacherloginlog__class_name']

            ret = models.TeacherLoginTimeWeekly(
                town_name=town_name,
                school_name=school_name,
                grade_name=grade_name,
                class_name=class_name,
                week=week,
                term=term,
                total_time = i['total_time'],
                school_year = i['teacherloginlog__term_school_year'],
                term_type = i['teacherloginlog__term_type'],
            )
            querylist_time.append(ret)

        models.TeacherLoginTimeWeekly.objects.bulk_create(querylist_time)
            #func = models.TeacherLoginTimeWeekly.objects.get_or_create
            #obj, c = func(town_name=town_name, school_name=school_name,
            #              term=term, grade_name=grade_name,
            #              class_name=class_name, week=week)
            #if obj.total_time != i['total_time']:
            #    if DEBUG or debug:
            #        print 'total_time   changed:%s -> %s' % (obj.total_time, i['total_time'])
            #    obj.total_time = i['total_time']
            #    obj.save()
            # if DEBUG or debug:
            #     print 'total_time:', week, i['total_time']

    def traverse_weeks(self, term, first_monday, debug=False):
        monday = first_monday
        sunday = first_monday + datetime.timedelta(days=6)
        while monday <= term.end_date:
            s = datetime.datetime.combine(monday, datetime.time.min)
            e = datetime.datetime.combine(sunday, datetime.time.max)
            week = datetimeutil.get_week_number(term, s, e)
            if week < 1:
                continue
            self.calculate_lesson_count(term, week, s, e, debug)
            self.calculate_weekly_time(term, week, s, e, debug)
            monday += datetime.timedelta(days=7)
            sunday += datetime.timedelta(days=7)

    def handle(self, *args, **options):
        '''
            1. 遍历所有学期
            2. 遍历学期的每周
            3. 计算每周汇总
        '''
        cursor = connection.cursor()
        cursor.execute('TRUNCATE TABLE db_teacherlogincountweekly')
        cursor.execute('TRUNCATE TABLE db_teacherlogintimeweekly')

        # 默认当前学年学期
        terms = models.Term.get_current_term_list()

        # 所有学年学期
        if 'update-old-terms' in args:
            lst = terms and map(lambda i: i.pk, terms) or []
            terms = models.Term.objects.all()
        
        # 指定学年学期
        elif args:
            term_uuid , = args
            terms = [models.Term.objects.get(uuid=term_uuid)]

        if 'debug' in args:
            debug = True
        else:
            debug = False

        count = len(terms)
        i = 1
        for term in terms:
            if DEBUG:
                print i, term.school_year, term.term_type, term.school.name
            i += 1
            first_monday = term.start_date - datetime.timedelta(days=term.start_date.weekday())
            self.traverse_weeks(term, first_monday, debug)

def run_by_http(request):
    from django.http import HttpResponse
    cmd = Command()
    cmd.handle()
    return HttpResponse('操作成功,<a href="/">返回</a>')
