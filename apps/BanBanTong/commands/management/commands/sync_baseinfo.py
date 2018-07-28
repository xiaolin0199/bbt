# coding=utf-8
from django.core.management.base import BaseCommand
from BanBanTong.tasks.sync_baseinfo import Task


class Command(BaseCommand):
    '''
        重新计算G表的教师已授课时 和  授课时长
    '''

    def handle(self, *args, **options):
        Task(force=True)
