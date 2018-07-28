#!/usr/bin/env python
# coding=utf-8
import apscheduler.schedulers
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger

import importlib
import logging
import traceback
import BanBanTong.tasks
from django.conf import settings
DEBUG = settings.DEBUG
del settings

logger = logging.getLogger(__name__)

jobstores = {'default': MemoryJobStore()}
executors = {'default': ThreadPoolExecutor(16)}
scheduler = BlockingScheduler(jobstores=jobstores,
                              executors=executors)


def add_job(cls):
    '''
        1. run_period  每隔多少时间运行
        2. run_date 设定固定日期运行
        3. cron_date 自定义设置日期循环运行
           def __init__(self, year=None, month=None, day=None, week=None, day_of_week=None, hour=None, minute=None,second=None, start_date=None, end_date=None, timezone=None)
           :param int|str year: 4-digit year
           :param int|str month: month (1-12)
           :param int|str day: day of the (1-31)
           :param int|str week: ISO week (1-53)
           :param int|str day_of_week: number or name of weekday (0-6 or mon,tue,wed,thu,fri,sat,sun)
           :param int|str hour: hour (0-23)
           :param int|str minute: minute (0-59)
           :param int|str second: second (0-59)
           :param datetime|str start_date: earliest possible date/time to trigger on (inclusive)
           :param datetime|str end_date: latest possible date/time to trigger on (inclusive)
           :param datetime.tzinfo|str timezone: time zone to use for the date/time calculations
                                                (defaults to scheduler timezone)
    '''
    global scheduler

    if hasattr(cls, 'run_period'):
        t = IntervalTrigger(seconds=cls.run_period)
    elif hasattr(cls, 'run_date'):
        t = DateTrigger(run_date=cls.run_date)
    elif hasattr(cls, 'cron_date'):
        year = cls.year if hasattr(cls, 'year') else None
        month = cls.month if hasattr(cls, 'month') else None
        day = cls.day if hasattr(cls, 'day') else None
        week = cls.week if hasattr(cls, 'week') else None
        day_of_week = cls.day_of_week if hasattr(cls, 'day_of_week') else None
        hour = cls.hour if hasattr(cls, 'hour') else None
        minute = cls.minute if hasattr(cls, 'minute') else None
        second = cls.second if hasattr(cls, 'second') else None
        start_date = cls.start_date if hasattr(cls, 'start_date') else None
        end_date = cls.end_date if hasattr(cls, 'end_date') else None
        timezone = cls.timezone if hasattr(cls, 'timezone') else None

        t = CronTrigger(year=year, month=month, day=day, week=week, day_of_week=day_of_week, hour=hour,
                        minute=minute, second=second, start_date=start_date, end_date=end_date, timezone=timezone)
    else:
        return None

    scheduler.add_job(cls, trigger=t)


def start():
    global scheduler
    print 'start tasks'
    for name in BanBanTong.tasks.__all__:
        m = importlib.import_module('BanBanTong.tasks.' + name)
        if DEBUG:
            logger.debug('add task: %s' % name)
        cls = getattr(m, 'Task')
        add_job(cls)
    try:
        logger.debug('scheduler.start')
        scheduler.start()
        logger.debug('scheduler.start OK')
    except apscheduler.schedulers.SchedulerAlreadyRunningError:
        print 'tasks already running'
        return
    except KeyboardInterrupt:
        print 'interrupted'
        return
    except:
        traceback.print_exc()
        logger.exception('')
