# coding=utf-8
import re
import time
# import json
import datetime
import logging
import requests
import hashlib
from django.conf import settings
from django.core.cache import cache
from utils.decorator import cached_property
from django import forms
from BanBanTong.db import models
# from BanBanTong.forms.class_mac import ClassForm
from BanBanTong.forms.teacher import TeacherForm
from BanBanTong.forms.lesson_teacher import LessonTeacherForm
logger = logging.getLogger(__name__)

conf = settings.CONF
p1 = re.compile(u'^(\d{4}#)?([初高]?中?[一二三四五六]?(年级)?)(\d{4}级)?(([(（]?.*?[)）]?))?班?$')
p2 = re.compile(u'^[(（](.*?)[)）]$')
grade_name_map = {k.decode('utf8'): v.decode('utf8') for k, v in conf.sync_api.grade_name_map.items()}
weekday_map = dict(list(enumerate(['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'])))

key_map = {}
for k, v in conf.sync_api.json_key_map.items():
    lst = v.split('|')
    for key in lst:
        key_map[key.decode('utf8')] = k

"""
settings.ini示例:
[DEFAULT]
debug=true

[server]
grade_map='一:一,二:二,三:三,四:四,五:五,六:六,七:初一,八:初一,九:初一,十:高一,十一:高二,十二:高三,电脑教室:电脑教室'


[db]
port=3306
user=root
name=bbt-school

[sync_api]
hostname=http://172.16.42.2:21070
school_id=2300000001000649700
sync_type=json
job_start_path=/bbt/bbt/index.do
school_domain_path=/bbt/bbt/getSchoolAdress.do
school_openapi_path=/opendata/api/data/query
teacher_path=/bbt/bbt/getSchoolMsgJson.do
teachers_key=list_teacher
lesson_teachers_key=list_shouke
grade_name_map='小学-1:一,小学-2:二,小学-3:三,小学-4:四,小学-5:五,小学-6:六,初中-1:初一,初中-2:初二,初中-3:初三,高中-1:高一,高中-2:高二,高中-3:高三'
json_path=/bbt/bbt/getSchoolMsgJson.do
json_key_map='class_id:班级ID,grade_name:学段,class_name:授课班级,teacher_id:ID|Id,teacher_name:姓名,teacher_sex:性别,teacher_edu_background:学历,teacher_birthday:生日|出生年月,teacher_title:教师职称,teacher_mobile:移动电话,teacher_qq:QQ,teacher_remark:备注,teacher_register_at:注册时间,lesson_name:授课课程,schedule_time:schedule_time,sequence:sequence,start_time:start_time,end_time:end_timeme,lesson_period:lesson_period,weekday:weekdaya,levelname:grade_name'
json_teacher_key=teachers
json_class_key=classes
json_lesson_teacher_key=lesson_teachers

"""


class LessonScheduleForm(forms.ModelForm):

    class Meta:
        model = models.LessonSchedule
        exclude = ['uuid']


class ClassForm(forms.ModelForm):
    begin_year = forms.IntegerField(required=True)
    grade_name = forms.CharField(max_length=30)
    grade_number = forms.IntegerField(required=False)

    class Meta:
        model = models.Class
        exclude = ['uuid', 'grade']

    def clean_grade_name(self):
        begin_year = self.cleaned_data['begin_year']
        grade_name = self.cleaned_data['grade_name']
        now = datetime.datetime.now()
        return grade_name_map.get(u'%s-%s' % (grade_name, now.year - int(begin_year) + 1))

    def clean_grade_number(self):
        return abs(int(self.cleaned_data['grade_number']))

    def clean_name(self):
        class_name = self.cleaned_data['name']
        class_name = p1.match(class_name) and p1.match(class_name).groups()[-1] or class_name
        class_name = p2.match(class_name) and p2.match(class_name).group(1) or class_name
        return class_name

    def clean_number(self):
        return abs(int(self.cleaned_data['number']))

    def save(self, term, *args, **kw):
        grade, is_new = models.Grade.objects.get_or_create(name=self.cleaned_data['grade_name'], number=self.cleaned_data['grade_number'], term=term)
        obj, is_new = models.Class.objects.get_or_create(
            number=self.cleaned_data['number'],
            grade=grade,
            defaults={'name': self.cleaned_data['name']}
        )
        if not is_new and obj.name != self.cleaned_data['name']:
            obj.name = self.cleaned_data['name']
            obj.save()
        return obj


