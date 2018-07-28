#!/usr/bin/env python
# coding=utf-8
import pypinyin
from django.core.management.base import BaseCommand
from BanBanTong import constants
from BanBanTong.utils import mongo


class Command(BaseCommand):

    def handle(self, *args, **options):
        if not constants.BANBANTONG_USE_MONGODB:
            print 'not using mongodb'
            return
        client = mongo._get_conn()
        if not client:
            print 'failed to get mongodb client'
            return
        table = client.banbantong.classes

        for d in table.find(snapshot=True):
            province_pinyin = ' '.join(pypinyin.lazy_pinyin(d['province_name'], style=pypinyin.TONE2))
            city_pinyin = ' '.join(pypinyin.lazy_pinyin(d['city_name'], style=pypinyin.TONE2))
            country_pinyin = ' '.join(pypinyin.lazy_pinyin(d['country_name'], style=pypinyin.TONE2))
            town_pinyin = ' '.join(pypinyin.lazy_pinyin(d['town_name'], style=pypinyin.TONE2))
            school_pinyin = ' '.join(pypinyin.lazy_pinyin(d['school_name'], style=pypinyin.TONE2))
            table.update({'_id': d['_id']},
                         {'$set': {'province_pinyin': province_pinyin,
                                   'city_pinyin': city_pinyin,
                                   'country_pinyin': country_pinyin,
                                   'town_pinyin': town_pinyin,
                                   'school_pinyin': school_pinyin}})
