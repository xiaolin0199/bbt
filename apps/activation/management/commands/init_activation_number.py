#coding=utf-8
from django.core.management.base import BaseCommand
from django.db import connection
from BanBanTong.db import models


class Command(BaseCommand):

    def handle(self, *args, **options):
        N = 0
        server_type = models.Setting.getvalue('server_type')
        if server_type != 'country':
            print u'仅县级服务器可用'
            return

        objs = models.Node.objects.all()
        term = o = models.NewTerm.objects.all().order_by('-start_date')
        term = term.exists() and term[0] or None
        if not term:
            print u'无可用学年学期'
            return

        print u'节点总数:', objs.count()
        for o in objs:
            try:
                s = models.Group.objects.get(
                    group_type='school',
                    name=o.name
                )
            except:
                continue

            terms = s.term_set.filter(
                school_year=term.school_year,
                term_type=term.term_type
            )

            cls = models.Class.objects.filter(grade__term__in=terms)
            o.activation_number = cls.count()
            o.save()
            N += 1

        print u'初始化完成,影响条目数:', N
