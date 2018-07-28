# coding=utf-8
import datetime
import logging
from django.db import connections
from django.utils.dateparse import parse_datetime
from BanBanTong import constants
from BanBanTong.db import models


class Task(object):
    run_period = 10 * 60
    logger = logging.getLogger(__name__)

    def __init__(self):
        if not constants.BANBANTONG_DB_AUTO_OPTIMIZE:
            return
        now = datetime.datetime.now()
        if now.hour != 0:
            return

        start = False
        try:
            obj = models.Setting.objects.get(name='last_optimize_time')
            last_datetime = parse_datetime(obj.value)
            delta = now - last_datetime
            if delta.days >= constants.BANBANTONG_DB_AUTO_OPTIMIZE_PERIOD:
                start = True
        except:
            obj = models.Setting(name='last_optimize_time')
            start = True
        if start:
            cursor = connections['default'].cursor()
            tables = ['AssetLog', 'AssetRepairLog', 'LessonSchedule',
                      'SyncLog', 'TeacherAbsentLog', 'TeacherLoginLog']
            for table in tables:
                self.logger.debug('optimize table %s %s', table,
                                  cursor.execute('OPTIMIZE TABLE %s;' % table))

            obj.value = str(now)
            obj.save()
