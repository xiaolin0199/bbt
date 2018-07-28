# coding=utf-8
import random
import datetime
from django.core.management.base import BaseCommand
from BanBanTong.db.models import Setting
from django.conf import settings


class Command(BaseCommand):

    def handle(self, *args, **options):
        if settings.DEBUG and settings.ACTIVATE_DIRECTLY:
            now = datetime.datetime.now()
            Setting.setval('activation', {
                'quota': random.randint(100, 300),
                'update_time': now.strftime('%Y-%m-%d %H:%M:%S'),
                'start_date': str((now - datetime.timedelta(1)).date()),
                'end_date': str((now + datetime.timedelta(15)).date()),
            })
            print 'activate success'
