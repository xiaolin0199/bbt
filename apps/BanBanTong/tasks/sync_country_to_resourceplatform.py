# coding=utf-8
import base64
import bz2
import logging
import requests
from django.core import serializers
import json
from BanBanTong import constants
from BanBanTong.db import models


class Task(object):
    '''县级服务器定期执行，向资源平台推送数据'''
    run_period = 60 * 30
    logger = logging.getLogger(__name__)

    def _sync_data(self, host):
        '''
            每隔一段时间县级服务器调用资源平台接口同步上课数据
        '''
        objs = models.CountryToResourcePlatformSyncLog.objects.filter(used=False).order_by('created_at')

        post_data = []

        for obj in objs:
            data = {}
            one = serializers.deserialize('json', obj.operation_content)
            pk = obj.pk
            for i in one:
                # teacherloginlog 上课信息
                teacherloginlog = i.object.teacherloginlog
                model_name = i.object.__class__.__name__
                data.update({
                    'pk': pk,
                    'model_name': model_name,
                    'term_school_year': teacherloginlog.term_school_year,
                    'term_type': teacherloginlog.term_type,
                    'province_name': teacherloginlog.province_name,
                    'city_name': teacherloginlog.city_name,
                    'country_name': teacherloginlog.country_name,
                    'town_name': teacherloginlog.town_name,
                    'school_name': teacherloginlog.school_name,
                    'grade_name': teacherloginlog.grade_name,
                    'class_name': teacherloginlog.class_name,
                    'lesson_name': teacherloginlog.lesson_name,
                    'teacher_name': teacherloginlog.teacher_name,
                    'lesson_period_start_time': teacherloginlog.lesson_period_start_time.strftime('%H:%M:%S'),
                    'lesson_period_end_time': teacherloginlog.lesson_period_end_time.strftime('%H:%M:%S'),
                    'weekday': teacherloginlog.weekday,
                    'log_create_time': teacherloginlog.created_at.strftime('%Y-%m-%d %H:%M:%S')
                })
                # 大纲与上课信息
                if model_name == 'TeacherLoginLogLessonContent':
                    lessoncontent = i.object.lessoncontent

                    data.update({'publish': lessoncontent.syllabus_grade_lesson.publish,
                                 'bookversion': lessoncontent.syllabus_grade_lesson.bookversion,
                                 'seq': lessoncontent.seq, 'subseq': lessoncontent.subseq, 'title': lessoncontent.title})
                    if lessoncontent.parent:
                        parent_title = lessoncontent.parent.title
                    else:
                        parent_title = u''
                    data.update({'parent_title': parent_title})

                # 课件与上课信息
                elif model_name == 'TeacherLoginLogCourseWare':
                    courseware = i.object.courseware

                    data.update({'md5': courseware.md5, 'title': courseware.title, 'size': courseware.size, 'use_times': courseware.use_times,
                                 'download_times': courseware.download_times, 'qiniu_url': courseware.qiniu_url, 'log_create_time': courseware.create_time.strftime('%Y-%m-%d %H:%M:%S')})

            post_data.append(data)

        url = "%s/view/api/sync/country-to-resourceplatform/" % (host)

        try:
            ret = requests.post(url, data={'data': base64.b64encode(bz2.compress(json.dumps(post_data)))}, timeout=120)
            ret = ret.json()

            if ret['status'] == 'success':
                for obj in objs.filter(pk__in=ret['success_pk']):
                    obj.used = True
                    obj.save()

        except:
            self.logger.exception('')

    def __init__(self):
        if models.Setting.getvalue('installed') != 'True':
            return
        if models.Setting.getvalue('server_type') != 'country':
            return

        # 资源平台HOST http://xxxxx:xx/
        self._sync_data(constants.RESOURCE_PLATFORM_HOST)
