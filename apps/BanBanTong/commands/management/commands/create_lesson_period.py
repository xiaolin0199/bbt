# coding: utf-8
import datetime
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from BanBanTong.db import models


class Command(BaseCommand):

    @staticmethod
    def create_lesson_period(start_time, end_time, lesson_time, rest_time, exclude):
        begin = parse_datetime(start_time)
        endtime = parse_datetime(end_time)
        terms = models.Term.get_current_term_list()
        models.LessonPeriod.objects.filter(term__in=terms).delete()
        n = 0
        while begin < endtime:
            if begin.hour in exclude:
                end = (begin + datetime.timedelta(minutes=lesson_time))
                begin = end + datetime.timedelta(minutes=rest_time)
                continue
            n += 1
            end = (begin + datetime.timedelta(minutes=lesson_time))
            o, is_new = models.LessonPeriod.objects.get_or_create(
                term=terms[0],
                sequence=n,
                defaults={
                    'start_time': begin.time(),
                    'end_time': end.time(),
                }
            )
            if not is_new:
                o.start_time = begin.time()
                o.end_time = end.time()
                o.save()
            print 'create %3d %s %s' % (o.sequence, o.start_time, o.end_time)
            begin = end + datetime.timedelta(minutes=rest_time)


    def handle(self, *args, **kwargs):
        print u'该脚本用于创建默认的节次信息'
        print u'例如,9:00到17:00属于上课时间,每节课45分钟,休息10分钟',
        print u'午间休息时间从12:00 到14:00(12和13后属于休息时间)'
        print u'那么参数输入如下: 9 17 45 10 12 13',
        print u'默认创建9到19点(12到13点休息)间的4分钟课时,1分钟休息的节次信息'
        print u'自己计算让时间落在整点时间段上,程序上不作限定'

        x = raw_input('please in put')
        if not x:
            x = '9 19 4 1 12 13'
        args = x.split(' ')
        start_time = '2015-02-09 %s:00:00' % args[0].zfill(2)
        end_time = '2015-02-09 %s:00:00' % args[1].zfill(2)
        lesson_time = int(args[2])
        rest_time = int(args[3])
        exclude = [int(i) for i in args[4:]]

        Command.create_lesson_period(start_time, end_time, lesson_time, rest_time, exclude)