class Task(object):
    """
    从科大讯飞的校园平台上面拉取基础数据, 包括年级/班级/教师/授课教师/课表信息
    """
    run_period = 60 * 60

    def fetch(self, url, method='GET', **params):
        logger.debug('url=%s, params=%s', url, params)
        if method == 'GET':
            ret = self.session.get(url, params=params)
        else:
            ret = self.session.request(method, url, data=params)

        # if isinstance(data, dict) and data.get('status') == 'success':
        #     data = json.loads(data['data'])
        logger.debug('ret=%s', ret)
        return ret

    def send_start_job_signal(self):
        job_key = 'send_start_job_signal:%s' % conf.sync_api.school_id
        if not cache.get(job_key):
            logger.debug('start job.')
            self.fetch(conf.sync_api.hostname + conf.sync_api.job_start_path, sid=conf.sync_api.school_id)
            cache.set(job_key, datetime.datetime.now().strftime('%Y%m%d%H%M%S'), 3600)
        else:
            logger.debug('job already started at:%s', cache.get(job_key))

    @cached_property
    def school_info(self):
        data = {}
        if not conf.sync_api.school_id:
            raise Exception('School ID not set.')
        req = self.fetch(conf.sync_api.hostname + conf.sync_api.school_domain_path, sid=conf.sync_api.school_id)
        if req.ok and req.json()['code'] == 'success':
            data = req.json()
        if data['domain'] and not data['domain'].startswith('http'):
            data['domain'] = 'http://%s' % data['domain']
        return data

    def get_json_info_iflytek(self):
        req = self.fetch(conf.sync_api.hostname + conf.sync_api.json_path, sid=conf.sync_api.school_id)
        if not (req.ok and req.json()['code'] == 'success'):
            return
        data = req.json()
        now = datetime.datetime.now()
        original_teachers = [{key_map[k]: v for k, v in d.items()} for d in data.get(conf.sync_api.teachers_key)]
        original_lesson_teachers = [{key_map[k]: v for k, v in d.items()} for d in data.get(conf.sync_api.lesson_teachers_key)]
        lesson_teachers = {}
        teachers = {}
        for obj in original_teachers:
            teachers[obj['teacher_id']] = {
                'name': obj.get('teacher_name'),
                'sex': obj.get('teacher_sex', u'男') == u'男' and 'male' or 'female',
                'edu_background': obj.get('teacher_edu_background') or u'未知',
                'title': obj.get('teacher_title', ''),
                'mobile': obj.get('teacher_mobile', ''),
                'qq': obj.get('teacher_qq', ''),
                'remark': obj.get('teacher_remark'),
                'birthday': obj['teacher_register_at'].strip().split(' ', 1)[0],
                'teacher_id': int(obj['teacher_id']) % 10 ** 9
            }

        for obj in original_lesson_teachers:
            if not (obj['teacher_id'] and obj['class_id'] and obj['lesson_name']):
                continue

            class_year, class_name = obj['class_name'].split('-', 1)
            grade_name = grade_name_map.get(u'%s-%s' % (obj['grade_name'], now.year - int(class_year) + 1))
            if not (grade_name and class_name):
                logger.debug(u'not found: grade_name=%s, class_name=%s', grade_name, class_name)
                continue

            class_name = p1.match(class_name) and p1.match(class_name).groups()[-1] or class_name
            class_name = p2.match(class_name) and p2.match(class_name).group(1) or class_name
            lesson_teachers['%s-%s-%s' % (obj['teacher_id'], obj['class_id'], obj['lesson_name'])] = {
                "grade_name": grade_name,
                "class_name": class_name,
                "lesson_name": obj['lesson_name'],
                "teacher_name": obj['teacher_name'],
                "birthday": teachers[obj['teacher_id']]['birthday'],
                "teacher_id": int(obj['teacher_id']) % 10 ** 9,
                "schedule_time": 0
            }

        self.get_teacher_info(teachers.values())
        self.get_lesson_teacher_info(lesson_teachers.values())

    def get_teacher_info(self, records=None):
        """
        URL: /bbt/teacher.json?sid={school_id}
        从市级平台获取指定学校的教师信息
        返回状态码说明:
            200 数据已经准备好
            204 请求已经接受, 数据尚未准备好
            400 参数错误
            500 服务器异常

        返回的文件内容格式(标准json文件):
        {
            "records": [
                // 教师ID        姓名           性别          教育背景                 出生日期                 职称        电弧         QQ       备注
                {"teacher_id":31, "name":"张三", "sex":"male", "edu_background":"本科", "birthday":"2017-01-01", "title":"", "mobile":"", "qq":"", "remark":""},
                {"teacher_id":32, "name":"李四", "sex":"male", "edu_background":"本科", "birthday":"2017-01-01", "title":"", "mobile":"", "qq":"", "remark":""},
                {"teacher_id":33, "name":"王五", "sex":"male", "edu_background":"本科", "birthday":"2017-01-01", "title":"", "mobile":"", "qq":"", "remark":""},
            ]
        }
        """
        if records is None:
            ret = self.fetch(conf.sync_api.hostname + conf.sync_api.teacher_path, sid=conf.sync_api.school_id)
            if ret.status_code == 200:
                records = ret.json()[conf.sync_api.json_teacher_key]

        logger.debug('teachers=%s', records)
        school = models.Group.objects.get(group_type='school')
        for data in records:
            try:
                obj = models.Teacher.objects.get(sequence=data['teacher_id'])
            except models.Teacher.MultipleObjectsReturned:
                obj = models.Teacher.objects.filter(sequence=data['teacher_id'], name=data['name'], sex=data['sex'], birthday=data['birthday']).first()
            except models.Teacher.DoesNotExist:
                obj = None
            data['sequence'] = data.get('sequence') or data['teacher_id']
            f = TeacherForm(data, instance=obj)
            if f.is_valid() and f.has_changed():
                # f.save()
                teacher = f.save(commit=False)
                teacher.school = school
                teacher.deleted = False
                teacher.save()
            elif not f.is_valid():
                logger.warning('errors=%s', f.errors)

    def get_class_info(self, records=None, get_records=False):
        """从校级平台获取指定学校的年级班级信息"""
        timestamp = int(time.time() * 1000)
        ret = self.fetch(self.school_info['domain'] + conf.sync_api.school_openapi_path, method='POST', **{
            'clientId': 'bbt_id',
            'clientSecrect': 'bbt_name',
            'timestamp': timestamp,
            'signature': hashlib.md5('bbt_id' + 'bbt_name' + str(timestamp)).hexdigest(),
            'table': 'class'
        })
        logger.debug(ret.json())
        if ret.status_code == 200:
            records = ret.json()
            if get_records:
                return records
            term = models.Term.get_current_term_list()[0]
            for data in records:
                try:
                    obj = models.Class.objects.get(number=abs(data['classid']))
                except models.Class.DoesNotExist:
                    obj = None
                f = ClassForm({
                    "begin_year": int(data['rxnd']),
                    "grade_name": data['levelname'],
                    "grade_number": abs(data['gradeid']),
                    "name": data['classname'],
                    "number": abs(data['classid']),
                }, instance=obj)
                if obj:
                    self.class_map[u'%s-%s-%s' % (term.pk, obj.grade.name, obj.name)] = obj

                if f.is_valid() and f.has_changed():
                    try:
                        obj = f.save(term)
                    except:
                        continue
                    self.class_map[u'%s-%s-%s' % (term.pk, obj.grade.name, obj.name)] = obj
                elif not f.is_valid():
                    logger.warning('data=%s, errors=%s', data, f.errors)

    def get_lesson_teacher_info(self, records=None):
        """
        URL: /bbt/lesson_teacher.json?sid={school_id}
        从市级平台获取指定学校的授课教师信息
        返回状态码说明:
            200 数据已经准备好
            204 请求已经接受, 数据尚未准备好
            400 参数错误
            500 服务器异常

        返回的文件内容格式(标准json文件):
        {
            "records": [
                // 课程名              教师ID          班级ID         计划课时
                {"lesson_name":"语文", "teacher_id":31, "class_id":21, "schedule_time":20},
                {"lesson_name":"数学", "teacher_id":32, "class_id":22, "schedule_time":20},
                {"lesson_name":"英语", "teacher_id":33, "class_id":23, "schedule_time":20},
            ]
        }
        """
        if records is None:
            ret = self.fetch(conf.sync_api.hostname + conf.sync_api.lesson_teacher_path, sid=conf.sync_api.school_id)
            if ret.status_code == 200:
                records = ret.json()[conf.sync_api.json_lesson_teacher_key]
        logger.debug('lesson_teachers=%s', records)
        for data in records:
            try:
                obj = models.LessonTeacher.objects.get(
                    class_uuid__name=data['class_name'],
                    class_uuid__grade__name=data['grade_name'],
                    teacher__sequence=data['teacher_id'],
                    lesson_name__name=data['lesson_name']
                )
            except models.LessonTeacher.DoesNotExist:
                obj = None
            f = LessonTeacherForm(data, instance=obj)
            if not obj:
                f.fields['teacher'].required = False
            if f.is_valid() and f.has_changed():
                f.save()
            elif not f.is_valid():
                logger.warning('data=%s, errors=%s', data, f.errors)

    def get_lesson_period_info(self, records=None):
        """
        URL: /bbt/lesson_period.json?sid={school_id}
        从市级平台获取指定学校的作息时间信息
        返回状态码说明:
            200 数据已经准备好
            204 请求已经接受, 数据尚未准备好
            400 参数错误
            500 服务器异常

        返回的文件内容格式(标准json文件):
        {
            "records": [
                // 节次        开始时间              结束时间
                {"sequence":1, "start_time":"08:00", "end_time":"08:45"},
                {"sequence":2, "start_time":"09:00", "end_time":"09:45"},
                {"sequence":3, "start_time":"10:00", "end_time":"10:45"},
            ]
        }
        """
        ret = self.fetch(conf.sync_api.hostname + conf.sync_api.lesson_teacher_path, sid=conf.sync_api.school_id)
        print ret

    def get_lesson_schedule_info(self):
        """从校级平台获取指定学校的课表信息"""
        t = models.Term.get_current_term_list()[0]
        # grade_classes = self.get_class_info(get_records=True)
        grade_map = {g.number: g.name for g in models.Grade.objects.filter(term=t)}
        lesson_period_map = {obj.sequence: obj.pk for obj in models.LessonPeriod.objects.filter(term=t)}
        lesson_name_map = {obj.name: obj.pk for obj in models.LessonName.objects.all()}
        logger.debug('lesson_period_map=%s', lesson_period_map)
        logger.debug('grade_map=%s', grade_map)
        # now = datetime.datetime.now()
        timestamp = int(time.time() * 1000)
        ret = self.fetch(self.school_info['domain'] + conf.sync_api.school_openapi_path, method='POST', **{
            'clientId': 'bbt_id',
            'clientSecrect': 'bbt_name',
            'timestamp': timestamp,
            'signature': hashlib.md5('bbt_id' + 'bbt_name' + str(timestamp)).hexdigest(),
            'table': 'classArrangement',
            'data': "{groupOp:'and',orderBy:'',rules:[{field:'xn',op:'eq',data:'%(school_year)s'},{field:'weekend',op:'eq',data:'%(week)s'},{field:'xq',op:'eq',data:'%(term_type)s'}]}" % {
                'school_year': '2017-2018',
                'week': '1',
                'term_type': u'第一学期'
            }
        })
        logger.debug('ret=%s', ret.json())
        lesson_schedules = {}
        for obj in ret.json():
            class_name = obj['classname']
            # grade_name = grade_name_map.get(u'%s-%s' % (obj['grade_name'], now.year - int(obj['rxnd']) + 1))
            grade_name = grade_map.get(obj['gradeid'])
            if not (grade_name and class_name):
                continue

            class_name = p1.match(class_name) and p1.match(class_name).groups()[-1] or class_name
            class_name = p2.match(class_name) and p2.match(class_name).group(1) or class_name
            try:
                class_uuid = self.class_map.get('%s-%s-%s' % (t.pk, grade_name, class_name))
                if not class_uuid:
                    class_uuid = models.Class.objects.get(name=class_name, grade__name=grade_name, grade__term=t)
                    self.class_map['%s-%s-%s' % (t.pk, grade_name, class_name)] = class_uuid
            except models.Class.DoesNotExist:
                logger.warning('grade=%s, class=%s, does not exist.', grade_name, class_name)
                continue
            except Exception as e:
                logger.exception(e)

            weekday_index, sequence = obj['table_id'].split(',', 1)
            lesson_schedules['%s-%s' % (obj['class_id'], obj['table_id'])] = {
                "class_uuid": class_uuid.pk,
                "lesson_name": lesson_name_map.get(obj['kcmc']),
                "weekday": weekday_map.get(int(weekday_index.strip()) - 1),
                "lesson_period": lesson_period_map.get(int(sequence.strip())),
            }
            logger.debug('lesson_schedules=%s', lesson_schedules)
        records = lesson_schedules.values()
        for data in records:
            try:
                obj = models.LessonSchedule.objects.get(
                    class_uuid=data['class_uuid'],
                    lesson_period=data['lesson_period'],
                    weekday=data['weekday']
                )
            except models.LessonSchedule.DoesNotExist:
                obj = None
            f = LessonScheduleForm(data, instance=obj)
            if f.is_valid() and f.has_changed():
                f.save()
            elif not f.is_valid():
                logger.warning('data=%s, errors=%s', data, f.errors)

    def sync(self):
        self.send_start_job_signal()
        if conf.sync_api.sync_type == 'normal':
            self.get_grade_class_info()
            self.get_teacher_info()
            self.get_lesson_teacher_info()
            self.get_lesson_schedule_info()
        elif conf.sync_api.sync_type == 'json':
            self.get_class_info()
            self.get_json_info_iflytek()
            self.get_lesson_schedule_info()

    def __init__(self, force=False):
        if models.Setting.getvalue('installed') != 'True':
            return
        if models.Setting.getvalue('server_type') != 'school':
            return
        if datetime.datetime.now().hour in range(9, 18) and not force:
            return
        if not conf.sync_api.school_id:
            return
        self.class_map = {}
        self.session = requests.Session()
        self.sync()
