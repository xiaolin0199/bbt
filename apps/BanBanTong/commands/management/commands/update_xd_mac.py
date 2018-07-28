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
        old = {}  # 年级，班级，mac
        school = models.Group.objects.get(name='硒都民族实验小学', group_type='school')
        term = models.Term.objects.get(school=school, school_year='2013-2014', term_type='春季学期')
        grades = models.Grade.objects.filter(term=term)
        for g in grades:
            old[g.name] = {}
            classes = models.Class.objects.filter(grade=g)
            for c in classes:
                macs = models.ClassMacV2.objects.filter(class_uuid=c)
                if macs:
                    m = str(macs[0].mac)
                else:
                    m = u''
                old[g.name][c.name] = m
                # old.append([g.name,c.name,m])

        # 处理2014-2015秋季
        try:
            term = models.Term.objects.get(school=school, school_year='2014-2015', term_type='秋季学期')
        except:
            term = None
        if term:
            grades = models.Grade.objects.filter(term=term)
            for g in grades:
                print g.name
                classes = models.Class.objects.filter(grade=g)
                for c in classes:
                    print c.name
                    macs = models.ClassMacV2.objects.filter(class_uuid=c)
                    for mac in macs:
                        m = mac.mac
                        # print old[g.name][str(c.name)]
                        try:
                            old_m = old[g.name][c.name]
                        except:
                            continue
                        if old_m != m:
                            mac.mac = old_m
                            mac.save()

        # 处理2014-2015春季
        try:
            term = models.Term.objects.get(school=school, school_year='2014-2015', term_type='春季学期')
        except:
            term = None
        if term:
            grades = models.Grade.objects.filter(term=term)
            for g in grades:
                classes = models.Class.objects.filter(grade=g)
                for c in classes:
                    macs = models.ClassMacV2.objects.filter(class_uuid=c)
                    for mac in macs:
                        m = mac.mac
                        # print old[g.name][str(c.name)]
                        try:
                            old_m = old[g.name][c.name]
                        except:
                            continue
                        if old_m != m:
                            mac.mac = old_m
                            mac.save()
