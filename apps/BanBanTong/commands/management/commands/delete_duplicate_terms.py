#!/usr/bin/env python
# coding=utf-8
from django.core.management.base import BaseCommand

from BanBanTong.db import models


class Command(BaseCommand):
    '''
        在恩施县级服务器发现，有些学校的Term会有重复，例如同一个学校的相同学年学期，
        有几条Term记录（当然uuid不一样）。猜测是校级从县级拉取NewTerm设置时有某种问题。
        这个程序就是用来删除县级服务器多余的Term的。
    '''

    def handle(self, *args, **options):
        if models.Setting.getvalue('server_type') != 'country':
            print '只运行在县级服务器上'
            return
        # 1. 找出所有学校
        schools = models.Group.objects.filter(group_type='school')
        # 2. 所有NewTerm（用于查询Term）
        newterms = models.NewTerm.objects.all().order_by('start_date')
        # 3. 对每个学校，找出每个(school_year, term_type)有多个Term记录的
        for school in schools:
            for newterm in newterms:
                terms = models.Term.objects.filter(school=school,
                                                   school_year=newterm.school_year,
                                                   term_type=newterm.term_type)
                count = terms.count()
                print school.name, newterm, count
                if count <= 1:
                    continue
                # 对于有多个重复Term的，找出没有Grade的Term，直接删掉
                for term in terms:
                    if term.grade_set.count() == 0:
                        print '--- delete', school.name, term
                        term.delete()
