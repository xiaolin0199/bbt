# coding=utf-8
import logging
import datetime
import traceback
from django.core.management.base import BaseCommand

from BanBanTong.db import models


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''
        重新计算登录日志中的使用时长
    '''

    def handle(self, *args, **options):
        if models.Setting.getvalue('installed') != 'True':
            return
        now = datetime.datetime.now()
        objs = models.TeacherLoginTimeTemp.objects.all()
        # objs = objs.filter(teacherloginlog__lesson_period_end_time__lt=now.time())
        for i in objs:
            tl = i.teacherloginlog
            # 每节课的最大上课时间(秒) 结束TIME - 登录时间TIME
            s = datetime.datetime.combine(now.date(), tl.lesson_period_start_time)
            e = datetime.datetime.combine(now.date(), tl.lesson_period_end_time)
            seconds = (e - s).total_seconds()
            # 如果我们的计算时间大于每节课的最大上课时间，则保存设定的最大上课时间
            login_time = i.login_time if i.login_time < seconds else seconds
            # teacherloginlog中的login_time字段保存
            if hasattr(tl, 'login_time'):
                tl.login_time = login_time
                try:
                    tl.save()
                except Exception as e:
                    traceback.print_exc()

            # teacherlogintime中的login_time字段保存
            obj = models.TeacherLoginTime(teacherloginlog=tl,
                                          login_time=login_time)
            try:
                obj.save()  # 这个流程里面有些鬼会引起异常
            except:
                logger.exception('')
                pass
            finally:
                if models.TeacherLoginTime.objects.filter(teacherloginlog=tl).exists():
                    i.delete()
