# coding=utf-8
import time
import datetime
from django.core.management.base import BaseCommand
from BanBanTong.db import models


class Command(BaseCommand):
    def handle(self, *args, **options):
        if args:
            term_uuid, = args
            term = models.Term.objects.get(uuid=term_uuid)
            n = 0
            start_date = datetime.datetime.now()
            print 'start: ' , start_date

            province = models.Group.objects.get(group_type='province')
            city = models.Group.objects.get(group_type='city')
            country = models.Group.objects.get(group_type='country')
            if term:
                school = term.school
                town = school.parent
                # 初始化province , city  , country , town , school
                o_province = models.Statistic.create_one_item(term, province)
                o_city = models.Statistic.create_one_item(term, city, o_province)
                o_country = models.Statistic.create_one_item(term, country, o_city)
                o_town = models.Statistic.create_one_item(term, town, o_country)
                o_school = models.Statistic.create_one_item(term, school, o_town)

                # 初始化年级
                grades = models.Grade.objects.filter(term=term, term__school=school)
                for grade in grades:
                    o_grade = models.Statistic.create_one_item(term, grade, o_school)
                    # 初始化班级
                    classes = models.Class.objects.filter(grade__term=term, grade=grade)
                    for c in classes:
                        o_class = models.Statistic.create_one_item(term, c, o_grade)
                        # 初始化课程
                        lessones = models.LessonName.objects.filter(school=school)
                        for lesson in lessones:
                            o_lesson = models.Statistic.create_one_item(term, lesson, o_class)


            print 'finished: ' , datetime.datetime.now() - start_date

        else:
            models.Statistic.init_all()
            models.Statistic.update_all()
            return


def run_by_http(request):
    from django.http import HttpResponse
    cmd = Command()
    cmd.handle()
    return HttpResponse('综合分析数据库初始化成功,<a href="/">返回</a>')