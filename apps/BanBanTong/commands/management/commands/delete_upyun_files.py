#!/usr/bin/env python
# coding=utf-8
import time
import upyun
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    '''
        清空upyun的制定空间
        命令行: python manage.py delete_upyun_files <group_id>
    '''

    def _delete_upyun_folder(self, up, name):
        res = up.getlist(name)
        for i in res:
            if i['type'] == 'F':
                self._delete_upyun_folder(up, name + i['name'] + '/')
            else:
                up.delete(name + i['name'])
                print name + i['name']
        up.delete(name)

    def handle(self, *args, **options):
        up = upyun.UpYun('oebbt-%s' % args[0], 'oseasy', 'oseasyoseasy', endpoint=upyun.ED_AUTO)
        print up.usage()
        time.sleep(1)
        res = up.getlist('/')
        for i in res:
            if i['type'] != 'F':
                print i
                continue
            self._delete_upyun_folder(up, '/' + i['name'] + '/')
