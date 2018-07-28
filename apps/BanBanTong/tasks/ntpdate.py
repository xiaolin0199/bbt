# coding=utf-8
import logging
import ntplib
import os
import platform
import socket
import time
from BanBanTong import constants


class Task(object):
    run_period = 10 * 60
    logger = logging.getLogger(__name__)

    def __init__(self):
        if not constants.BANBANTONG_NTP_CRON:
            return
        try:
            c = ntplib.NTPClient()
            response = c.request('cn.pool.ntp.org')
            ts = response.tx_time
            _date = time.strftime('%Y-%m-%d', time.localtime(ts))
            _time = time.strftime('%X', time.localtime(ts))
            if platform.system() == 'Windows':
                os.system('date {} && time {}'.format(_date, _time))
            elif platform.system() == 'Linux':
                os.system('date -s "%s %s"' % (_date, _time))
        except (socket.gaierror, ntplib.NTPException):
            pass
        except:
            self.logger.exception('')
