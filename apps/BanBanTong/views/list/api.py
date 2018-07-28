#!/usr/bin/env python
# coding=utf-8
from BanBanTong.db import models
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import datetimeutil
from BanBanTong.utils import model_list_to_dict


def get_grade_class(request):
    ret = datetimeutil.get_term_from_date_range(request)
    computerclass_need = request.GET.get('computerclass_need', False)
    only_computerclass = request.GET.get('only_computerclass', False)
    if isinstance(ret, (str, unicode)):
        return create_failure_dict(msg=ret)
    grades = models.Grade.objects.filter(term=ret)
    if only_computerclass == 'true':  # 仅需要电脑教室的联动信息
        grades = grades.filter(number=13)
    elif computerclass_need != 'true':  # 仅需要普通年级班级的联动信息
        grades = grades.exclude(number=13)

    classes = models.Class.objects.filter(grade__in=grades)
    data = {'grade': model_list_to_dict(grades.values('uuid', 'name')),
            'class': model_list_to_dict(classes.values('uuid', 'name', 'grade'))}
    return create_success_dict(data=data)


def get_lesson_name(request):
    ret = datetimeutil.get_term_from_date_range(request)
    if isinstance(ret, (str, unicode)):
        return create_failure_dict(msg=ret)
    q = models.LessonSchedule.objects.filter(class_uuid__grade__term=ret)
    q = q.values_list('lesson_name__name', flat=True)
    if not q.exists():
        q = models.LessonName.objects.filter(school=ret.school)
        q = q.values_list('name', flat=True)
    records = [{'name': i} for i in set(q)]
    return create_success_dict(data={'lesson_name': records})


def get_lesson_period(request):
    ret = datetimeutil.get_term_from_date_range(request)
    if isinstance(ret, (str, unicode)):
        return create_failure_dict(msg=ret)
    q = models.LessonPeriod.objects.filter(term=ret)
    q = q.values('uuid', 'sequence')
    return create_success_dict(data={'lesson_period': model_list_to_dict(q)})
