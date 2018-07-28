# coding=utf-8
import datetime
import logging
import socket
import cPickle as pickle
from BanBanTong.db import models


# 每隔1分钟检查一下远程定时关机功能是否开始工作
class Task(object):
    run_period = 1 * 60

    #cron_date = True
    #hour = '15'
    #minute = '30,33,35'

    logger = logging.getLogger(__name__)

    def run(self):
        switch = models.Setting.getvalue('scheduler_shutdown_switch')
        if switch is None or switch == '0':
            # 没有开启定时远程关机
            return
        else:
            # 关机时间
            next_run = models.Setting.getvalue('scheduler_shutdown_next_run')
            next_run = datetime.datetime.strptime(next_run, '%Y-%m-%d %H:%M:%S')
            # 当前时间
            now = datetime.datetime.now()
            if next_run > now:  # 未到关机时间
                return
            else:
                seconds = (now - next_run).seconds
                # 在合理范围内 (0 ~ 300 s)都执行
                if seconds >= 0 and seconds <= 300:
                    # 关机是否延时
                    delay = models.Setting.getvalue('scheduler_shutdown_delay')
                    # 获取所有的本学年学期已申报客户端(包括电脑教室) mac 集合
                    try:
                        school = models.Group.objects.get(group_type='school')
                    except:
                        return
                    try:
                        term = models.Term.get_current_term_list(school)[0]
                    except:
                        return
                    macfilter = models.ClassMacV2.objects.filter(class_uuid__grade__term=term).values_list('mac', flat=True)
                    # PUB shutdown msg to zmq
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect(('127.0.0.1', 9528))

                    # time.sleep(2)
                    msg = 'shutdown###%s###%s' % (delay, pickle.dumps(macfilter))
                    sock.send(msg)

                # 不管执行完成还是不执行,都将next_run改为第二天
                obj = models.Setting.objects.get(name='scheduler_shutdown_next_run')
                next_run += datetime.timedelta(days=1)
                obj.value = next_run
                obj.save()

    def __init__(self):
        if models.Setting.getvalue('server_type') != 'school':
            return

        if models.Setting.getvalue('installed') != 'True':
            return
        self.run()
