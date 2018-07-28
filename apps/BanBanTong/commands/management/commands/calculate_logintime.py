# coding=utf-8
import logging
import traceback
import datetime
from django.core.management.base import BaseCommand
from BanBanTong.db import models
from django.conf import settings
DEBUG = settings.DEBUG
del settings


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''
        重新计算TeacherLoginTime表的教师授课时长
    '''

    def add_arguments(self, parser):
        parser.add_argument('seconds', default=60 * 45, help=u'连接密钥.')

    def calculate(self, obj, *args, **kwargs):
        now = datetime.datetime.now()
        s = datetime.datetime.combine(now.date(), obj.teacherloginlog.lesson_period_start_time)
        e = datetime.datetime.combine(now.date(), obj.teacherloginlog.lesson_period_end_time)
        seconds = (e - s).total_seconds()
        login_time = 0
        try:
            # 查看是否在临时表中存在数据
            q = models.TeacherLoginTimeTemp.objects.get(teacherloginlog=obj)
            login_time = q.login_time
            print 'no TeacherLoginTimeTemp'
        except:
            try:
                # 没有的话,根据登录日志重新计算使用时长
                date = obj.teacherloginlog.created_at.date()
                s = datetime.datetime.combine(date, obj.teacherloginlog.lesson_period_start_time)
                e = datetime.datetime.combine(date, obj.teacherloginlog.lesson_period_end_time)
                if s <= obj.teacherloginlog.created_at <= e:
                    login_time = (e - obj.teacherloginlog.created_at).total_seconds()
            except:
                if DEBUG:
                    traceback.print_exc()
                else:
                    logger.exception('')
                return

        login_time = login_time if login_time <= seconds else seconds
        if login_time > 0:
            obj.login_time = login_time
            obj.save(force_update=True)
            print 'update TeacherLoginTime:', obj.teacherloginlog.term_school_year,
            print obj.teacherloginlog.term_type, obj.teacherloginlog.grade_name,
            print obj.teacherloginlog.class_name, obj.login_time

    def handle(self, *args, **options):
        if models.Setting.getvalue('server_type') not in ('school', 'country'):
            return
        # now = datetime.datetime.now()
        # lp = models.LessonPeriod.objects.all()[0]
        # s = datetime.datetime.combine(now.date(), lp.start_time)
        # e = datetime.datetime.combine(now.date(), lp.end_time)
        # seconds = (e - s).total_seconds()
        seconds = options.get('seconds', 60 * 45)

        term = models.NewTerm.get_current_term()
        if not term:
            print 'no term'
            return
        print term.school_year, term.term_type
        objs = models.TeacherLoginTime.objects.filter(login_time__gt=seconds)
        objs = objs.filter(
            teacherloginlog__term_school_year=term.school_year,
            teacherloginlog__term_type=term.term_type
        )
        if not objs.exists():
            print 'no objs'
        for o in objs:
            self.calculate(o)  # 不添加缓存数据


def fix(seconds=60 * 45):
    o = Command()
    o.handle(seconds=seconds)
