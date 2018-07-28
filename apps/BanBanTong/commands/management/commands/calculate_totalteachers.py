#coding=utf-8
import logging
from django.core.management.base import BaseCommand
from BanBanTong.db import models


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''
        清空所有TotalTeachers*表，重新计算
    '''

    def calculate_country(self, server_type, terms):
        if server_type not in ('city', ):
            return
        models.TotalTeachersCountry.objects.filter(term__in=terms).delete()
        for term in terms:
            q = models.LessonTeacher.objects.all()
            q = q.filter(class_uuid__grade__term=term)
            q = q.values('teacher').distinct()
            count = q.count()
            if count == 0:
                continue
            models.TotalTeachersCountry(country_name=term.school.parent.parent.name,
                                        term=term, total=count).save()
            #print term.school.parent.parent.name, term.school_year, term.term_type, count

    def calculate_town(self, server_type, terms):
        if server_type not in ('city', 'country'):
            return
        models.TotalTeachersTown.objects.filter(term__in=terms).delete()
        for term in terms:
            q = models.LessonTeacher.objects.all()
            q = q.filter(class_uuid__grade__term=term)
            q = q.values('teacher').distinct()
            count = q.count()
            if count == 0:
                continue
            models.TotalTeachersTown(country_name=term.school.parent.parent.name,
                                     town_name=term.school.parent.name,
                                     term=term, total=count).save()
            #print term.school.parent.name, term.school_year, term.term_type, count

    def calculate_school(self, server_type, terms):
        if server_type not in ('city', 'country'):
            return
        models.TotalTeachersSchool.objects.filter(term__in=terms).delete()
        for term in terms:
            q = models.LessonTeacher.objects.all()
            q = q.filter(class_uuid__grade__term=term)
            q = q.values('teacher').distinct()
            count = q.count()
            if count == 0:
                continue
            models.TotalTeachersSchool(country_name=term.school.parent.parent.name,
                                       town_name=term.school.parent.name,
                                       school_name=term.school.name,
                                       term=term, total=count).save()
            #print term.school.name, term.school_year, term.term_type, count

    def calculate_lesson(self, server_type, terms):
        if server_type not in ('city', 'country', 'school'):
            return
        models.TotalTeachersLesson.objects.filter(term__in=terms).delete()
        for term in terms:
            lesson_names = models.LessonName.objects.filter(school=term.school)
            for l in lesson_names:
                q = models.LessonTeacher.objects.all()
                q = q.filter(class_uuid__grade__term=term, lesson_name=l)
                q = q.values('teacher').distinct()
                count = q.count()
                if count == 0:
                    continue
                models.TotalTeachersLesson(country_name=term.school.parent.parent.name,
                                           town_name=term.school.parent.name,
                                           school_name=term.school.name,
                                           lesson_name=l.name,
                                           term=term, total=count).save()
                #print term.school.name, l.name, term.school_year, term.term_type, count

    def calculate_grade(self, server_type, terms):
        if server_type not in ('city', 'country', 'school'):
            return
        models.TotalTeachersGrade.objects.filter(term__in=terms).delete()
        for term in terms:
            grades = models.Grade.objects.filter(term=term)
            for g in grades:
                q = models.LessonTeacher.objects.all()
                q = q.filter(class_uuid__grade=g)
                q = q.values('teacher').distinct()
                count = q.count()
                if count == 0:
                    continue
                models.TotalTeachersGrade(country_name=term.school.parent.parent.name,
                                          town_name=term.school.parent.name,
                                          school_name=term.school.name,
                                          grade_name=g.name,
                                          term=term, total=count).save()
                #print term.school.name, g.name, term.school_year, term.term_type, count

    def calculate_lessongrade(self, server_type, terms):
        if server_type not in ('school', ):
            return
        models.TotalTeachersLessonGrade.objects.filter(term__in=terms).delete()
        for term in terms:
            lesson_names = models.LessonName.objects.filter(school=term.school)
            for l in lesson_names:
                grades = models.Grade.objects.filter(term=term)
                for g in grades:
                    q = models.LessonTeacher.objects.all()
                    q = q.filter(class_uuid__grade=g, lesson_name=l)
                    q = q.values('teacher').distinct()
                    count = q.count()
                    if count == 0:
                        continue
                    models.TotalTeachersLessonGrade(town_name=term.school.parent.name,
                                                    school_name=term.school.name,
                                                    lesson_name=l.name,
                                                    grade_name=g.name,
                                                    term=term, total=count).save()
                    #print term.school.name, l.name, g.name, term.school_year, term.term_type, count

    def handle(self, *args, **options):

        server_type = models.Setting.getvalue('server_type')
        terms = models.Term.get_current_term_list() # 默认当前学年学期
        if args:
            if 'update-old-terms' in args: # 所有学年学期
                lst = terms and map(lambda i: i.pk, terms) or []
                terms = models.Term.objects.exclude(pk__in=lst)
            else: # 指定学年学期
                term_uuid , = args
                terms = [models.Term.objects.get(uuid=term_uuid)]

        self.calculate_country(server_type, terms)
        self.calculate_town(server_type, terms)
        self.calculate_school(server_type, terms)
        self.calculate_lesson(server_type, terms)
        self.calculate_grade(server_type, terms)
        self.calculate_lessongrade(server_type, terms)


def calculate_totalteachers(update_type='current-terms'):
    obj = Command()
    obj.handle(update_type)