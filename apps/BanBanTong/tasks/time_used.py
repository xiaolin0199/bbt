# coding=utf-8
import datetime
import logging
from BanBanTong.db import models


logger = logging.getLogger(__name__)


class Task(object):
    '''
        如果当前时间是下课期间，就把之前的TeacherLoginTimeTemp记录结转掉
    '''
    # 注:
    # 这里在BanBanTong.utils.format_record.activity_logged_in_new.__fix_task
    # 中有一部分对该定时任务的补充
    # 此处修改的时候注意留意一下

    run_period = 60

    # 处理所有TeacherLoginTimeTemp
    def save_teacherlogintime(self):
        now = datetime.datetime.now()
        objs = models.TeacherLoginTimeTemp.objects.all()
        objs = objs.filter(teacherloginlog__lesson_period_end_time__lt=now.time())
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
                tl.save()

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

    def __init__(self):
        if models.Setting.getvalue('server_type') != 'school':
            return
        if models.Setting.getvalue('installed') != 'True':
            return
        self.save_teacherlogintime()
