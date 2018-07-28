#!/usr/bin/env python
# coding=utf-8
import datetime
import hashlib
import math
import random
import MySQLdb
import traceback

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import F

from BanBanTong.db import models
from BanBanTong.utils.str_util import generate_node_key


class Command(BaseCommand):

    def run(self):
        nodes = models.Node.objects.all()
        all_node = nodes.values_list('communicate_key', flat=True)
        for node in nodes:
            print '%s start' % node.name
            while True:
                new_communicate_key = generate_node_key()
                if new_communicate_key not in all_node:
                    break
            print 'old key: %s , new key: %s' % (node.communicate_key, new_communicate_key)

            node.communicate_key = new_communicate_key
            node.save()

    def handle(self, *args, **options):
        cursor = connection.cursor()
        cursor.execute('SET unique_checks=0')
        cursor.execute('SET foreign_key_checks=0')

        self.run()

        cursor.execute('SET unique_checks=1')
        cursor.execute('SET foreign_key_checks=1')
