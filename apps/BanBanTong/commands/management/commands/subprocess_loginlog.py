#!/usr/bin/env python
# coding=utf-8
import datetime
import hashlib
import math
import random
import uuid
import MySQLdb
import threading
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.db import transaction
from django.utils.dateparse import parse_date
from django.utils.dateparse import parse_time
from BanBanTong.db import models

DEBUG = True


class Command(BaseCommand):

    def handle(self, *args, **options):
        cursor = connection.cursor()
        cursor.execute('SET unique_checks=0')
        cursor.execute('SET foreign_key_checks=0')

        # 获取Term表信息， 进而处理每一个term
        # 比如一个term,就是测试学校001 2013-2014 秋季学期
        start_now = datetime.datetime.now()

        terms = models.Term.objects.all()
        count = 0
        for term in terms:
            count += 1
            print count, term.school_year, term.term_type, term.school.name
            subprocess.call('python manage.py country_test_data_loginlog %s' % term.uuid, shell=True)

        print 'success: ', datetime.datetime.now() - start_now

        cursor.execute('SET unique_checks=1')
        cursor.execute('SET foreign_key_checks=1')
