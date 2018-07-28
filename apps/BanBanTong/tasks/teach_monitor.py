# coding=utf-8
import datetime
import logging
from django.utils.dateparse import parse_datetime
from BanBanTong.db import models
from BanBanTong.db.models import TeacherAbsentLog as ta


# 检测上一节课是否有未登录的教师，向TeacherAbsentLog插入一条记录
class Task(object):
    run_period = 5 * 60
    logger = logging.getLogger(__name__)

    # 检查指定时段的课程计划，添加TeacherAbsentLog
    def check_teachlog(self, c, day, checktime, now):
        count = 0
        weekday = day.strftime('%a').lower()
        # 从LessonSchedule找出在checktime之内结束的课程
        if day == checktime.date():
            start_time = checktime.time()
        else:
            start_time = datetime.time()
        if day == now.date():
            end_time = now.time()
        else:
            end_time = datetime.time.max
        # self.logger.debug('TeachMonitorCron: check %s %s %s %s %s',
        #                  c.grade.name, c, day, start_time, end_time)
        q = models.LessonSchedule.objects.all()
        ls = q.filter(class_uuid=c, weekday=weekday,
                      lesson_period__end_time__range=(start_time, end_time))
        # 找出其中没有TeacherLoginLog和TeacherAbsentLog记录的课程
        for i in ls:
            q = models.TeacherLoginLog.objects.all()
            q = q.filter(class_uuid=i.class_uuid,
                         lesson_period=i.lesson_period, weekday=i.weekday,
                         lesson_name=i.lesson_name.name,
                         created_at__year=day.year,
                         created_at__month=day.month,
                         created_at__day=day.day)
            if q.exists():
                # print 'TeachMonitorCron: 已有TeacherLoginLog，跳过'
                continue
            q = models.TeacherAbsentLog.objects.all()
            q = q.filter(class_uuid=i.class_uuid,
                         lesson_period=i.lesson_period, weekday=i.weekday,
                         lesson_name=i.lesson_name.name,
                         created_at__year=day.year,
                         created_at__month=day.month,
                         created_at__day=day.day)
            if q.exists():
                # print 'TeachMonitorCron: 已有TeacherAbsentLog，跳过'
                continue
            # 为找到的LessonSchedule添加一条TeacherAbsentLog记录
            try:
                l = models.LessonTeacher.objects.get(class_uuid=i.class_uuid,
                                                     lesson_name=i.lesson_name)
                end = i.lesson_period.end_time
                created_at = datetime.datetime.combine(day, end)
                ta.log_teacher('absent', teacher=l.teacher,
                               lesson_name=i.lesson_name.name,
                               class_uuid=i.class_uuid,
                               lesson_period=i.lesson_period,
                               created_at=created_at,
                               weekday=i.weekday)
                # print 'TeachMonitorCron: 添加一条TeacherAbsentLog'
                # print l.teacher, i.lesson_name, i.class_uuid, i.lesson_period
                count += 1
            except:
                # print 'TeachMonitorCron: LessonSchedule未安排教师，跳过'
                continue
        return count

    # 遍历所有班级
    def traverse_class(self, term, now):
        q = models.Class.objects.filter(lessonschedule__isnull=False,
                                        grade__term=term).distinct()
        for c in q:
            name = 'absent_checktime_%s' % c.uuid
            obj, flag = models.Setting.objects.get_or_create(name=name)
            checktime = parse_datetime(obj.value)
            if not checktime:
                checktime = datetime.datetime.combine(term.start_date,
                                                      datetime.time())
            count = self.traverse_date_range(c, now, checktime)
            if count > 0:
                obj.value = str(now)
                obj.save()

    # 为某个班级遍历所有日期
    def traverse_date_range(self, c, now, checktime=None):
        start_date = checktime.date()
        r = range((now.date() - start_date).days + 1)
        datelist = [start_date + datetime.timedelta(days=x) for x in r]
        count = 0
        for day in datelist:
            count += self.check_teachlog(c, day, checktime, now)
        return count

    def __init__(self):
        if models.Setting.getvalue('server_type') != 'school':
            return
        if models.Setting.getvalue('installed') != 'True':
            return
        now = datetime.datetime.now()
        try:
            term = models.Term.objects.get(start_date__lte=now,
                                           end_date__gte=now,
                                           deleted=False)
        except:
            self.logger.exception('')
            # print 'TeachMonitorCron: no Term found'
            return
        self.traverse_class(term, now)
