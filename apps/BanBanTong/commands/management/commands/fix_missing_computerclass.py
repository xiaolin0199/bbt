# coding=utf-8
from django.core.management.base import BaseCommand
from BanBanTong.db import models


class Command(BaseCommand):

    def handle(self, *args, **options):
        objs = models.Class.objects.filter(grade__number=13)
        for obj in objs:
            if not hasattr(obj, 'computerclass'):
                cc, is_new = models.ComputerClass.objects.get_or_create(class_bind_to=obj)
                print u'创建电脑教室', cc
