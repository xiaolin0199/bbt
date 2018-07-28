#!/usr/bin/env python
# coding=utf-8
from django.core.management.base import BaseCommand
from BanBanTong.utils import task_scheduler


class Command(BaseCommand):
    '''
        启动BanBanTong.tasks定时任务
    '''

    def handle(self, *args, **options):
        task_scheduler.start()
