# coding=utf-8
import json
import logging
import base64
import urllib2
import urllib
from django.core import serializers
from BanBanTong.db import models
from activation.serverside import update_activate_info
import traceback
from BanBanTong.utils import str_util
from django.conf import settings
DEBUG = settings.DEBUG
del settings


class Task(object):
    '''校级服务器从县级获取学期课程资源设置'''
    run_period = 10
    logger = logging.getLogger(__name__)

    def _save_term(self, school, records):
        newterms = serializers.deserialize('json', records)
        old_terms_uuid = list(models.Term.objects.all().values_list('uuid', flat=True))

        for newterm in newterms:
            newterm = newterm.object
            # 校Term表中所有该学年该学期的纪录,历史原因，有些学校有重复的term纪录
            terms = models.Term.objects.filter(school_year=newterm.school_year,
                                               term_type=newterm.term_type)
            if terms:
                for term in terms:
                    # 修改成跟newterm一样
                    if term.start_date != newterm.start_date or term.end_date != newterm.end_date \
                            or term.deleted != newterm.deleted \
                            or term.schedule_time != newterm.schedule_time:

                        term.start_date = newterm.start_date
                        term.end_date = newterm.end_date
                        term.deleted = newterm.deleted
                        term.schedule_time = newterm.schedule_time
                        term.save()
                    old_terms_uuid.remove(term.uuid)

            else:
                term = models.Term(school_year=newterm.school_year,
                                   term_type=newterm.term_type,
                                   start_date=newterm.start_date,
                                   end_date=newterm.end_date,
                                   school=school,
                                   deleted=newterm.deleted,
                                   schedule_time=newterm.schedule_time)
                term.save()

        if old_terms_uuid:
            # models.Term.objects.filter(uuid__in=old_terms_uuid).delete()
            models.Term.objects.filter(uuid__in=old_terms_uuid).update(deleted=True)

    def _save_lesson(self, school, records):  # records: [{'name': '', 'deleted': False,
        #            'types': '初中,小学']}, {...}]
        old_lessons_uuid = list(models.LessonName.objects.all().values_list('uuid', flat=True))
        for record in records:
            try:
                lesson = models.LessonName.objects.get(name=record['name'])
                if lesson.deleted != record['deleted'] \
                        or lesson.types != record['types']:
                    lesson.deleted = record['deleted']
                    lesson.types = record['types']
                    lesson.save()
                old_lessons_uuid.remove(lesson.uuid)
            except:
                lesson = models.LessonName(school=school,
                                           name=record['name'],
                                           deleted=record['deleted'],
                                           types=record['types'])
                lesson.save()

        if old_lessons_uuid:
            # models.LessonName.objects.filter(uuid__in=old_lessons_uuid).delete()
            models.LessonName.objects.filter(uuid__in=old_lessons_uuid).update(deleted=True)

    def _save_resourcefrom(self, values):
        records = serializers.deserialize('json', values)
        old_froms_uuid = list(models.ResourceFrom.objects.all().values_list('uuid', flat=True))

        for record in records:
            record = record.object
            try:
                obj = models.ResourceFrom.objects.get(value=record.value)
                if obj.value != record.value or obj.remark != record.remark:
                    obj.value = record.value
                    obj.remark = record.remark
                    obj.save()
                old_froms_uuid.remove(obj.uuid)
            except:
                record.save()

        if old_froms_uuid:
            models.ResourceFrom.objects.filter(uuid__in=old_froms_uuid).delete()

    def _save_resourcetype(self, values):
        records = serializers.deserialize('json', values)
        old_types_uuid = list(models.ResourceType.objects.all().values_list('uuid', flat=True))

        for record in records:
            record = record.object
            try:
                #obj = models.ResourceType.objects.get(uuid=record.uuid)
                obj = models.ResourceType.objects.get(value=record.value)
                if obj.value != record.value or obj.remark != record.remark:
                    obj.value = record.value
                    obj.remark = record.remark
                    obj.save()
                old_types_uuid.remove(obj.uuid)
            except:
                record.save()

        if old_types_uuid:
            models.ResourceType.objects.filter(uuid__in=old_types_uuid).delete()

    def _update_quota(self, quota):
        if quota:
            communicate_key = models.Setting.getvalue('sync_server_key')
            name = models.Group.objects.filter(group_type='school')[0].name
            try:
                content = base64.b64decode(quota)
                key = '%s-%s' % (communicate_key, name)
                key = base64.b64encode(json.dumps(key))
                d = str_util.decode(content, key=key)
                update_activate_info(d)
            except:
                if DEBUG:
                    traceback.print_exc()
                self.logger.exception('')

    def __init__(self):
        if models.Setting.getvalue('server_type') != 'school':
            return
        if models.Setting.getvalue('installed') != 'True':
            return
        host = models.Setting.getvalue('sync_server_host')
        port = models.Setting.getvalue('sync_server_port')
        if not host or not port:
            return

        url = 'http://%s:%s/api/term-lesson-resource/' % (host, port)
        try:
            key = models.Setting.getvalue('sync_server_key')
            post_data = {'communicate_key': key}
            req = urllib2.Request(url, urllib.urlencode(post_data))
            req.add_header('Content-Type', "application/x-www-form-urlencoded")
            req = urllib2.urlopen(req)
        except:
            if DEBUG:
                traceback.print_exc()
            return
        try:
            ret = req.read()
            req.fp._sock.recv = None
            req.close()
            ret = json.loads(ret)
            if ret['status'] == 'success':
                school = models.Group.objects.get(group_type='school')
                self._save_term(school, ret['data']['term'])
                self._save_lesson(school, ret['data']['lesson'])
                self._save_resourcefrom(ret['data']['resourcefrom'])
                self._save_resourcetype(ret['data']['resourcetype'])
                self._update_quota(ret['data']['quota'])
            else:
                self.logger.debug('%s', ret)
        except:
            if DEBUG:
                traceback.print_exc()
            self.logger.exception('')
