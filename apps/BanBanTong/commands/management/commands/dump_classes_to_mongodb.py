#!/usr/bin/env python
# coding=utf-8
from django.core.management.base import BaseCommand
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.utils import mongo


class Command(BaseCommand):
    '''
        把Class的数据从MySQL导入到MongoDB的classes
        {province_name: xx, city_name: xx, country_name: xx, town_name: xx,
        school_name: xx, school_year: xx, term_type: xx, term_start_date: xx,
        term_end_date: xx, grade_name: xx, class_name: xx}
    '''

    def handle(self, *args, **options):
        if not constants.BANBANTONG_USE_MONGODB:
            print 'not using mongodb'
            return

        q = models.Class.objects.all()
        print q.count()
        i = 0
        for obj in q:
            i += 1
            mongo.save_class(obj)
            if i % 100 == 0:
                print 'Class', i
