#!/usr/bin/env python
# coding=utf-8
from django.core.management.base import BaseCommand

from BanBanTong.db import models


class Command(BaseCommand):
    '''
        查看某个学校某学期的mac绑定
    '''

    def handle(self, *args, **options):
        #school = models.Group.objects.get(name='硒都民族实验小学', group_type='school')
        school = models.Group.objects.get(name='穿洞小学', group_type='school')
        print school
        term = models.Term.objects.get(school=school, school_year='2013-2014', term_type='春季学期')
        print term
        grades = models.Grade.objects.filter(term=term).order_by('number')
        print grades
        for grade in grades:
            classes = models.Class.objects.filter(grade=grade).order_by('name')
            for c in classes:
                macs = models.ClassMacV2.objects.filter(class_uuid=c)
                if macs:
                    for mac in macs:
                        print grade.name, c.name, mac.mac
                else:
                    print grade.name, c.name, 'N'
