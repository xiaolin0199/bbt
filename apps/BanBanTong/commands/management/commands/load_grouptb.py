#!/usr/bin/env python
# coding=utf-8
import MySQLdb
import traceback
from django.core.management.base import BaseCommand
from BanBanTong.db import models


class Command(BaseCommand):
    '''
        从GroupTB数据库载入最新的GroupTB数据
    '''

    def handle(self, *args, **options):
        try:
            conn = MySQLdb.connect(host='10.10.10.102', port=3306,
                                   user='root', passwd='oseasy',
                                   db='grouptb', charset='utf8')
            cursor = conn.cursor()
        except:
            traceback.print_exc()
            return
        sql = """SELECT group_id, name, parent_id FROM db_groupinfo"""
        cursor.execute(sql)
        res = cursor.fetchall()
        group_ids = []
        for row in res:
            group_ids.append(row[0])
            if row[2]:
                parent = models.GroupTB.objects.get(group_id=row[2])
            else:
                parent = None
            try:
                obj = models.GroupTB.objects.get(group_id=row[0])
                modified = False
                if obj.name != row[1]:
                    modified = True
                    obj.name = row[1]
                if obj.parent != parent:
                    modified = True
                    obj.parent = parent
                if modified:
                    obj.save()
                    print 'modify', row[0], row[1]
            except:
                models.GroupTB(group_id=row[0], name=row[1], parent=parent).save()
                print 'add', row[0], row[1]
        q = models.GroupTB.objects.all().exclude(group_id__in=group_ids)
        print q.count()
        print q.values_list('name', flat=True)
        q.delete()
