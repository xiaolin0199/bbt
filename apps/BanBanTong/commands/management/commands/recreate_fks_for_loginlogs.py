# coding=utf-8
from django.core.management.base import BaseCommand
from django.db.models import Q
from BanBanTong.db import models

class Command(BaseCommand):
    def handle(self, *args, **options):
        cond = Q(school__isnull=True)
        cond |= Q(grade__isnull=True)
        cond |= Q(class_uuid__isnull=True)
        cond |= Q(lesson_teacher__isnull=True)
        objs = models.TeacherLoginLog.objects.filter(cond)
        print objs.count(), 'items need to fix'
            
        n = 0
        for o in objs:
            try:
                c = models.Class.objects.get(
                    grade__term=o.term,
                    name=o.class_name, 
                    grade__name=o.grade_name
                )
            except:
                n += 1
                print 'class has been deleted:', o.school_name, o.grade_name, o.class_name
                continue
            
            print 'fix:',
            if not o.school:
                print ' s',
                o.school = c.grade.term.school
            if not o.grade:
                print ' g',
                o.grade = c.grade
            if not o.class_uuid:
                print ' c',
                o.class_uuid = c
            if not o.lesson_teacher:
                print ' lt',
                try:
                    lt = c.lessonteacher_set.get(
                        teacher__name=o.teacher_name,
                        lesson_name__name=o.lesson_name
                    )
                    o.lesson_teacher = lt
                    print 'ok',
                except:
                    print 'lt failure',
                    pass
            print
            o.save()

def run_by_http(request):
    from django.http import HttpResponse
    cmd = Command()
    cmd.handle()
    return HttpResponse('重建登录日志的外键完成,<a href="/">返回</a>')