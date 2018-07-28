#!/usr/bin/env python
# coding=utf-8
from django.core.management.base import BaseCommand

from BanBanTong.db import models


class Command(BaseCommand):
    '''
        更新硒都民族实验小学的
        2014-2015学年二个学期的MAC
        来源为2013-2014(春季学期)
    '''

    def handle(self, *args, **options):
        school = models.Group.objects.get(name='硒都民族实验小学', group_type='school')

        old = {
            u'一': {u'6': '08-60-6E-67-99-60', u'7': '08-60-6E-6F-0C-5B', u'8': '08-60-6E-6F-08-C4', '9': '08-60-6E-6F-0C-5F', u'10': '08-60-6E-6F-08-CD', u'12': '08-60-6E-53-84-86'},
            u'二': {u'10': '08-60-6E-ED-95-C5'},
            u'三': {u'4': '08-60-6E-80-0A-1B', u'8': '08-60-6E-67-99-6C', u'11': '08-60-6E-80-FC-9A', u'12': '08-60-6E-7F-DF-C2'},
            u'四': {u'1': '08-60-6E-7F-EA-33'},
            u'五': {u'3': '08-60-6E-6F-0C-69', u'4': '08-60-6E-74-40-A6', u'6': '08-60-6E-ED-94-FB'},
            u'六': {u'2': '08-60-6E-6F-09-0C', u'4': '08-60-6E-ED-96-0B'}
        }

        # 处理2014-2015春季
        try:
            term = models.Term.objects.get(school=school, school_year='2014-2015', term_type='春季学期')
        except:
            term = None

        for k1, v1 in old.iteritems():
            g = k1
            # 该学期对应该年级的obj
            try:
                g_obj = models.Grade.objects.get(name=g, term=term)
            except:
                g_obj = None
                print u'年级出错', g
            if g_obj:
                for k2, v2 in v1.iteritems():
                    c = k2
                    m = v2
                    # 该学期对应的该班级obj
                    try:
                        c_obj = models.Class.objects.get(name=c, grade=g_obj)
                    except:
                        c_obj = None
                        print u'班级出错', g, c

                    if c_obj:
                        # 看classmacv2里有没有这个学期这个班级的对应mac,有就替换
                        try:
                            o = models.ClassMacV2.objects.get(class_uuid=c_obj)
                            o.mac = m
                            o.save()
                        except:
                            models.ClassMacV2.objects.create(class_uuid=c_obj, mac=m)

                        print g, c, m, 'success'
