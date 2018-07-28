# coding=utf-8
import logging
from BanBanTong.db import models
from django.conf import settings
DEBUG = settings.DEBUG
del settings


class Task(object):
    '''
        计算G表的教师已授课时
    '''
    if DEBUG:
        run_period = 60 * 5
    else:
        run_period = 60 * 60
    logger = logging.getLogger(__name__)

    def calculate_finished_time(self, term, lt):
        q = models.TeacherLoginLog.objects.all()
        q = q.filter(term=term, teacher=lt.teacher,
                     class_uuid__grade__name=lt.class_uuid.grade.name,
                     class_uuid__name=lt.class_uuid.name,
                     lesson_name=lt.lesson_name.name)
        n = q.count()
        if n != lt.finished_time:
            lt.finished_time = n
            lt.save(force_update=True)

    def __init__(self):
        if models.Setting.getvalue('server_type') not in ('school', 'country'):
            return
        # 遍历LessonTeacher
        terms = models.Term.get_current_term_list()
        if len(terms) == 0:
            return
        q = models.LessonTeacher.objects.all()
        for term in terms:
            q1 = q.filter(class_uuid__grade__term=term)
            for i in q1:
                self.calculate_finished_time(term, i)
