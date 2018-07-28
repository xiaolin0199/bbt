#!/usr/bin/env python
# coding=utf-8
import base64
import bz2
import datetime
import hashlib
import json
import logging
import time
import uuid
import urllib
import urllib2
from django.conf import settings
from django.core import serializers
from django.core import validators
from django.core.cache import cache
from django.core.serializers.base import DeserializationError
import django.db
from django.db import models
from django.db.models import signals, Sum
from django.db.models.query import QuerySet
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.utils.dateparse import parse_date

from BanBanTong import constants
from BanBanTong.utils import mongo
from BanBanTong.utils import str_util, get_macs


DEBUG = settings.DEBUG
logger = logging.getLogger(__name__)

SEX = (
    ('female', u'女'),
    ('male', u'男'),
)
ASSET_FROM = (
    (u'校自主采购', u'校自主采购'),
    (u'县级电教采购', u'县级电教采购'),
    (u'地级电教采购', u'地级电教采购'),
    (u'省级电教采购', u'省级电教采购'),
    (u'其他', u'其他'),
)
ASSET_LOG_TYPE = (
    (u'新增', u'新增'),
    (u'停用', u'停用'),
)
ASSET_STATUS = (
    (u'在用', u'在用'),
    (u'停用', u'停用'),
)
ASSET_TYPE = (
    ('pc', u'台式计算机'),
    ('whiteboard', u'电子白板'),
    ('projector', u'投影仪'),
    ('visual_presenter', u'视频展台'),
    ('center_console', u'教室中控台'),
    ('lfd', u'大屏显示器'),
    ('notebook', u'笔记本'),
    ('printer', u'打印机'),
    ('thin_terminal', u'瘦终端'),
    ('switchboard', u'网络交换机'),
    ('others1', u'其他教具1'),
    ('others2', u'其他教具2'),
    ('others3', u'其他教具3'),
)
GROUP_TYPES = (
    ('province', 'province'),
    ('city', 'city'),
    ('country', 'country'),
    ('town', 'town'),
    ('school', 'school'),
    ('grade', 'grade')
)
RESOURCE_TYPES = (
    (u'音频', u'音频'),
    (u'音视频', u'音视频'),
    (u'PPT 幻灯片', u'PPT 幻灯片'),
    (u'文档', u'文档'),
    (u'动画片', u'动画片'),
    (u'其它', u'其它'),
)
TERM_TYPES = (
    (u'春季学期', u'春季学期'),
    (u'秋季学期', u'秋季学期'),
)
TOKEN_TYPES = (
    ('lesson_start', 'lesson_start'),
    ('node_sync', 'node_sync'),
    ('user_login', 'user_login'),
)
USER_LEVELS = (
    ('province', u'省级'),
    ('city', u'市级'),
    ('country', u'乡级'),
    ('town', u'县级'),
    ('school', u'校级'),
)
USER_STATUS = (
    ('active', u'已激活'),
    ('suspended', u'已禁用'),
)
WEEK_KEYS = (
    ('mon', u'星期一'),
    ('tue', u'星期二'),
    ('wed', u'星期三'),
    ('thu', u'星期四'),
    ('fri', u'星期五'),
    ('sat', u'星期六'),
    ('sun', u'星期天'),
)
AREA_LEVELS = ['school', 'town', 'country', 'city', 'province']


class BigAutoField(models.AutoField):

    def db_type(self, connection):
        if 'mysql' in connection.__class__.__module__:
            return 'bigint AUTO_INCREMENT'
        return super(BigAutoField, self).db_type(connection)


class PasswordCharField(models.CharField):

    def save_form_data(self, instance, data):
        if data != u'':
            data = data.encode('utf8')
            setattr(instance, self.name, hashlib.sha1(data).hexdigest())


def _make_uuid():
    return str(uuid.uuid1()).upper()


class SyncLogPack(object):
    """
    对于Exception：

    问题严重，无法保存数据，需要让unpack过程终止的，就raise
    否则就忽略掉
    """

    @staticmethod
    def unpack_log(operation_type, operation_content, silent=True):
        try:
            if operation_type == 'add':
                for obj in serializers.deserialize('json', operation_content):
                    if isinstance(obj.object, Group):
                        obj.object.save()
                    if isinstance(obj.object, Setting) and obj.object.name == 'activation':
                        value = json.loads(str_util.decode(obj.object.value))
                        if isinstance(value, dict):
                            Setting.setval('activation', value)
                    else:
                        logger.debug('add %s', obj)
                        obj.object.save(force_insert=True)
            elif operation_type == 'update':
                for obj in serializers.deserialize('json', operation_content):
                    try:
                        obj.object.save(force_update=True)
                    except:
                        obj.object.save(force_insert=True)
            elif operation_type == 'delete':
                for obj in serializers.deserialize('json', operation_content):
                    obj.object.delete()
        except UnicodeDecodeError, e:
            logger.exception('%s', operation_content)
            raise e
        except DeserializationError, e:
            logger.exception('%s', operation_content)
            raise e
        except django.db.IntegrityError, e:
            if e.args[0] == 1062:
                # Duplicate entry '%s' for key '%s'
                if "for key 'PRIMARY'" in e.args[1]:
                    # 主键重复，说明此记录已存在，可以放心跳过
                    # logger.exception('主键重复 %s', operation_content)
                    pass
                else:
                    # 其他UNIQUE KEY重复，要记下来看看到底是怎么回事
                    logger.exception('IntegrityError 1062 %s %s %s %s',
                                     operation_type, operation_content,
                                     e.args, e.message)
            elif e.args[0] == 1452:
                # Cannot add or update a child row: a foreign key constraint fails
                logger.exception('')
            else:
                logger.exception('%s', e.args)
                raise e
        except django.db.OperationalError, e:
            if e.args[0] == 2006:  # MySQL server has gone away
                # 摘自django_mysqlpool.auto_close_db
                for connection in django.db.connections.all():
                    connection.close()
            elif e.args[0] == 2014 and silent:  # Command Out of Sync
                try:
                    cursor = django.db.connection.cursor()
                    cursor.close()
                except Exception as e:
                    logger.exception(e)
                time.sleep(5)
                return SyncLogPack.unpack_log(operation_type, operation_content, silent=False)
            raise e
        except django.db.DatabaseError, e:
            if operation_type == 'update':
                if e.args[0] == 'Forced update did not affect any rows.':
                    logger.exception('skip record Force update: %s',
                                     operation_content)
                else:
                    logger.exception('DatabaseError %s %s',
                                     e.args, operation_content)
            else:
                logger.exception('%s %s', operation_type, operation_content)
                raise e
        except StandardError, e:
            logger.exception('%s %s', operation_type, operation_content)
            raise e
        except Exception as e:
            logger.exception('err=%s, operation_type=%s, operation_content=%s', e, operation_type, operation_content)
            if not silent:
                raise e


class InitModel(models.Model):

    def __iter__(self):
        _dict = self.to_dict()
        return _dict.iteritems()

    # def to_dict(self, max_depth=2, depth=0, *args, **kw):
    #     return model_to_dict(self, max_depth, depth, *args, **kw)

    def _pack_log(self, dict_data):
        class_name = self.__class__.__name__
        pack_func_name = '_pack_log_for_%s' % class_name
        if hasattr(self, pack_func_name):
            pack_func = getattr(self, pack_func_name)
            return pack_func(dict_data)

        return dict_data

    def save(self, *args, **kwargs):
        if 'force_insert' in kwargs and kwargs['force_insert']:
            log_type = 'add'
        elif 'force_update' in kwargs and kwargs['force_update']:
            log_type = 'update'
        else:
            if self._state.adding:
                log_type = 'add'
            else:
                log_type = 'update'
        super(InitModel, self).save(*args, **kwargs)
        # if self.__class__.__name__ == 'TeacherLoginLogLessonContent':
        if self.__class__.__name__ in ['TeacherLoginLogLessonContent',
                                       'TeacherLoginLogCourseWare']:
            # 如果是县级服务器则写同步log
            if Setting.getvalue('server_type') == 'country' and settings.CONF.server.sync_resource_enable:
                CountryToResourcePlatformSyncLog.add_log(self, log_type)
            if Setting.getvalue('server_type') != 'school':  # 只需要从校级传到县级
                if Setting.getvalue('installed') == 'True':  # 回传到校级时也要写log
                    return
        if settings.CONF.server.sync_log_enable:
            try:
                cursor = django.db.connection.cursor()
                cursor.execute('UNLOCK TABLES;')
                cursor.close()
            except Exception as e:
                logger.exception(e)
            SyncLog.add_log(self, log_type, self._pack_log)

    class Meta:
        abstract = True


class BaseModel(InitModel):
    uuid = models.CharField(primary_key=True, default=_make_uuid, max_length=40)

    class Meta:
        abstract = True


class SchoolPost(models.Model):
    title = models.CharField(u'标题', max_length=100)
    content = models.TextField(u'内容', blank=True, null=True)
    active = models.BooleanField(u'是否启用', default=False)
    create_date = models.DateTimeField(u'创建时间', auto_now_add=True)
    update_date = models.DateTimeField(u'更新时间', auto_now=True, null=True, blank=True)
    expire_date = models.DateTimeField(u'过期时间', blank=True, null=True)

    def __unicode__(self):
        return self.title


class ActiveTeachers(models.Model):
    """该表用于记录登记教师的授课状态"""

    teacher = models.ForeignKey('Teacher', to_field='uuid',
                                db_column='teacher_uuid')
    active_date = models.DateField()
    country_name = models.CharField(max_length=100, blank=True)
    town_name = models.CharField(max_length=100, blank=True)
    school_name = models.CharField(max_length=100, blank=True)
    school_year = models.CharField(max_length=20)
    term_type = models.CharField(max_length=20)
    lesson_name = models.CharField(max_length=20, blank=True)
    grade_name = models.CharField(max_length=20, blank=True)

    class Meta:
        index_together = [
            # ('school_year', 'term_type', 'town_name', 'school_name', 'lesson_name',),
            ('school_year', 'term_type', 'town_name', 'school_name', 'grade_name',),
            # ('active_date', 'town_name', 'school_name', 'lesson_name',),
            ('active_date', 'teacher', 'town_name', 'school_name', 'grade_name',),
            # ('school_year', 'term_type', 'lesson_name', 'grade_name',),
            # ('active_date', 'lesson_name', 'grade_name',),
        ]


class Asset(BaseModel):
    """资产表"""

    related_asset = models.ForeignKey('Asset',
                                      help_text='停用设备对应的在用批次uuid',
                                      db_column='related_asset_uuid',
                                      limit_choices_to={'status': '在用'},
                                      on_delete=models.SET_NULL,
                                      blank=True, null=True,
                                      db_index=True)
    asset_type = models.ForeignKey('AssetType', to_field='uuid',
                                   db_column='asset_type_uuid',
                                   db_index=True)
    school = models.ForeignKey('Group', to_field='uuid',
                               db_column='school_uuid',
                               limit_choices_to={'group_type': 'school'},
                               db_index=True)
    device_model = models.CharField(max_length=100,
                                    help_text='设备型号',
                                    db_index=True)
    number = models.IntegerField(help_text='设备数量',
                                 db_index=True)
    asset_from = models.CharField(max_length=10,
                                  help_text='资产来源',
                                  choices=ASSET_FROM)
    reported_by = models.CharField(max_length=20,
                                   help_text='申报用户',
                                   blank=True,
                                   db_index=True)
    reported_at = models.DateTimeField(auto_now_add=True,
                                       help_text='申报时间',
                                       db_index=True)
    status = models.CharField(max_length=20,
                              help_text='资产状态',
                              choices=ASSET_STATUS,
                              default=u'在用',
                              db_index=True)
    remark = models.CharField(max_length=180, blank=True, db_index=True)

    def __unicode__(self):
        return '%s: %s' % (self.asset_type.name, self.device_model)

    class Meta:
        db_table = 'Asset'


class AssetType(BaseModel):
    """资产类型"""

    name = models.CharField(max_length=20,
                            db_index=True)
    icon = models.CharField(max_length=20)
    unit_name = models.CharField(max_length=10,
                                 help_text='数量单位',
                                 blank=True)
    school = models.ForeignKey('Group', to_field='uuid',
                               db_column='school_uuid',
                               limit_choices_to={'group_type': 'school'},
                               related_name='school_assettype_set',
                               blank=True, null=True,
                               db_index=True)
    # 预设5个系统类型不能删除
    cannot_delete = models.BooleanField(default=False)
    # 删除类型之后只做个标记
    deleted = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def test_speak(self):
        return u'%s' % (self.icon)

    class Meta:
        db_table = 'AssetType'


class AssetLog(BaseModel):
    """资产申报记录"""

    country_name = models.CharField(max_length=100,
                                    blank=True)
    town = models.ForeignKey('Group', to_field='uuid',
                             db_column='town_uuid',
                             limit_choices_to={'group_type': 'town'},
                             related_name='town_assetlog_set',
                             blank=True, null=True,
                             on_delete=models.SET_NULL,
                             db_index=True)
    town_name = models.CharField(max_length=100,
                                 blank=True)
    school = models.ForeignKey('Group', to_field='uuid',
                               db_column='school_uuid',
                               limit_choices_to={'group_type': 'school'},
                               related_name='school_assetlog_set',
                               blank=True, null=True,
                               on_delete=models.SET_NULL,
                               db_index=True)
    school_name = models.CharField(max_length=100)
    reported_at = models.DateTimeField(auto_now_add=True,
                                       db_index=True)
    log_type = models.CharField(max_length=10,
                                help_text='申报类型',
                                choices=ASSET_LOG_TYPE,
                                db_index=True)
    asset_type = models.ForeignKey('AssetType', to_field='uuid',
                                   db_column='asset_type_uuid',
                                   db_index=True)
    asset_from = models.CharField(max_length=10,
                                  help_text='资产来源',
                                  choices=ASSET_FROM,
                                  default='',
                                  blank=True)
    device_model = models.CharField(max_length=100,
                                    help_text='设备型号',
                                    db_index=True)
    number = models.IntegerField(help_text='设备数量',
                                 db_index=True)
    reported_by = models.CharField(max_length=20,
                                   help_text='申报用户',
                                   blank=True, null=True,
                                   db_index=True)
    remark = models.CharField(max_length=180, blank=True, db_index=True)

    class Meta:
        db_table = 'AssetLog'


class AssetRepairLog(BaseModel):
    country_name = models.CharField(max_length=100,
                                    blank=True)
    town = models.ForeignKey('Group', to_field='uuid',
                             db_column='town_uuid',
                             limit_choices_to={'group_type': 'town'},
                             related_name='town_assetrepairlog_set',
                             blank=True, null=True,
                             on_delete=models.SET_NULL,
                             db_index=True)
    town_name = models.CharField(max_length=100,
                                 blank=True)
    school = models.ForeignKey('Group', to_field='uuid',
                               db_column='school_uuid',
                               limit_choices_to={'group_type': 'school'},
                               related_name='school_assetrepairlog_set',
                               blank=True, null=True,
                               on_delete=models.SET_NULL,
                               db_index=True)
    school_name = models.CharField(max_length=100,
                                   blank=True)
    asset = models.ForeignKey('Asset', to_field='uuid',
                              db_column='asset_uuid',
                              blank=True, null=True,
                              on_delete=models.SET_NULL,
                              db_index=True)
    reported_at = models.DateTimeField(auto_now_add=True,
                                       db_index=True)
    reported_by = models.CharField(max_length=20,
                                   help_text='申报用户',
                                   blank=True, null=True,
                                   db_index=True)
    asset_type = models.ForeignKey('AssetType', to_field='uuid',
                                   db_column='asset_type_uuid',
                                   db_index=True)
    device_model = models.CharField(max_length=100,
                                    db_index=True)
    grade_name = models.CharField(max_length=20,
                                  db_index=True)
    class_name = models.CharField(max_length=20,
                                  db_index=True)
    remark = models.CharField(max_length=180, blank=True, db_index=True)

    class Meta:
        db_table = 'AssetRepairLog'


class Class(BaseModel):
    name = models.CharField(max_length=20, db_index=True)
    number = models.IntegerField(default=0, blank=True, db_index=True)
    grade = models.ForeignKey('Grade', to_field='uuid', db_column='grade_uuid', db_index=True)
    teacher = models.ForeignKey('Teacher', to_field='uuid', db_column='teacher_uuid', blank=True, null=True)
    last_active_time = models.DateTimeField(blank=True, null=True)

    def cala_assigned_time(self):
        """计算该班级的所有已分配课时"""
        q = LessonTeacher.objects.filter(class_uuid=self)
        ret = q.aggregate(models.Sum('schedule_time'))['schedule_time__sum']
        if ret is None:
            ret = 0
        return ret

    def cala_remain_time(self):
        """计算该班级的所有未分配课时"""
        return int(self.grade.term.schedule_time) - int(self.cala_assigned_time())

    def mac(self):
        o = ClassMacV2.objects.filter(class_uuid=self.uuid)
        if o.exists():
            return o[0].mac
        return u''

    def ip(self):
        o = ClassMacV2.objects.filter(class_uuid=self.uuid)
        if o.exists():
            return o[0].ip
        return u''

    def get_status(self):
        if hasattr(self, 'computerclass') and self.grade.number == 13:
            return self.computerclass.get_status()

        lp = LessonPeriod.get_current_or_next_period()
        if not lp:
            return False, None
        today = datetime.datetime.now().date()
        s = datetime.datetime.combine(today, datetime.time.min)
        e = datetime.datetime.combine(today, datetime.time.max)
        logs = TeacherLoginLog.objects.filter(
            class_uuid=self.uuid,
            lesson_period=lp, created_at__range=(s, e)
        )
        if logs.exists():
            return True, logs[0]
        return False, None

    def rank(self, node_type='class', **kwargs):
        # 课程授课次数统计排名
        obj = Statistic.objects.get(key=self.pk)
        if node_type == 'lesson':
            # 课程排名
            lesson_name = kwargs.get('lesson_name')
            if not lesson_name:
                return -1
            cls_objs = [obj, ]
            # objs = obj.parent.get_descendants('lesson')
            brothers_and_me = Statistic.get_items_descendants(cls_objs, 'lesson')
            obj = brothers_and_me.get(name=lesson_name, parent=obj)
        elif node_type == 'school':
            # 全校排名
            brothers_and_me = obj.parent.parent.get_descendants('class')
        elif node_type == 'grade':
            # 年级排名
            brothers_and_me = obj.parent.get_descendants('class')
        lst = list(brothers_and_me.values_list('teach_count', flat=True))
        lst.sort(reverse=True)
        ranks = lst.index(obj.teach_count)
        if DEBUG:
            return '(%s/%s)' % (ranks + 1, len(lst))
        return ranks + 1

    def get_lesson_info(self):
        # 获取本班级当前节次的授课信息 节次/教师/课程
        lp, ls = None, None
        t = LessonTeacher.objects.none()
        lp = LessonPeriod.get_current_or_next_period()
        if not lp:
            return None
        wk = datetime.datetime.now().strftime('%a').lower()
        if self.grade.number != 13:
            lessons = self.lessonschedule_set.filter(lesson_period=lp, weekday=wk)
            teachers = self.lessonteacher_set
        else:
            lessons = self.computerclass.get_curriculum(True)
            lessons = lessons.filter(lesson_period=lp)
            _lst = lessons.values_list('class_uuid', flat=True)
            teachers = LessonTeacher.objects.filter(class_uuid__in=_lst)
        if lessons.exists():
            ls = lessons[0]
            t = teachers.filter(
                class_uuid=ls.class_uuid,
                lesson_name=ls.lesson_name
            )
        return {
            'sequence': lp and lp.sequence or None,
            'teacher_name': t.exists() and t[0].teacher.name or u'尚未分配',
            'lesson_name': ls and ls.lesson_name.name or u'尚未排课'
        }

    def get_lesson_schedule_info(self, lesson_name=None, teacher=None, **kwargs):
        # 改方法用于获取本班级的 指定课程/指定教师 的 授课次数/计划授课次数
        if self.grade.number != 13:
            objs = self.lessonteacher_set.filter(teacher__deleted=False)
        else:
            cls = kwargs.get('cls')
            if not cls:
                return {}
            objs = cls.lessonteacher_set.filter(teacher__deleted=False)

        if lesson_name:
            objs = objs.filter(lesson_name__name=lesson_name)
        if teacher:
            objs = objs.filter(teacher=teacher)
        schedule_time = objs.aggregate(x=Sum('schedule_time'))['x']
        finished_time = objs.aggregate(x=Sum('finished_time'))['x']
        return {
            'schedule_time': schedule_time and schedule_time or 0,
            'finished_time': finished_time and finished_time or 0
        }

    def save(self, *args, **kwargs):
        super(Class, self).save(*args, **kwargs)
        if constants.BANBANTONG_USE_MONGODB:
            mongo.save_class(self)
        cache.delete('class-all')
        # 上级服务器同步校级的班级或者校级新增/回传班级的时候创建节点
        Statistic.create_one_item(self.grade.term, self)
        # Tips
        # 编辑班级的时候只改变的是班主任(pk和name字段都没有变)
        # 所以这里可以不用考虑Statistic中节点的更新问题
        # 只是编辑班级的时候, Statistic中再走一遍get_or_create流程

    def delete(self, *args, **kwargs):
        Statistic.delete_one_item(self.grade.term, self)
        super(Class, self).delete(*args, **kwargs)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'Class'
        unique_together = ('name', 'grade')


class ClassMacV2(BaseModel):
    class_uuid = models.ForeignKey('Class', to_field='uuid',
                                   db_column='class_uuid',
                                   db_index=True)
    mac = models.CharField(max_length=64, blank=True)
    ip = models.CharField(max_length=64, blank=True, null=True)

    @staticmethod
    def is_computerclass(mac, get_obj=False):
        try:
            # FIXME:
            # 这样其实是有bug的, 应当限定term的范围
            cc = ClassMacV2.objects.get(mac=mac, class_uuid__grade__number=13)
            if get_obj:
                return cc
            return True
        except:
            return None


class ClassTime(BaseModel):
    """班级参考课时和已分配课时"""

    class_uuid = models.OneToOneField(Class)
    schedule_time = models.IntegerField()
    assigned_time = models.IntegerField()


class ComputerClass(BaseModel):
    # display_name = models.CharField(max_length=40, default='computerclass', db_index=True)
    client_number = models.IntegerField(default=0, blank=True)
    class_bind_to = models.OneToOneField('Class')
    lesson_range = models.ManyToManyField('LessonName', through='ComputerClassLessonRange', blank=True)

    def get_status(self):
        lp = LessonPeriod.get_current_or_next_period()
        if not lp:
            return False, None
        tags = TeacherLoginLogTag.objects.filter(created_at=self.class_bind_to)
        tags = tags.values_list('bind_to', flat=True)
        today = datetime.datetime.now().date()
        s = datetime.datetime.combine(today, datetime.time.min)
        e = datetime.datetime.combine(today, datetime.time.max)
        try:
            log = TeacherLoginLog.objects.get(uuid__in=tags, lesson_period=lp, created_at__range=(s, e))
            return True, log
        except:
            return False, None

    def get_curriculum(self, today=False):
        """
        获取当前教室的课程表

        默认获取全部课表数据,
        today为True时候获取当天的数据
        """
        lr = self.lesson_range.values_list('uuid', flat=True)
        t = Term.get_current_term_list()[0]
        ls = LessonSchedule.objects.filter(lesson_name__in=lr, class_uuid__grade__term=t)
        ls = ls.order_by('class_uuid__grade__number', 'class_uuid__number', 'lesson_period__sequence')
        if today:
            wk = datetime.datetime.now().strftime('%a').lower()
            ls = ls.filter(weekday=wk)
        return ls

    def __unicode__(self):
        return '%s(%s)' % (self.class_bind_to.name, self.class_bind_to.number)


class ComputerClassLessonRange(BaseModel):
    lessonname = models.ForeignKey('LessonName', db_index=True)
    computerclass = models.ForeignKey('ComputerClass', db_index=True)


class CountryToSchoolBaseModel(models.Model):
    """从县级向校级同步的数据"""

    def save(self, *args, **kwargs):
        if 'force_insert' in kwargs and kwargs['force_insert']:
            log_type = 'add'
        elif 'force_update' in kwargs and kwargs['force_update']:
            log_type = 'update'
        else:
            if self._state.adding:
                log_type = 'add'
            else:
                log_type = 'update'
        super(CountryToSchoolBaseModel, self).save(*args, **kwargs)
        if Setting.getvalue('server_type') != 'country':
            return
        CountryToSchoolSyncLog.add_log(self, log_type)

    class Meta:
        abstract = True


class CountryToSchoolSyncLog(models.Model):
    created_at = BigAutoField(primary_key=True)
    operation_type = models.CharField(max_length=10)
    operation_content = models.TextField(default='', blank=True)
    used = models.BooleanField(default=False)

    @staticmethod
    def add_log(instance, log_type):
        try:
            data = serializers.serialize('json', [instance, ])
            CountryToSchoolSyncLog.objects.create(operation_type=log_type,
                                                  operation_content=data)
        except:
            logger.exception('')

    @staticmethod
    def pack_all_data():
        q = CountryToSchoolSyncLog.objects.all().order_by('created_at')
        ret = serializers.serialize('json', q)
        ret = base64.b64encode(bz2.compress(ret))
        return ret


class CountryToResourcePlatformSyncLog(models.Model):
    """县级向资源平台同步上课数据"""

    created_at = BigAutoField(primary_key=True)
    operation_type = models.CharField(max_length=10)
    operation_content = models.TextField(default='', blank=True)
    used = models.BooleanField(default=False)

    @staticmethod
    def add_log(instance, log_type):
        try:
            data = serializers.serialize('json', [instance, ])
            CountryToResourcePlatformSyncLog.objects.create(operation_type=log_type, operation_content=data)
        except:
            logger.exception('')


class DesktopGlobalPreview(BaseModel):
    """用于实时概况>桌面预览的缓存表，只保存每个班级的最新预览图"""

    pic = models.ForeignKey('DesktopPicInfo', to_field='uuid',
                            db_column='pic_uuid',
                            db_index=True)


class DesktopGlobalPreviewTag(BaseModel):
    """用于实时概况>桌面预览的缓存表中标记预览图产生于电脑教室"""

    bind_to = models.OneToOneField('DesktopGlobalPreview')
    # created_by = models.ForeignKey('Class', blank=True, null=True)

    @staticmethod
    def update():
        lst = DesktopGlobalPreview.objects.all().values_list('uuid', flat=True)
        obj = DesktopGlobalPreviewTag.objects.exclude(bind_to__in=lst)
        obj.all().delete()
        return

    @staticmethod
    def get_lst():
        DesktopGlobalPreviewTag.update()
        lst = DesktopGlobalPreviewTag.objects.all().values_list('bind_to', flat=True)
        return lst


class DesktopPicInfo(BaseModel):
    """grade_number和class_number用于排序"""

    school_year = models.CharField(max_length=20, blank=True, null=True)
    term_type = models.CharField(max_length=20, blank=True, null=True)
    school = models.ForeignKey('Group', to_field='uuid',
                               db_column='school_uuid')
    grade = models.ForeignKey('Grade', to_field='uuid',
                              db_column='grade_uuid')
    grade_number = models.IntegerField()
    class_uuid = models.ForeignKey('Class', to_field='uuid',
                                   db_column='class_uuid')
    class_number = models.IntegerField()
    lesson_name = models.CharField(max_length=20)
    teacher_name = models.CharField(max_length=100)
    lesson_period_sequence = models.IntegerField()
    # 图片链接由http://<host><url>组成，其中<url>以斜杠开头
    host = models.CharField(max_length=180)
    url = models.CharField(max_length=180)
    created_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        self.school_year = self.grade.term.school_year
        self.term_type = self.grade.term.term_type
        super(DesktopPicInfo, self).save(*args, **kwargs)

    class Meta:
        index_together = [
            # ('class_uuid', 'school', 'lesson_period_sequence',),
            # ('class_uuid', 'created_at', 'lesson_period_sequence',),
            ('school_year', 'term_type',),
            ('created_at', 'class_uuid', 'lesson_period_sequence',),
        ]


class DesktopPicInfoTag(BaseModel):
    """用于使用记录>标记桌面使用日志的截屏产生于电脑教室"""

    bind_to = models.OneToOneField('DesktopPicInfo')
    created_by = models.ForeignKey('Class', blank=True, null=True)

    @staticmethod
    def get_lst(name='bind_to'):
        if not name:
            return dict(DesktopPicInfoTag.objects.all().values_list('bind_to', 'created_by', flat=True))

        return DesktopPicInfoTag.objects.all().values_list(name, flat=True)


class Grade(BaseModel):
    name = models.CharField(max_length=20, db_index=True)
    number = models.IntegerField(default=0, blank=True, db_index=True)
    term = models.ForeignKey('Term', to_field='uuid', db_column='term_uuid', db_index=True)

    def save(self, *args, **kwargs):
        super(Grade, self).save(*args, **kwargs)
        server_type = Setting.getvalue('server_type')
        if server_type == 'school':
            q = User.objects.all().values_list('uuid', flat=True)
            for uu in q:
                k = 'group-%s' % uu
                cache.delete(k)
        cache.delete('grade-all')

        # 上级服务器同步校级的年级或者校级新增/回传年级的时候创建节点
        Statistic.create_one_item(self.term, self)

    def delete(self, *args, **kwargs):
        Statistic.delete_one_item(self.term, self)
        super(Grade, self).delete(*args, **kwargs)

    @staticmethod
    def is_computerclass(grade_uuid):
        try:
            grade = Grade.objects.get(uuid=grade_uuid, number=13)
            return grade
        except:
            return False

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'Grade'


class Group(BaseModel):
    """省市区乡镇街道学校"""

    name = models.CharField(max_length=100)
    group_type = models.CharField(max_length=20, choices=GROUP_TYPES,
                                  db_index=True)
    parent = models.ForeignKey('self', to_field='uuid',
                               db_column='parent_uuid',
                               related_name='child_set', blank=True,
                               null=True, db_index=True)

    def __unicode__(self):
        return '%s: %s' % (self.group_type, self.name)

    # 获取当前节点以及所有子节点的树
    def get_tree(self):
        ret = []
        ret.append(self)
        for child in Group.objects.filter(parent=self):
            ret.extend(child.get_tree())
        return ret

    def get_province(self):
        ret = self
        while ret.group_type != 'province':
            ret = ret.parent
            if not ret:
                break
        return ret

    def get_town(self):
        parent = self.parent
        if parent.group_type == 'town':
            return parent, parent.name
        else:
            return None, ''

    # 获取school上级town的名称，如果是直属学校，town名称可能为空
    def get_town_name(self):
        parent = self.parent
        if parent.group_type == 'town':
            return parent.name
        else:
            return ''

    def get_country_name(self):
        parent = self.parent
        if parent.group_type == 'town':
            parent = parent.parent
        if parent.group_type == 'country':
            return parent.name
        else:
            return ''

    def save(self, *args, **kwargs):
        super(Group, self).save(*args, **kwargs)
        q = User.objects.all().values_list('uuid', flat=True)
        for uu in q:
            k = 'group-%s' % uu
            cache.delete(k)
        cache.delete('group-all')
        # Group表中数据更新的时候在Statistic表中应该对应的创建一个当前学期节点
        # 这里把节点的创建的触发方式放在了NewTerm和Term的模型中了

    def delete(self, *args, **kwargs):
        server_type = Setting.getvalue('server_type')
        if server_type == 'school':
            terms = Term.objects.all()
        else:
            terms = NewTerm.objects.all()
        for term in terms:
            try:
                Statistic.delete_one_item(term, self)
            except:
                logger.exception('')

        cache.delete('group-all')
        super(Group, self).delete(*args, **kwargs)

    class Meta:
        db_table = 'Group'


class GroupTB(models.Model):
    """从淘宝导入的省市区县乡镇街道"""

    group_id = models.IntegerField(db_column='group_id',
                                   primary_key=True)
    name = models.CharField(max_length=30, db_index=True)
    parent = models.ForeignKey('GroupTB', to_field='group_id',
                               db_column='parent_id',
                               related_name='child_set',
                               blank=True, null=True,
                               on_delete=models.SET_NULL,
                               db_index=True)

    def __unicode__(self):
        return '%d %s' % (self.group_id, self.name)

    class Meta:
        db_table = 'GroupTB'


class NewLessonType(BaseModel):
    """课程类型(小学, 初中, 高中)"""

    country = models.ForeignKey('Group', to_field='uuid', db_column='country_uuid', db_index=True)
    name = models.CharField(max_length=20, db_index=True)
    remark = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'NewLessonType'


# 2014-06-26 开课课程调整  校级 -> 区县
class NewLessonName(BaseModel):
    country = models.ForeignKey('Group', to_field='uuid', db_column='country_uuid', db_index=True)
    name = models.CharField(max_length=20, db_index=True)
    deleted = models.BooleanField(default=False)
    lesson_type = models.ManyToManyField('NewLessonType', through='NewLessonNameType')

    def __unicode__(self):
        return self.name

    class Meta:
        # unique_together = ('school', 'name')
        db_table = 'NewLessonName'


class NewLessonNameType(BaseModel):
    newlessonname = models.ForeignKey('NewLessonName', to_field='uuid', db_column='newlessonname_uuid', db_index=True)
    newlessontype = models.ForeignKey('NewLessonType', to_field='uuid', db_column='newlessontype_uuid', db_index=True)

    class Meta:
        db_table = 'NewLessonNameType'


class LessonName(BaseModel):
    school = models.ForeignKey('Group', to_field='uuid',
                               db_column='school_uuid',
                               db_index=True)
    name = models.CharField(max_length=20,
                            db_index=True)
    deleted = models.BooleanField(default=False)
    types = models.CharField(max_length=50, blank=True, null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'LessonName'
        unique_together = ('school', 'name')


class LessonPeriod(BaseModel):
    term = models.ForeignKey('Term', to_field='uuid',
                             db_column='term_uuid',
                             db_index=True)
    sequence = models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    @staticmethod
    def get_current_or_next_period():
        """获取本学期当前或下一节次"""
        now = datetime.datetime.now()
        t = Term.get_current_term_list()
        if not t:
            logger.debug(u'获取学年学期失败')
            return None
        try:
            lp = LessonPeriod.objects.filter(end_time__gte=now, term=t[0])
            lp = lp.order_by('start_time')
            if lp.exists():
                return lp[0]
            return None
        except:
            return None

    def __unicode__(self):
        return str(self.sequence)

    class Meta:
        db_table = 'LessonPeriod'
        unique_together = ('term', 'sequence')
        # ordering = ['-term__school_year', 'sequence']
        ordering = ['-term__start_date', 'sequence']


class LessonSchedule(BaseModel):
    class_uuid = models.ForeignKey('Class', to_field='uuid',
                                   db_column='class_uuid')
    lesson_period = models.ForeignKey('LessonPeriod', to_field='uuid',
                                      db_column='lesson_period_uuid')
    weekday = models.CharField(max_length=10, choices=WEEK_KEYS)
    lesson_name = models.ForeignKey('LessonName', to_field='uuid',
                                    db_column='lesson_name_uuid')

    def save(self, *args, **kwargs):
        super(LessonSchedule, self).save(*args, **kwargs)
        # 为班级节点创建一个对应的课程节点
        term = self.class_uuid.grade.term
        key = 'flag:%s-%s' % (self.class_uuid.pk, self.lesson_name.pk)
        has_created = cache.get(key)
        if not has_created:
            Statistic.create_one_item(term, self)
            cache.set(key, True, 30)

    def delete(self, *args, **kwargs):
        try:
            term = self.class_uuid.grade.term
            lesson = self.lesson_name
            parent = self.class_uuid
            Statistic.delete_one_item(term, lesson, parent)
        except Exception as e:
            logger.exception(e)
        super(LessonSchedule, self).delete(*args, **kwargs)

    class Meta:
        db_table = 'LessonSchedule'
        unique_together = ('class_uuid', 'lesson_period', 'weekday')


class LessonTeacher(BaseModel):
    """班级授课老师信息（包括计划课时）"""

    class_uuid = models.ForeignKey('Class', db_column='class_uuid')
    teacher = models.ForeignKey('Teacher', db_column='teacher_uuid')
    lesson_name = models.ForeignKey('LessonName', db_column='lesson_name_uuid')
    v = [validators.MaxValueValidator(2147483647),
         validators.MinValueValidator(0)]
    # 老师课程的计划上课节次
    schedule_time = models.IntegerField(default=0, validators=v)
    # 老师课程的实际上课节次
    finished_time = models.IntegerField(default=0, validators=v,
                                        blank=True,
                                        db_index=True)
    # 14.08.12 add
    # 老师课程的实际上课时间(秒)
    login_time = models.IntegerField(default=0, validators=v)

    @staticmethod
    def get_info(field='schedule_time', **kwargs):
        # 获取指定班级/教师/课程 的授课信息
        cls = kwargs.get('klass')
        teacher = kwargs.get('teacher')
        lesson = kwargs.get('lesson')
        term = kwargs.get('term')
        objs = LessonTeacher.objects.all()
        if cls:
            objs = objs.filter(class_uuid=cls)
        if teacher:
            if isinstance(teacher, Teacher):
                d = {'teacher': teacher}
            else:
                d = {'teacher__pk': teacher}
            objs = objs.filter(**d)
        if lesson:
            objs = objs.filter(lesson_name=lesson)
        if term:
            objs = objs.filter(class_uuid__grade__term=term)
        result = -1
        if field in ('schedule_time', 'finished_time', 'login_time'):
            result = objs.aggregate(x=Sum(field))['x']
            result = result and result or 0
        return result

    @staticmethod
    def calculate_total_teachers(instance):
        server_type = Setting.getvalue('server_type')
        c = instance.class_uuid.grade.term.school.parent.parent
        t = instance.class_uuid.grade.term.school.parent
        s = instance.class_uuid.grade.term.school
        l = instance.lesson_name
        g = instance.class_uuid.grade
        term = instance.class_uuid.grade.term
        if server_type == 'city':
            # TotalTeachersCountry
            obj, f = TotalTeachersCountry.objects.get_or_create(country_name=c.name,
                                                                term=term)
            q = LessonTeacher.objects.filter(class_uuid__grade__term=term)
            q = q.values('teacher').distinct()
            obj.total = q.count()
            obj.save()
        if server_type in ('city', 'country') \
                or Setting.getvalue('installed') != 'True':
            # TotalTeachersTown
            obj, f = TotalTeachersTown.objects.get_or_create(country_name=c.name,
                                                             town_name=t.name,
                                                             term=term)
            q = LessonTeacher.objects.filter(class_uuid__grade__term=term)
            q = q.values('teacher').distinct()
            obj.total = q.count()
            obj.save()
            # TotalTeachersSchool
            obj, f = TotalTeachersSchool.objects.get_or_create(country_name=c.name,
                                                               town_name=t.name,
                                                               school_name=s.name,
                                                               term=term)
            q = LessonTeacher.objects.filter(class_uuid__grade__term=term)
            q = q.values('teacher').distinct()
            obj.total = q.count()
            obj.save()
        if server_type in ('city', 'country', 'school'):
            # TotalTeachersLesson
            obj, f = TotalTeachersLesson.objects.get_or_create(country_name=c.name,
                                                               town_name=t.name,
                                                               school_name=s.name,
                                                               lesson_name=l.name,
                                                               term=term)
            q = LessonTeacher.objects.filter(class_uuid__grade__term=term,
                                             lesson_name__name=l.name)
            q = q.values('teacher').distinct()
            obj.total = q.count()
            obj.save()
            # TotalTeachersGrade
            obj, f = TotalTeachersGrade.objects.get_or_create(country_name=c.name,
                                                              town_name=t.name,
                                                              school_name=s.name,
                                                              grade_name=g.name,
                                                              term=term)
            q = LessonTeacher.objects.filter(class_uuid__grade=g)
            q = q.values('teacher').distinct()
            obj.total = q.count()
            obj.save()
        if server_type == 'school':
            # TotalTeachersLessonGrade
            obj, f = TotalTeachersLessonGrade.objects.get_or_create(town_name=t.name,
                                                                    school_name=s.name,
                                                                    lesson_name=l.name,
                                                                    grade_name=g.name,
                                                                    term=term)
            q = LessonTeacher.objects.filter(class_uuid__grade=g,
                                             lesson_name=l)
            q = q.values('teacher').distinct()
            obj.total = q.count()
            obj.save()

    def calculate_finished_time(self):
        q = TeacherLoginLog.objects.all()
        q = q.filter(term=self.class_uuid.grade.term, teacher=self.teacher,
                     grade_name=self.class_uuid.grade.name,
                     class_name=self.class_uuid.name,
                     lesson_name=self.lesson_name.name)
        n = q.count()
        if n != self.finished_time:
            self.finished_time = n
            self.save(force_update=True)
            logger.debug(
                'school: %s, teacher: %s, grade: %s, class: %s, lesson: %s, n: %s',
                self.class_uuid.grade.term.school.name,
                self.teacher.name, self.class_uuid.grade.name,
                self.class_uuid.name, self.lesson_name.name, n
            )

    @staticmethod
    def clean_bad_items():
        # 该方法对表中的不符规范的数据进行清理
        # 清理原则:
        # 1. 当前学期的被删除的教师 (后来想想这个还是给他留着吧)
        # 2. 当前学期没有产生过授课记录的教师
        _lst = Term.get_current_term_list()
        objs = LessonTeacher.objects.filter(class_uuid__grade__term__in=_lst)
        # deleted_objs = objs.filter(teacher__deleted=True)

        # 确保 finished_time 字段是最新的
        for o in objs:
            o.calculate_finished_time()
        objs.filter(finished_time=0).all().delete()

    def save(self, *args, **kwargs):
        super(LessonTeacher, self).save(*args, **kwargs)
        if 'force_update' in kwargs and kwargs['force_update'] is True:
            return
        LessonTeacher.calculate_total_teachers(self)
        # 为班级节点创建一个对应的课程节点
        term = self.class_uuid.grade.term
        Statistic.create_one_item(term, self)

    class Meta:
        db_table = 'LessonTeacher'
        unique_together = ('class_uuid', 'teacher', 'lesson_name')
        ordering = ['-class_uuid__grade__term__school_year',
                    'class_uuid__grade__term__term_type',
                    'class_uuid__grade__name',
                    'class_uuid__name',
                    'lesson_name']


class Node(models.Model):
    """用于管理下级服务器"""

    name = models.CharField(max_length=20, blank=True)
    host = models.CharField(max_length=255, blank=True)
    communicate_key = models.CharField(max_length=16, unique=True,
                                       db_index=True)
    activation_number = models.IntegerField(u'县级分配的激活可用终端数量', default=0, blank=True)
    session_key = models.CharField(max_length=128, blank=True)
    # 下级服务器传上来的最大ID
    last_upload_id = models.BigIntegerField(default=0,
                                            blank=True, null=True)
    # 其中，上级服务器已处理的最大ID
    last_save_id = models.BigIntegerField(default=0,
                                          blank=True, null=True)
    remark = models.CharField(max_length=180, blank=True)
    last_active_time = models.DateTimeField(default=None, null=True,
                                            blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_upload_time = models.DateTimeField(default=None, null=True,
                                            blank=True)
    db_version = models.IntegerField(default=0)
    sync_status = models.SmallIntegerField(default=0)

    def __unicode__(self):
        return str(self.pk)

    def get_use_number(self):
        """获取该node学校已使用的授权点数"""
        try:
            school = Group.objects.get(group_type='school', name=self.name)
            terms = Term.get_current_term_list(school)
            return Class.objects.filter(grade__term__in=terms).count()
        except Exception:
            return 0

    def save(self, *args, **kwargs):
        super(Node, self).save(*args, **kwargs)
        cache.delete('group-all')

    def delete(self, *args, **kwargs):
        try:
            group = Group.objects.get(name=self.name)
            group.delete()
        except Exception as e:
            logger.debug(str(e))
        super(Node, self).delete(*args, **kwargs)

    class Meta:
        db_table = 'Node'


class Resource(BaseModel):
    resource_from = models.CharField(max_length=50, db_index=True)
    resource_type = models.CharField(max_length=20,
                                     choices=RESOURCE_TYPES,
                                     db_index=True)
    remark = models.CharField(max_length=180, blank=True, db_index=True)

    def __unicode__(self):
        return '%s %s' % (self.resource_from, self.resource_type)

    class Meta:
        db_table = 'Resource'


# 2014-06-26 资源来源  校级 -> 区县
class ResourceFrom(BaseModel):
    country = models.ForeignKey('Group', to_field='uuid', db_column='country_uuid', db_index=True)
    value = models.CharField(max_length=50, db_index=True)
    remark = models.CharField(max_length=180, blank=True)

    def __unicode__(self):
        return self.value

    class Meta:
        unique_together = ('country', 'value')


# 2014-06-26 资源类型  校级 -> 区县
class ResourceType(BaseModel):
    country = models.ForeignKey('Group', to_field='uuid', db_column='country_uuid', db_index=True)
    value = models.CharField(max_length=20, db_index=True)
    remark = models.CharField(max_length=180, blank=True)

    def __unicode__(self):
        return self.value

    class Meta:
        unique_together = ('country', 'value')


class Role(BaseModel):
    name = models.CharField(max_length=100)
    remark = models.CharField(max_length=180, blank=True, db_index=True)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'Role'


class RolePrivilege(BaseModel):
    role = models.ForeignKey('Role', to_field='uuid',
                             db_column='role_uuid',
                             db_index=True)
    privilege = models.CharField(max_length=50)

    class Meta:
        db_table = 'RolePrivilege'


class Setting(BaseModel):
    name = models.CharField(max_length=100, db_index=True)
    value = models.CharField(max_length=1024, blank=True)

    def __unicode__(self):
        return '%s %s' % (self.name, self.value)

    @staticmethod
    def get_node_id_from_top(host, port, key):
        # 根据 host port key 取得该校级服务器在上级服务器中的node_id
        try:
            url = 'http://%s:%s/api/sync-server/get_node_id/' % (host, port)
            data = {'key': key}
            conn = urllib2.urlopen(url, urllib.urlencode(data), timeout=5).read()
            node_id = json.loads(conn)['data']['node_id']
        except:
            node_id = None

        return node_id

    @staticmethod
    def getvalue(name):
        try:
            obj = Setting.objects.get(name=name)
            return obj.value
        except:
            # sync_node_id是后加上的，可能有的学校没有这个setting字段值
            if name == 'sync_node_id':
                # 获取上级服务器的HOST，PORT，KEY
                host = Setting.getvalue('sync_server_host')
                port = Setting.getvalue('sync_server_port')
                key = Setting.getvalue('sync_server_key')
                node_id = Setting.get_node_id_from_top(host, port, key)

                if node_id:
                    # 创建
                    obj, c = Setting.objects.get_or_create(name='sync_node_id')
                    obj.value = node_id
                    obj.save()
                    return node_id
            return None

    @staticmethod
    def setval(name, value, key=None):
        """用于本地加密保存Setting表中的数据"""
        if not key:
            # 默认根据机器码计算得到16位salt进行加密
            mac = uuid.UUID(int=uuid.getnode()).hex[-12:].upper()
            if constants.ACTIVATE_DIRECTLY:
                mac = 'abcdefghijkl'
            key = str_util._salt(16, mac)
        value, key = str_util.encode(value, key=key)
        # 存储前先bs64一下, 防止由于数据库字符编码设定引起的保存失败的问题
        obj, is_new = Setting.objects.get_or_create(
            name=name,
            defaults={'value': base64.b64encode(value)}
        )
        if not is_new:
            obj.value = base64.b64encode(value)
            obj.save()
        return obj

    @staticmethod
    def getval(name, key=None):
        """同setval的用法相反"""
        def _getval(value, mac):
            try:
                key = str_util._salt(16, mac)
                return str_util.decode(base64.b64decode(obj.value), key=key)
            except:
                logger.exception('')

        try:
            obj = Setting.objects.get(name=name)
            if not key:
                macs = get_macs()
                mac = uuid.UUID(int=uuid.getnode()).hex[-12:].upper()
                macs.insert(0, mac)
                if constants.ACTIVATE_DIRECTLY:
                    macs.insert(0, 'abcdefghijkl')

            for mac in macs:
                value = _getval(obj.value, mac)
                if value and isinstance(value, dict):
                    return value

            else:
                return _getval(obj.value, key)
        except Exception as e:
            logger.debug(e)
            return

    class Meta:
        db_table = 'Setting'
        # unique_together = ['name', 'value']

_not_update_on_change_key = 'do-not-update-statistic-now'
# cache.set(_not_update_on_change_key, True, 100)
_NOT_UPDATE_ON_CHANGE = cache.get(_not_update_on_change_key)
# _NOT_UPDATE_ON_CHANGE = True
_N = 0


class Statistic(models.Model):
    """用于统计分析功能的表"""

    GROUP_TYPES2 = (
        ('province', 'province'),
        ('city', 'city'),
        ('country', 'country'),
        ('town', 'town'),
        ('school', 'school'),
        ('grade', 'grade'),
        ('class', 'class'),
        ('lesson', 'lesson'),
        ('teacher', 'teacher'),
        # TODO
        # 加入教师类型的节点, 将校级按班级教师课程统计和按教师统计一并纳入
    )
    FULL_LST = (
        'province', 'city', 'country', 'town', 'school', 'grade', 'class',
        'lesson', 'teacher',
    )
    term = models.CharField(max_length=40, blank=True, null=True)  # NewTerm/Term

    school_year = models.CharField(max_length=20, db_index=True)
    term_type = models.CharField(max_length=20, choices=TERM_TYPES, db_index=True)
    key = models.CharField(max_length=400, blank=True)
    name = models.CharField(max_length=100, db_index=True)
    type = models.CharField(max_length=20, choices=GROUP_TYPES2, db_index=True)
    parent = models.ForeignKey('self', related_name='child_set', blank=True, null=True)

    class_count = models.IntegerField(default=0, blank=True)  # 班级总数/开课班级总数
    teach_count = models.IntegerField(default=0, blank=True)  # 授课次数/课程授课次数
    teach_time = models.IntegerField(default=0, blank=True)  # 授课时长/课程授课时长
    teacher_num = models.IntegerField(default=0, blank=True)  # 授课人数/课程授课人数

    last_update_count = models.DateTimeField(default=datetime.datetime.now)
    last_update_time = models.DateTimeField(default=datetime.datetime.now)
    last_update_num = models.DateTimeField(default=datetime.datetime.now)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = [('school_year', 'term_type')]

    def __unicode__(self):
        return str(self.pk)

    # 基础数据增删部分
    @staticmethod
    def init_all(term=None):
        """用来初始化/更新所有的节点, 范围为历史/指定学期的数据"""
        def _loop(term, obj, parent=None):
            if isinstance(obj, Group) and obj.group_type == 'school':
                # 学校节点在历史学期中未创建Term副本的时候, 不予创建该节点
                # 创建的话则会影响到统计分析中历史学期中的学校达标率
                terms = Term.objects.filter(
                    school_year=term.school_year,
                    term_type=term.term_type,
                    school=obj
                )
                if not terms.exists():
                    return
            o = Statistic.create_one_item(term, obj, parent)
            if isinstance(obj, Group) and hasattr(obj, 'child_set') and obj.child_set.all().exists():
                for i in obj.child_set.all():
                    _loop(term, i, o)

            if o and o.type == 'school':
                terms = Term.objects.filter(
                    school_year=term.school_year,
                    term_type=term.term_type,
                    school=obj
                )
                for t in terms:
                    for g in t.grade_set.all().exclude(number=13).order_by('number'):
                        gg = _loop(t, g, o)
                        for c in g.class_set.all().order_by('number'):
                            cc = _loop(t, c, gg)
                            # cc.leave_me_alone()
                            # lessons = c.lessonschedule_set.all()
                            # lessons = lessons.values('lesson_name').distinct()
                            # lessons = LessonName.objects.filter(pk__in=lessons)
                            # 课程节点可以通过LessonTeacher表获取, 受限于该表的频繁变动特性
                            # 这里不采用LessonTeacher获取, 而是直接通过LessonName表, TeacherLoginLog表
                            # LessonSchedule表来获取
                            lessons = t.school.lessonname_set.all()
                            _lst = t.school.school_teacherloginlog_set.values('lesson_name').distinct()
                            lessons = lessons.filter(name__in=_lst)
                            for ls in lessons:
                                Statistic.create_one_item(t, ls, cc)
                                lesson_teachers = c.lessonteacher_set.filter(lesson_name=ls)
                                for lt in lesson_teachers:
                                    Statistic.create_one_item(t, lt)
            return o

        server_type = Setting.getvalue('server_type')
        if not term:
            if server_type == 'school':
                terms = Term.objects.all()
            else:
                terms = NewTerm.objects.all()
        else:
            terms = [term, ]

        provinces = Group.objects.filter(group_type='province')
        for t in terms:
            for o in provinces:
                _loop(t, o)

            Setting.objects.get_or_create(
                name='task-init-statictic-term',
                value=t.pk
            )
        logger.debug('init_all finished')

    @staticmethod
    def create_one(term, obj, parent=None, **kwargs):
        """创建一个基本节点并且更新统计数据的元方法, 其他的创建方法调用该方法"""
        # 1. 获取基本信息
        if isinstance(obj, Group):
            node_type = obj.group_type.lower()
            parent_obj = kwargs.get('parent_obj', obj.parent)
        elif isinstance(obj, Grade):
            node_type = 'grade'
            parent_obj = kwargs.get('parent_obj', obj.term.school)
        elif isinstance(obj, Class):
            node_type = 'class'
            parent_obj = obj.grade
        elif isinstance(obj, LessonSchedule):
            node_type = 'lesson'
            parent_obj = kwargs.get('parent_obj', obj.class_uuid)
            obj = obj.lesson_name
        # create_one 内部调用: LessonName
        elif isinstance(obj, LessonName):
            node_type = 'lesson'
            parent_obj = kwargs.get('parent_obj')
            if not parent_obj and not parent:
                logger.debug('we want to get a parent')
                return None, False
        elif isinstance(obj, LessonTeacher):
            node_type = 'teacher'
            parent_obj = kwargs.get('parent_obj', obj.lesson_name)
            grandpa_obj = kwargs.get('grandpa_obj', obj.class_uuid)
            obj = obj.teacher
        else:
            return None, False

        # 2.创建节点
        if node_type == 'province':
            # 省级没有上级节点, 直接创建
            o, is_new = Statistic.objects.get_or_create(
                school_year=term.school_year,
                term_type=term.term_type,
                key=obj.pk,
                name=obj.name,
                type=node_type,
                defaults={
                    'term': term.pk,
                }
            )
        else:
            if not parent:
                # 后面去过teacher节点还有子节点, 那么以此类推的可能还会有grand_grandpa
                if node_type == 'teacher':
                    try:
                        # lesson
                        parent = Statistic.objects.get(
                            school_year=term.school_year,
                            term_type=term.term_type,
                            key=parent_obj.pk,
                            parent__key=grandpa_obj.pk
                        )
                    except Statistic.DoesNotExist:
                        parent = Statistic.create_one(term, parent_obj, parent_obj=grandpa_obj)[0]
                    except Exception as e:
                        logger.exception(e)
                        return None, False
                else:
                    try:
                        parent = Statistic.objects.get(
                            school_year=term.school_year,
                            term_type=term.term_type,
                            key=parent_obj.pk
                        )
                    except Statistic.DoesNotExist:
                        parent = Statistic.create_one(term, parent_obj)[0]
                    except Exception as e:
                        logger.exception(e)
                        return None, False

                if not parent:
                    # 省级以外的没有parent的节点是不允许的
                    return None, False

            o, is_new = Statistic.objects.get_or_create(
                school_year=term.school_year,
                term_type=term.term_type,
                key=obj.pk,
                name=obj.name,
                type=node_type,
                parent=parent,
                defaults={
                    'term': term.pk,
                }
            )

        # 3.数据更新
        if is_new and settings.CONF.server.update_statistic_onchange:
            o.update_on_change()
        return o, is_new

    @staticmethod
    def create_one_item(term, obj, parent=None):
        """新增省市区县校年级班级节点的时候调用该方法在Statistic表中创建节点"""
        try:
            if isinstance(obj, Group):
                o, is_new = Statistic.create_one(term, obj, parent)
                return o

            elif isinstance(obj, Grade):
                if obj.number == 13:
                    return
                g = Statistic.create_one(term, obj, parent)[0]
                return g

            elif isinstance(obj, Class):
                if obj.grade.number == 13:
                    return
                c = Statistic.create_one(term, obj, parent)[0]
                return c
            elif isinstance(obj, LessonName):
                l = Statistic.create_one(term, obj, parent)[0]
                return l
            # LessonSchedule 变动的时候触发更新
            elif isinstance(obj, LessonSchedule):
                l = Statistic.create_one(term, obj, parent)[0]
                return l
            # LessonTeacher 变动的时候触发更新
            elif isinstance(obj, LessonTeacher):
                t = Statistic.create_one(term, obj, parent)[0]
                return t
        except Exception as e:
            logger.exception(e)

    @staticmethod
    def delete_one_item(term, obj, parent=None):
        """删除指定节点并更新上级节点"""
        targets = Statistic.objects.filter(
            school_year=term.school_year,
            term_type=term.term_type,
            key=obj.pk
        )
        if parent:
            targets = targets.filter(parent__key=parent.pk)
        for target in targets:
            parent = target.parent
            logger.debug('delete_one_item: %s', target.name)
            target.delete()
            if parent:
                parent.update_on_change()

    def leave_me_alone(self, node_type='lesson'):
        them = self.get_descendants(node_type)
        if node_type == 'lesson':
            # 授课次数不为0的说明以前上过课, 所以条目不应该删除
            them = them.exclude(teach_count__gt=0)
        them.all().delete()

    # 数据计算/更新部分
    def cala(self, cala_item='class_count', force_flush=False):
        """基础更新方法, 其他更新方法调用该方法更新条目的统计字段"""
        # 可以直接通过下级求和的字段: class_count, teach_num, teach_count,
        # 不可以直接求和的字段: teacher_num
        if cala_item == 'teacher_num':
            if self.type == 'teacher':
                result = 1
            else:
                result = self.get_descendants('teacher').values('key').distinct().count()

        elif cala_item == 'class_count':
            if self.type in ('teacher', 'lesson', 'class'):
                result = 1
            else:
                result = self.child_set.aggregate(x=Sum(cala_item))['x']
        elif cala_item == 'teach_time':
            if self.type == 'teacher':
                d = {
                    # 'term_school_year': self.school_year,
                    # 'term_type': self.term_type,
                    'class_uuid': self.parent.parent.key,
                    'lesson_name': self.parent.name,
                    'teacher': self.key,
                }
                objs = TeacherLoginLog.objects.filter(**d)
                result = objs.aggregate(x=Sum('teacherlogintime__login_time'))['x']
            else:
                result = self.child_set.aggregate(x=Sum(cala_item))['x']
        elif cala_item == 'teach_count':
            if self.type == 'teacher':
                d = {
                    # 'term_school_year': self.school_year,
                    # 'term_type': self.term_type,
                    'class_uuid': self.parent.parent.key,
                    'lesson_name': self.parent.name,
                    'teacher': self.key,
                }
                result = TeacherLoginLog.objects.filter(**d).count()
            elif self.type == 'lesson':
                d = {
                    # 'term_school_year': self.school_year,
                    # 'term_type': self.term_type,
                    # 'town_name': self.parent.parent.parent.parent.name,
                    # 'school_name': self.parent.parent.parent.name,
                    # 'grade_name': self.parent.parent.name,
                    # 'class_name': self.parent.name,
                    'class_uuid': self.parent.key,
                    'lesson_name': self.name,
                }
                result = TeacherLoginLog.objects.filter(**d).count()
            elif self.type == 'class':
                d = {
                    'class_uuid': self.key,
                }
                result = TeacherLoginLog.objects.filter(**d).count()
            else:
                result = self.child_set.aggregate(x=Sum(cala_item))['x']

        result = result and result or 0
        # old_value = getattr(self, cala_item, 0)
        # if result == old_value:
        #     return
        setattr(self, cala_item, result)
        if cala_item in ('teach_count', 'teach_time', 'teacher_num'):
            now = datetime.datetime.now()
            setattr(self, 'last_update_%s' % cala_item.split('_')[1], now)
        self.save()

        if force_flush and self.parent:
            self.parent.cala(cala_item, force_flush)

    @staticmethod
    def update_all(term=None):
        logger.debug('begin to update: %s', datetime.datetime.now().strftime('%H:%M:%S %f'))
        server_type = Setting.getvalue('server_type')
        _lst = list(Statistic.FULL_LST)
        _lst.reverse()
        n = 0
        if not term:
            if server_type == 'school':
                terms = Term.objects.all()
            else:
                terms = NewTerm.objects.all()
        else:
            terms = [term, ]
        for term in terms:
            base_objs = Statistic.objects.filter(
                school_year=term.school_year,
                term_type=term.term_type
            )
            for node_type in _lst:
                objs = base_objs.filter(type=node_type)
                for o in objs:
                    n += 1
                    o.update_me()
                    if n % 200 == 0:
                        logger.debug('update: %s', n)

        logger.debug('update all finished %s', datetime.datetime.now().strftime('%H:%M:%S %f'))
        cache.set(_not_update_on_change_key, False, 3)

    def update_me(self):
        try:
            self.cala('class_count')
            self.cala('teach_count')
            self.cala('teach_time')
        except:
            logger.debug('Statistic Error: %s' % self.pk)
        # self.cala('teacher_num')

    def update_on_change(self):
        self.update_me()
        if self.parent:
            self.parent.update_me()

    @staticmethod
    def update_on_loginlog(obj):
        # log的class_uuid, grade_uuid等字段可能已经为NULL了(被删了)
        # 班级被删除后该节点(通过pk区分)的流水记录将不会在授课次数中予以统计
        if obj.class_uuid:  # and obj.lesson_name and obj.teacher
            try:
                target = Statistic.objects.get(
                    key=obj.teacher.pk,
                    parent__name=obj.lesson_name,
                    parent__parent__key=obj.class_uuid
                )
            except Statistic.DoesNotExist:
                if hasattr(obj, 'lesson_teacher') and obj.lesson_teacher:
                    target = Statistic.create_one(obj.term, obj.lesson_teacher)
                else:
                    logger.warning(u'Warning: we want to create but missing the lesson_teacher field from log: %s' % obj.pk)
                return
            except Exception as e:
                logger.exception(e)
                return
            while target:
                target.cala('teach_count')
                target = target.parent
        else:
            logger.debug('Bad Items: loginlog - %s' % obj.pk)

    @staticmethod
    def update_on_logintime(obj):
        log = obj.teacherloginlog
        if log.class_uuid:  # and obj.lesson_name and obj.teacher
            try:
                target = Statistic.objects.get(
                    key=log.teacher.pk,
                    parent__name=log.lesson_name,
                    parent__parent__key=log.class_uuid
                )
            except Statistic.DoesNotExist:
                if log.lesson_teacher:
                    target = Statistic.create_one(log.term, log.lesson_teacher)
                else:
                    logger.debug('Warning: we want to create but missing the lesson_teacher field from log: %s' % log.pk)
                return
            except:
                logger.exception('')
                return

            while target:
                target.cala('teach_time')
                target = target.parent
        else:
            logger.debug('Bad Items: logintime - %s' % obj.pk)

    # 统计结果获取
    def count_child(self, node_type='class'):
        # 统计该节点下辖的子孙的数目(默认统计班级数)
        lst = Statistic.FULL_LST
        if node_type not in lst:
            return -1
        elif lst.index(self.type) > lst.index(node_type):
            return 0
        elif self.type == node_type:
            return 1
        else:
            return self.get_descendants(node_type).count()

    @staticmethod
    def get_child(obj):
        # _lst = Statistic.FULL_LST
        if isinstance(obj, Statistic):
            return obj.child_set.all()

        if isinstance(obj, Group):
            node_type = obj.group_type.lower()
            term = obj.term_set.get(
                school_year=obj.school_year,
                term_type=obj.term_type
            )
        elif isinstance(obj, Grade):
            node_type = 'grade'
            term = obj.term
        elif isinstance(obj, Class):
            node_type = 'class'
            term = obj.grade.term
        else:
            return Statistic.objects.none()
        try:
            me = Statistic.objects.get(
                school_year=term.school_year,
                term_type=term.term_type,
                key=obj.pk
            )
        except Statistic.DoesNotExist:
            if node_type == 'school':
                parent = obj.parent
            elif node_type == 'grade':
                parent = obj.term.school
            elif node_type == 'class':
                parent = obj.grade
            me, is_new = Statistic.create_one(term, obj, parent)
            return Statistic.objects.none()
        except:
            logger.exception('')
            return Statistic.objects.none()

        return me.child_set.all()

    def get_descendants(self, node_type='class'):
        """获取指定类型的子节点, 默认获取下一级节点"""
        lst = self.FULL_LST
        n = node_type in lst and [(lst.index(node_type) - lst.index(self.type) - 1)] or [-1]
        if n[0] < 0:
            return Statistic.objects.none()

        parent_key = 'parent' + '__parent' * n[0]
        d = {
            parent_key: self,
            'school_year': self.school_year,
            'term_type': self.term_type,
            'type': node_type,
        }
        objs = Statistic.objects.filter(**d)
        return objs

    @staticmethod
    def get_items_descendants(objs, node_type='class'):
        descendants = Statistic.objects.none()
        for o in objs:
            descendants |= o.get_descendants(node_type)
        return descendants

    @staticmethod
    def get_schedule_time(schedule_time=None):
        # 计划课时以本服务器中记录的数据为准
        if schedule_time:
            return schedule_time
        try:
            server_type = Setting.getvalue('server_type')
            if server_type == 'school':
                schedule_time = Term.get_current_term_list()[0].schedule_time
            else:
                schedule_time = NewTerm.get_current_term().schedule_time
        except:
            schedule_time = None
        return schedule_time

    @staticmethod
    def get_filter_condition(d, node_type, term=None):
        """查询此表的时候, 可以将request.REQUEST传入, 格式化为针对本表的查询条件"""
        lst = Statistic.FULL_LST
        if node_type not in lst:
            return {}
        conditions = {'type': node_type}
        start_date = d.get('start_date')
        end_date = d.get('end_date')
        if start_date and end_date and not term:
            # TODO
            # 这里的term获取并不严谨
            try:
                term = Term.objects.filter(start_date__lte=start_date, end_date__gte=end_date)[0]
            except:
                pass
        school_year = term and term.school_year or d.get('school_year')
        term_type = term and term.term_type or d.get('term_type')
        if school_year:
            conditions['school_year'] = school_year
        if term_type:
            conditions['term_type'] = term_type
        for k in lst:
            n = lst.index(node_type) - lst.index(k)
            if n < 0:
                break
            value = d.get('%s_name' % k, d.get(k))
            # 针对参数命名并没有绝对的统一风格, 这里这样判断一下
            if value:
                if len(value.split('-')) == 5 and len(value.split('-')[-1]) == 12:
                    suffix = 'key'  # uuid
                else:
                    suffix = 'name'
                conditions['parent__' * n + suffix] = value
        return conditions

    @staticmethod
    def rate_them(descendants, schedule_time=None):
        schedule_time = Statistic.get_schedule_time(schedule_time)
        if not schedule_time:
            logger.debug('Error while trying to get schedule time')
            return '0.00%'
        lst = [1 if o.class_count > 0 and o.teach_count >= schedule_time * o.class_count else 0 for o in descendants]
        if DEBUG:
            rate = '%.2f%%(%s/%s)' % (
                (sum(lst) * 100.0 / (len(lst) and len(lst) or 1)),
                sum(lst), len(lst)
            )
        else:
            rate = '%.2f%%' % (sum(lst) * 100.0 / (len(lst) and len(lst) or 1))
        return rate

    def rate_me(self, child_node_type, schedule_time=None):
        descendants = self.get_descendants(child_node_type)
        return Statistic.rate_them(descendants, schedule_time)

    @staticmethod
    def get_rate_info(term, rate_obj_pk):
        """按自然时间查询的时候, 学校达标率和班级达标率就从Statistic表中获取"""
        o = Statistic.objects.filter(
            school_year=term.school_year,
            term_type=term.term_type,
            key=rate_obj_pk
        )
        # Tips
        # 理论上来说县级的schedule_time应该从NewTerm中获取, 但是这样就会有一点
        # 不一致, 所以这里还是等Term表数据同步后上传更新来实现一致.
        # 所以这里schedule_time字段就传入进去
        if o.exists() and o.count() == 1:
            return {
                'finished_rate_school': o[0].rate_me('school', term.schedule_time),
                'finished_rate_class': o[0].rate_me('class', term.schedule_time)
            }
        return {
            'finished_rate_school': '0.00%',
            'finished_rate_class': '0.00%',
            '# debug': {'exists': o.exists(), 'objs-len': o.count()}
        }


class SyllabusGrade(CountryToSchoolBaseModel):
    """年级"""

    school_year = models.CharField(max_length=20,
                                   db_index=True)
    term_type = models.CharField(max_length=20,
                                 choices=TERM_TYPES,
                                 db_index=True)  # 春季学期/秋季学期
    grade_name = models.CharField(max_length=20, db_index=True)
    in_use = models.BooleanField(help_text='是否已启用')


class SyllabusGradeLesson(CountryToSchoolBaseModel):
    """年级的课程教材"""

    syllabus_grade = models.ForeignKey('SyllabusGrade')
    lesson_name = models.CharField(max_length=20, db_index=True, help_text='语文，数学...')
    publish = models.CharField(max_length=20, help_text='人民教育出版社，湖北教育出版社', blank=True)
    edition = models.CharField(max_length=20, help_text='人教版，鄂教版...')
    bookversion = models.CharField(max_length=20, help_text='200301-2(2003年1月第2版)，200202-5(2002年2月第5版)...', blank=True)
    volume = models.CharField(max_length=10, blank=True, null=True)
    #   由于历史原因，以下两个字段本来是保存host和url的，现在改为：
    #   host指定为http://oebbt-cover.qiniudn.com
    #   下面两个字段用来保存封面截图和出版信息截图的url key
    picture_host = models.CharField(max_length=180, help_text='教材封面')
    picture_url = models.CharField(max_length=180, help_text='教材CIP截图')
    remark = models.CharField(max_length=180, blank=True)
    in_use = models.BooleanField(default=False, help_text='是否已启用')


class SyllabusGradeLessonContent(CountryToSchoolBaseModel):
    """教材对应的大纲。注：大纲最多只有两级目录"""

    syllabus_grade_lesson = models.ForeignKey('SyllabusGradeLesson')
    parent = models.ForeignKey('self', blank=True, null=True,
                               help_text='上级目录')
    # seq = models.IntegerField(help_text='一级目录序号')
    seq = models.FloatField(help_text='一级目录序号', blank=True, null=True)
    # subseq = models.IntegerField(help_text='二级目录序号')
    subseq = models.FloatField(help_text='二级目录序号', blank=True, null=True)
    title = models.CharField(max_length=100, help_text='教材大纲标题')


class SyncLog(models.Model):
    created_at = BigAutoField(primary_key=True)
    operation_type = models.CharField(max_length=10)
    operation_content = models.TextField(default='', blank=True)

    # 全局不处理
    _except_classes = ['GroupTB', 'Node',
                       'Resource', 'Role', 'RolePrivilege',
                       'Setting', 'SyncLog', 'Token',
                       'User', 'UserPermittedGroup',
                       'MigrationHistory']

    # 仅校级不处理
    _except_classes_only_school = ['ResourceFrom', 'ResourceType']

    @staticmethod
    def add_log(instance, log_type, prepare_func=None):
        try:
            if instance.__class__.__name__ in SyncLog._except_classes:
                return
            if instance.__class__.__name__ in SyncLog._except_classes_only_school:
                if Setting.getvalue('server_type') == 'school':
                    logger.debug('server_type != school')
                    return

            data = serializers.serialize('json', [instance, ])
            if prepare_func:
                data = prepare_func(data)
            SyncLog.objects.create(operation_type=log_type, operation_content=data)
        except Exception as e:
            logger.exception(e)

    class Meta:
        db_table = 'SyncLog'


class SyncLogTemp(models.Model):
    """下级服务器同步上来的数据，先保存在临时表里，后续再用另外的线程处理"""

    id = BigAutoField(primary_key=True)
    node = models.ForeignKey('Node')
    data = models.TextField()  # 下级服务器POST上来的base64(bz2(data))


def _create_teacher_sequence():
    max_seq = 1
    try:
        max_seq = Teacher.objects.latest('sequence').sequence + 1
    except models.ObjectDoesNotExist:
        pass

    return max_seq


class Teacher(BaseModel):
    sequence = models.IntegerField(default=_create_teacher_sequence)
    name = models.CharField(max_length=100,
                            help_text='姓名',
                            db_index=True)
    password = models.CharField(max_length=128, blank=True)
    sex = models.CharField(max_length=20, default='male', choices=SEX)
    edu_background = models.CharField(max_length=50)
    birthday = models.DateField()
    title = models.CharField(max_length=50, blank=True,
                             help_text='教师职称')
    mobile = models.CharField(max_length=20, blank=True)
    qq = models.CharField(max_length=20, blank=True)
    remark = models.CharField(max_length=180, blank=True)
    register_at = models.DateField(auto_now_add=True)
    deleted = models.BooleanField(default=False)
    school = models.ForeignKey('Group', to_field='uuid',
                               related_name='school_teacher_set',
                               limit_choices_to={'group_type': 'school'},
                               db_column='school_uuid', db_index=True)

    def __unicode__(self):
        return self.name

    def __iter__(self):
        _dict = self.to_dict(exclude=['password'])
        return _dict.iteritems()

    class Meta:
        db_table = 'Teacher'
        unique_together = ('name', 'birthday', 'school')
        ordering = ['sequence']
        verbose_name = _('Teacher')
        verbose_name_plural = _('Teacher')


class TeachLog(BaseModel):
    """教师登录记录"""

    # 教师
    teacher_name = models.CharField(max_length=100)
    # 课程名
    lesson_name = models.CharField(max_length=20)
    # 学校学期班级
    province_name = models.CharField(max_length=100)
    city_name = models.CharField(max_length=100)
    # 对于直属学校，country和town可能为空
    country_name = models.CharField(max_length=100, blank=True)
    town_name = models.CharField(max_length=100, blank=True)
    school_name = models.CharField(max_length=100)
    term_school_year = models.CharField(max_length=20)
    term_type = models.CharField(max_length=20)
    term_start_date = models.DateField()
    term_end_date = models.DateField()
    grade_name = models.CharField(max_length=20)
    class_name = models.CharField(max_length=20)
    # 作息时间
    lesson_period_sequence = models.IntegerField()
    lesson_period_start_time = models.TimeField()
    lesson_period_end_time = models.TimeField()
    # 课程表
    weekday = models.CharField(max_length=10, choices=WEEK_KEYS)
    # ForeignKey
    teacher = models.ForeignKey('Teacher', to_field='uuid',
                                db_column='teacher_uuid',
                                related_name='%(class)s_set',
                                null=True,
                                on_delete=models.SET_NULL)
    province = models.ForeignKey('Group', to_field='uuid',
                                 db_column='province_uuid',
                                 related_name='province_%(class)s_set')
    city = models.ForeignKey('Group', to_field='uuid',
                             db_column='city_uuid',
                             related_name='city_%(class)s_set')
    country = models.ForeignKey('Group', to_field='uuid',
                                db_column='country_uuid',
                                null=True,
                                related_name='country_%(class)s_set')
    town = models.ForeignKey('Group', to_field='uuid',
                             db_column='town_uuid',
                             null=True,
                             related_name='town_%(class)s_set')
    school = models.ForeignKey('Group', to_field='uuid',
                               db_column='school_uuid',
                               related_name='school_%(class)s_set')
    term = models.ForeignKey('Term', to_field='uuid',
                             db_column='term_uuid',
                             null=True,
                             on_delete=models.SET_NULL,
                             db_index=True)
    grade = models.ForeignKey('Grade', to_field='uuid',
                              db_column='grade_uuid',
                              null=True,
                              on_delete=models.SET_NULL,
                              related_name='grade_%(class)s_set')
    class_uuid = models.ForeignKey('Class', to_field='uuid',
                                   db_column='class_uuid',
                                   null=True,
                                   on_delete=models.SET_NULL,
                                   related_name='class_%(class)s_set')
    lesson_period = models.ForeignKey('LessonPeriod', to_field='uuid',
                                      db_column='lesson_period_uuid',
                                      null=True,
                                      on_delete=models.SET_NULL)
    lesson_teacher = models.ForeignKey('LessonTeacher', to_field='uuid',
                                       db_column='lesson_teacher_uuid',
                                       null=True,
                                       on_delete=models.SET_NULL)
    created_at = models.DateTimeField()

    @staticmethod
    def log_teacher(log_type, teacher=None, lesson_name=None,
                    class_uuid=None, lesson_period=None,
                    resource_from='', resource_type='',
                    lessoncontent=None,
                    created_at=None, weekday=None):
        try:
            if log_type == 'login':
                m = TeacherLoginLog
            elif log_type == 'absent':
                m = TeacherAbsentLog
            else:
                return
            if Setting.getvalue('server_type') != 'school':
                return
            province = Group.objects.get(group_type='province')
            city = Group.objects.get(group_type='city')
            try:
                country = Group.objects.get(group_type='country')
                country_name = country.name
            except:
                country = None
                country_name = ''
            try:
                town = Group.objects.get(group_type='town')
                town_name = town.name
            except:
                town = None
                town_name = ''
            school = Group.objects.get(group_type='school')
            term = Term.get_current_term_list(school)[0]
            now = datetime.datetime.now()
            try:
                lt = LessonTeacher.objects.get(class_uuid=class_uuid,
                                               lesson_name__name=lesson_name)
            except:
                lt = None
            if not created_at:
                if log_type == 'login':
                    created_at = now
            if not weekday:
                weekday = now.strftime('%a').lower()
            ret = m(teacher_name=teacher.name, lesson_name=lesson_name,
                    province_name=province.name, city_name=city.name,
                    country_name=country_name, town_name=town_name,
                    school_name=school.name, term_school_year=term.school_year,
                    term_type=term.term_type, term_start_date=term.start_date,
                    term_end_date=term.end_date,
                    grade_name=class_uuid.grade.name,
                    class_name=class_uuid.name,
                    lesson_period_sequence=lesson_period.sequence,
                    lesson_period_start_time=lesson_period.start_time,
                    lesson_period_end_time=lesson_period.end_time,
                    weekday=weekday, teacher=teacher,
                    province=province, city=city, country=country, town=town,
                    school=school, term=term, grade=class_uuid.grade,
                    class_uuid=class_uuid, lesson_period=lesson_period,
                    lesson_teacher=lt, created_at=created_at)
            if log_type == 'login':
                ret.resource_from = resource_from
                ret.resource_type = resource_type
            ret.save(force_insert=True)
            if log_type == 'login':
                # 初始化上课时间temp
                o, is_new = TeacherLoginTimeTemp.objects.get_or_create(
                    teacherloginlog=ret,
                    login_time=0,
                    last_login_datetime=now
                )
                # 大纲绑定上课信息
                if lessoncontent:
                    if lessoncontent != -1:
                        try:
                            obj = SyllabusGradeLessonContent.objects.get(id=lessoncontent)
                            TeacherLoginLogLessonContent(teacherloginlog=ret, lessoncontent=obj, title=obj.title).save()
                        except Exception as e:
                            logger.exception(e)
                # 更新课程表，如无则新建，有就如果变化则更新
                try:
                    ln_obj = LessonName.objects.get(school=school, name=lesson_name, deleted=False)
                    try:
                        ls = LessonSchedule.objects.get(class_uuid=class_uuid, lesson_period=lesson_period, weekday=weekday)
                        if ls.lesson_name != ln_obj:
                            ls.lesson_name = ln_obj
                            ls.save()
                    except:
                        LessonSchedule.objects.create(class_uuid=class_uuid, lesson_period=lesson_period, weekday=weekday, lesson_name=ln_obj)
                except Exception as e:
                    logger.exception(e)

            return ret
        except Exception as e:
            logger.exception(e)
            return

    class Meta:
        abstract = True


class TeacherLoginLog(TeachLog):
    """教师登录记录"""

    resource_from = models.CharField(max_length=50, blank=True)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES,
                                     blank=True)

    login_time = models.IntegerField(default=0, blank=True)

    def save(self, *args, **kwargs):
        super(TeacherLoginLog, self).save(*args, **kwargs)
        if constants.BANBANTONG_USE_MONGODB:
            mongo.save_teacherloginlog(self)
        data = {
            'teacher': self.teacher,
            'active_date': self.created_at.date(),
            'country_name': self.country_name,
            'town_name': self.town_name,
            'school_name': self.school_name,
            'school_year': self.term_school_year,
            'term_type': self.term_type,
            'lesson_name': self.lesson_name,
            'grade_name': self.grade_name
        }
        try:
            ActiveTeachers.objects.get_or_create(**data)
        except ActiveTeachers.MultipleObjectsReturned:
            ActiveTeachers.objects.filter(**data).all().delete()
            ActiveTeachers.objects.create(**data)
        except Exception as e:
            logger.exception(e)
        Statistic.update_on_loginlog(self)

    class Meta:
        db_table = 'TeacherLoginLog'
        index_together = [
            ('term_school_year', 'term_type', 'town_name', 'school_name', 'grade_name', 'class_name', 'lesson_name', 'teacher_name', 'lesson_period_sequence',),
            ('term_school_year', 'term_type', 'town_name', 'resource_from',),
            ('term_school_year', 'term_type', 'town_name', 'school_name', 'resource_from',),
            ('term_school_year', 'term_type', 'town_name', 'resource_type',),
            ('term_school_year', 'term_type', 'town_name', 'school_name', 'resource_type',),
            # ('term_school_year', 'term_type', 'grade_name', 'class_name', 'lesson_name', 'teacher_name', 'lesson_period_sequence',),
            ('created_at', 'town_name', 'school_name', 'grade_name', 'class_name', 'lesson_name', 'teacher_name', 'lesson_period_sequence',),
            ('created_at', 'town_name', 'resource_from',),
            ('created_at', 'town_name', 'school_name', 'resource_from',),
            ('created_at', 'town_name', 'resource_type',),
            ('created_at', 'town_name', 'school_name', 'resource_type',),
            # ('created_at', 'grade_name', 'class_name', 'lesson_name', 'teacher_name', 'lesson_period_sequence',),
        ]


class TeacherLoginLogTag(BaseModel):
    """教室登录记录附表>用于标记产生于电脑教室的登录记录"""

    bind_to = models.ForeignKey('TeacherLoginLog')
    created_at = models.ForeignKey('Class')


class TeacherLoginLogLessonContent(BaseModel):
    school_year = models.CharField(max_length=20, blank=True, null=True)
    term_type = models.CharField(max_length=20, blank=True, null=True)
    teacherloginlog = models.OneToOneField(TeacherLoginLog, db_column='teacherloginlog_uuid')
    title = models.CharField(u'大纲标题', max_length=100, blank=True, null=True)
    # lessoncontent = models.OneToOneField(SyllabusGradeLessonContent, unique=False, blank=True, null=True)
    lessoncontent = models.ForeignKey(SyllabusGradeLessonContent, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.school_year = self.teacherloginlog.term_school_year
        self.term_type = self.teacherloginlog.term_type
        super(TeacherLoginLogLessonContent, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'%s %s' % (self.teacherloginlog.teacher_name, self.title)

    class Meta:
        db_table = 'TeacherLoginLogLessonContent'
        index_together = [
            ('school_year', 'term_type',),
        ]


class TeacherLoginCountWeekly(models.Model):
    school_year = models.CharField(max_length=20, blank=True, null=True)
    term_type = models.CharField(max_length=20, blank=True, null=True)
    town_name = models.CharField(max_length=100,
                                 db_index=True)
    school_name = models.CharField(max_length=100,
                                   db_index=True)
    term = models.ForeignKey('Term', to_field='uuid',
                             db_column='term_uuid')
    grade_name = models.CharField(max_length=20,
                                  db_index=True)
    class_name = models.CharField(max_length=20,
                                  db_index=True)
    week = models.IntegerField(default=0, db_index=True)
    lesson_count = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        self.school_year = self.term.school_year
        self.term_type = self.term.term_type
        super(TeacherLoginCountWeekly, self).save(*args, **kwargs)

    class Meta:
        index_together = [
            ('school_year', 'term_type', 'town_name', 'school_name', 'grade_name', 'class_name', 'week',),
            # ('town_name', 'school_name', 'grade_name', 'class_name', 'week',),
        ]


class TeacherLoginTimeWeekly(models.Model):
    school_year = models.CharField(max_length=20, blank=True, null=True)
    term_type = models.CharField(max_length=20, blank=True, null=True)
    town_name = models.CharField(max_length=100,
                                 db_index=True)
    school_name = models.CharField(max_length=100,
                                   db_index=True)
    term = models.ForeignKey('Term', to_field='uuid',
                             db_column='term_uuid')
    grade_name = models.CharField(max_length=20,
                                  db_index=True)
    class_name = models.CharField(max_length=20,
                                  db_index=True)
    week = models.IntegerField(default=0, db_index=True)
    total_time = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        self.school_year = self.term.school_year
        self.term_type = self.term.term_type
        super(TeacherLoginTimeWeekly, self).save(*args, **kwargs)

    class Meta:
        index_together = [
            ('school_year', 'term_type', 'town_name', 'school_name', 'grade_name', 'class_name', 'week',),
            # ('town_name', 'school_name', 'grade_name', 'class_name', 'week',),
        ]


class TeacherLoginTime(BaseModel):
    """使用 时长，每条记录对应一个TeacherLoginLog记录"""

    school_year = models.CharField(max_length=20, blank=True, null=True)
    term_type = models.CharField(max_length=20, blank=True, null=True)
    teacherloginlog = models.OneToOneField(TeacherLoginLog)
    login_time = models.IntegerField()

    def __unicode__(self):
        return '%s %s' % (self.teacherloginlog.teacher.name,
                          str(self.login_time))

    def save(self, *args, **kwargs):
        self.school_year = self.teacherloginlog.term_school_year
        self.term_type = self.teacherloginlog.term_type
        super(TeacherLoginTime, self).save(*args, **kwargs)
        if constants.BANBANTONG_USE_MONGODB:
            mongo.save_teacherlogintime(self)
        if not self.teacherloginlog.grade \
                or not self.teacherloginlog.class_uuid \
                or not self.teacherloginlog.teacher:
            return
        if 'force_update' in kwargs and kwargs['force_update'] is True:
            Statistic.update_on_logintime(self)
            return
        if Setting.getvalue('server_type') in ('country', 'school', ) \
                or Setting.getvalue('installed') != 'True':
            # 添加一个缓存数据
            TeacherLoginTimeCache(
                town=self.teacherloginlog.town,
                school=self.teacherloginlog.school,
                grade=self.teacherloginlog.grade,
                class_uuid=self.teacherloginlog.class_uuid,
                teacher=self.teacherloginlog.teacher,
                lesson_name=self.teacherloginlog.lesson_name,
                teacherlogintime=self
            ).save()
            # 为lessonteacher添加login_time
            lessonteacher = self.teacherloginlog.lesson_teacher
            if lessonteacher:
                lessonteacher.login_time += self.login_time
                lessonteacher.save()

        Statistic.update_on_logintime(self)

    class Meta:
        index_together = [
            ('school_year', 'term_type',),
        ]


class TeacherLoginTimeTemp(models.Model):
    """临时表 ，客户端每若干秒心跳一次，服务器把增加的使用时长写入此表"""

    teacherloginlog = models.OneToOneField(TeacherLoginLog)
    login_time = models.IntegerField()
    last_login_datetime = models.DateTimeField(default=None, null=True)


class TeacherLoginTimeCache(models.Model):
    """
    缓存表 ，用于区县市级服务器班班通授课时长统计功能。

    每写入一条TeacherLoginTime记录时更新此表
    """

    school_year = models.CharField(max_length=20, blank=True, null=True)
    term_type = models.CharField(max_length=20, blank=True, null=True)
    town = models.ForeignKey('Group', to_field='uuid',
                             related_name='town_teacherlogintimecache_set',
                             db_column='town_uuid')
    school = models.ForeignKey('Group', to_field='uuid',
                               related_name='school_teacherlogintimecache_set',
                               db_column='school_uuid')
    grade = models.ForeignKey('Grade', to_field='uuid',
                              db_column='grade_uuid')
    class_uuid = models.ForeignKey('Class', to_field='uuid',
                                   db_column='class_uuid')
    teacher = models.ForeignKey('Teacher', to_field='uuid',
                                db_column='teacher_uuid')
    lesson_name = models.CharField(max_length=20, db_index=True)
    teacherlogintime = models.OneToOneField(TeacherLoginTime)

    def save(self, *args, **kwargs):
        self.school_year = self.teacherlogintime.school_year
        self.term_type = self.teacherlogintime.term_type
        super(TeacherLoginTimeCache, self).save(*args, **kwargs)

    class Meta:
        index_together = [
            ('school_year', 'term_type',),
        ]


class TeacherAbsentLog(TeachLog):
    """教师未登录记录"""

    class Meta:
        db_table = 'TeacherAbsentLog'
        ordering = ['-created_at']
        index_together = [
            ('term_school_year', 'term_type', 'town_name', 'school_name', 'grade_name', 'class_name', 'lesson_name', 'teacher_name', 'lesson_period_sequence',),
            # ('term_school_year', 'term_type', 'grade_name', 'class_name', 'lesson_name', 'teacher_name', 'lesson_period_sequence',),
            ('created_at', 'town_name', 'school_name', 'grade_name', 'class_name', 'lesson_name', 'teacher_name', 'lesson_period_sequence',),
            # ('created_at', 'grade_name', 'class_name', 'lesson_name', 'teacher_name', 'lesson_period_sequence',),
        ]


# 2014-06-25  学年学期设置 校级 -> 区县
class NewTerm(BaseModel):
    """学期"""

    # 学年: '2014-2015'
    # 学期: 春季学期/秋季学期
    school_year = models.CharField(max_length=20, db_index=True)
    term_type = models.CharField(max_length=20, choices=TERM_TYPES, db_index=True)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    country = models.ForeignKey('Group', to_field='uuid',
                                db_column='country_uuid',
                                limit_choices_to={'group_type': 'country'},
                                db_index=True)
    deleted = models.BooleanField(default=False)
    v = [validators.MaxValueValidator(2147483647),
         validators.MinValueValidator(0)]
    schedule_time = models.IntegerField(help_text='计划达标课时/班级',
                                        default=0,
                                        validators=v)

    @staticmethod
    def get_current_term(date=None):
        if not date:
            today = datetime.date.today()
        else:
            today = date
            if not isinstance(date, datetime.date):
                return None
        try:
            term = NewTerm.objects.get(start_date__lte=today, end_date__gte=today)
            return term
        except:
            return None

    @staticmethod
    def get_current_or_next_term():
        """获取当前或未来的一个学期"""
        o = NewTerm.get_current_term()
        if not o:
            today = datetime.datetime.now().date()
            o = NewTerm.objects.filter(start_date__gte=today).order_by('start_date')
            if o.exists():
                return o[0]
            return None
        else:
            return o

    @staticmethod
    def get_nearest_term():
        """获取当前>未来>距今最近的一个学年学期"""
        server_type = Setting.getvalue('server_type')
        if server_type != 'school':
            o = NewTerm.get_current_or_next_term()
            if not o:
                o = NewTerm.get_previous_term()
        else:
            o = Term.get_current_term_list()
            if not o:
                o = Term.get_previous_terms()
            o = o and o[0] or None
        return o

    @staticmethod
    def get_previous_term(term=None):
        # 上一学期
        if not term:
            term = NewTerm.get_current_term()
        if not term:
            return None
        if term.term_type == u'春季学期':
            school_year = term.school_year
            term_type = u'秋季学期'
        else:
            s, e = term.school_year.split('-')
            school_year = '%d-%d' % (int(s) - 1, int(e) - 1)
            term_type = u'春季学期'
        try:
            obj = NewTerm.objects.get(school_year=school_year, term_type=term_type)
            return obj
        except:
            return None

    @staticmethod
    def get_lastyear_term(term=None):
        # 去年同一学期
        if not term:
            term = NewTerm.get_current_term()
        if not term:
            return None
        s, e = term.school_year.split('-')
        school_year = '%d-%d' % (int(s) - 1, int(e) - 1)
        try:
            obj = NewTerm.objects.get(school_year=school_year, term_type=term.term_type)
            return obj
        except:
            return None

    @staticmethod
    def get_term(start_date, end_date, school_year, term_type):
        # 根据查询条件获取学期
        if start_date and end_date:
            s = parse_date(start_date)
            e = parse_date(end_date)
            cond = models.Q(start_date__lte=s, end_date__gte=e)
            cond |= models.Q(start_date__gte=s, end_date__lte=e)
            try:
                ret = NewTerm.objects.get(cond)
                return ret
            except:
                return
        else:
            try:
                ret = NewTerm.objects.get(school_year=school_year,
                                          term_type=term_type)
                return ret
            except:
                return

    @staticmethod
    def get_term_by_date(date):
        if isinstance(date, str):
            date = parse_date(date)
        elif isinstance(date, datetime.datetime):
            date = date.date()

        if not isinstance(date, datetime.date):
            return None

        return NewTerm.get_current_term(date=date)

    def __unicode__(self):
        return '%s %s' % (self.school_year, self.term_type)

    class Meta:
        db_table = 'NewTerm'


class Term(BaseModel):
    """学期"""

    # 学年格式为'2014-2015'
    school_year = models.CharField(max_length=20,
                                   db_index=True)
    term_type = models.CharField(max_length=20,
                                 choices=TERM_TYPES,
                                 db_index=True)  # 春季学期/秋季学期
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    school = models.ForeignKey('Group', to_field='uuid',
                               db_column='school_uuid',
                               limit_choices_to={'group_type': 'school'},
                               db_index=True)
    deleted = models.BooleanField(default=False)
    schedule_time = models.IntegerField(help_text='计划达标课时',
                                        default=0,
                                        blank=True)

    def allow_import_lesson(self):
        """
        该学年学期该班级是否可以导入课程表

        1. deleted = 1 不允许
        2. 导入日期 > end_date 不允许
        """
        if self.deleted:
            return False
        now = datetime.datetime.now()
        if now.date() > self.end_date:
            return False

        return True

    @staticmethod
    def get_current_term_list(school=None, date=None):
        # 获取当前学校/指定学校/学校列表的当前学期(或距今最近的一个未来学期)
        base_terms = Term.objects.filter(deleted=False)
        date = datetime.datetime.now()
        ret = []
        if school is None:
            school = Group.objects.filter(group_type='school')
        if isinstance(school, Group):
            q = base_terms.filter(start_date__lte=date, end_date__gte=date, school=school)
            if q.exists():
                ret.append(q[0])
            else:
                q = base_terms.filter(start_date__gt=date, school=school).order_by('start_date')
                if q.exists():
                    ret.append(q[0])
        elif isinstance(school, QuerySet):
            for i in school:
                ret.extend(Term.get_current_term_list(i))
        return ret

    @staticmethod
    def get_term_by_date(date=None):
        if not date:
            date = datetime.datetime.now().today()
        elif isinstance(date, str):
            date = parse_date(date)
        elif isinstance(date, datetime.datetime):
            date = date.date()

        if not isinstance(date, datetime.date):
            return None

        server_type = Setting.getvalue('server_type')
        if server_type == 'school':
            return Term.get_current_term_list(date=date)
        else:
            return None
            # just for school
            # return NewTerm.get_current_term(date=date)

    @staticmethod
    def get_previous_terms():
        # 用于区县市服务器，获取所有学校的上一个学期
        now = datetime.datetime.now()
        ret = []
        schools = Group.objects.filter(group_type='school')
        for school in schools:
            q = Term.objects.filter(end_date__lt=now, school=school)
            q = q.order_by('-end_date')
            if q.exists():
                ret.append(q[0])
        return ret

    @staticmethod
    def get_lastyear_terms(school=None):
        # 用于区县市服务器，获取上一学年同一个学期
        now = datetime.datetime.now()
        ret = []
        terms = Term.get_current_term_list()
        for term in terms:
            q = Term.objects.filter(end_date__lt=now, school=term.school,
                                    term_type=term.term_type)
            q = q.order_by('-end_date')
            if q.exists():
                ret.append(q[0])
        return ret

    def __unicode__(self):
        return '%s %s' % (self.school_year, self.term_type)

    class Meta:
        db_table = 'Term'
        index_together = [
            ('school_year', 'term_type',),
        ]


class Token(models.Model):
    token_type = models.CharField(max_length=20,
                                  choices=TOKEN_TYPES,
                                  db_index=True)
    value = models.CharField(max_length=128, db_index=True)
    info = models.TextField(default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Token'

    @staticmethod
    def clean_bad_tokens(type='lesson_start'):
        """
        lesson_start token的正确的生命周期应该处于上一节课结束到下一节课开始

        所以上一节课结束之前的token都属于残留的bad token, 应该予以清除
        """
        tokens = Token.objects.filter(token_type=type)
        lp = LessonPeriod.get_current_or_next_period()
        if not lp:
            # 今天课程全部结束, 清理掉全部的上课登录token
            tokens = tokens.all().delete()
            return
        now = datetime.datetime.now()
        today = now.date()
        e = datetime.datetime.combine(today, now.time())
        earlier_sq = LessonPeriod.objects.filter(sequence=lp.sequence - 1)
        if earlier_sq.exists():
            s = datetime.datetime.combine(today, earlier_sq[0].end_time)
        else:
            # 第一节课的时候, 那么清理掉今天以前的token
            s = datetime.datetime.combine(today, datetime.time.min)
        tokens.exclude(created_at__range=(s, e)).all().delete()
        return


class TotalTeachersCountry(models.Model):
    term = models.ForeignKey('Term', to_field='uuid',
                             null=True, default=None,
                             db_column='term_uuid')
    country_name = models.CharField(max_length=100, db_index=True)
    total = models.IntegerField(default=0)

    def __unicode__(self):
        return '%s %d' % (self.country_name, self.total)


class TotalTeachersTown(models.Model):
    term = models.ForeignKey('Term', to_field='uuid',
                             null=True, default=None,
                             db_column='term_uuid')
    country_name = models.CharField(max_length=100, db_index=True)
    town_name = models.CharField(max_length=100, db_index=True)
    total = models.IntegerField(default=0)

    def __unicode__(self):
        return '%s %s %d' % (self.country_name, self.town_name, self.total)


class TotalTeachersSchool(models.Model):
    term = models.ForeignKey('Term', to_field='uuid',
                             null=True, default=None,
                             db_column='term_uuid')
    country_name = models.CharField(max_length=100, db_index=True)
    town_name = models.CharField(max_length=100, db_index=True)
    school_name = models.CharField(max_length=100, db_index=True)
    total = models.IntegerField(default=0)

    def __unicode__(self):
        return '%s %s %s %d' % (self.country_name, self.town_name,
                                self.school_name, self.total)


class TotalTeachersLesson(models.Model):
    term = models.ForeignKey('Term', to_field='uuid',
                             null=True, default=None,
                             db_column='term_uuid')
    country_name = models.CharField(max_length=100, db_index=True)
    town_name = models.CharField(max_length=100, db_index=True)
    school_name = models.CharField(max_length=100, db_index=True)
    lesson_name = models.CharField(max_length=20, db_index=True)
    total = models.IntegerField(default=0)

    def __unicode__(self):
        return '%s %s %s %s %d' % (self.country_name, self.town_name,
                                   self.school_name, self.lesson_name,
                                   self.total)


class TotalTeachersGrade(models.Model):
    term = models.ForeignKey('Term', to_field='uuid',
                             null=True, default=None,
                             db_column='term_uuid')
    country_name = models.CharField(max_length=100, db_index=True)
    town_name = models.CharField(max_length=100, db_index=True)
    school_name = models.CharField(max_length=100, db_index=True)
    grade_name = models.CharField(max_length=20, db_index=True)
    total = models.IntegerField(default=0)

    def __unicode__(self):
        return '%s %s %s %s %d' % (self.country_name, self.town_name,
                                   self.school_name, self.grade_name,
                                   self.total)


class TotalTeachersLessonGrade(models.Model):
    term = models.ForeignKey('Term', to_field='uuid',
                             null=True, default=None,
                             db_column='term_uuid')
    town_name = models.CharField(max_length=100, db_index=True)
    school_name = models.CharField(max_length=100, db_index=True)
    lesson_name = models.CharField(max_length=20, db_index=True)
    grade_name = models.CharField(max_length=20, db_index=True)
    total = models.IntegerField(default=0)

    def __unicode__(self):
        return '%s %s %s %s %d' % (self.town_name, self.school_name,
                                   self.lesson_name, self.grade_name,
                                   self.total)

    class Meta:
        index_together = [
            ['lesson_name', 'grade_name'],
        ]


class User(BaseModel):
    username = models.CharField(max_length=20)
    password = PasswordCharField(max_length=128, blank=True)
    realname = models.CharField(max_length=100, default='', blank=True)
    sex = models.CharField(max_length=20, default='male', choices=SEX,
                           db_index=True, blank=True)
    qq = models.CharField(max_length=20, default='', blank=True)
    mobile = models.CharField(max_length=20, default='', blank=True)
    email = models.CharField(max_length=200, default='', blank=True)
    status = models.CharField(max_length=20, default='active',
                              choices=USER_STATUS)
    role = models.ForeignKey('Role', to_field='uuid',
                             db_column='role_uuid',
                             blank=True, null=True,
                             on_delete=models.SET_NULL, db_index=True)
    level = models.CharField(max_length=20, default='school',
                             choices=USER_LEVELS)
    created_at = models.DateTimeField(auto_now_add=True)
    permitted_groups = models.ManyToManyField('Group',
                                              through='UserPermittedGroup')
    remark = models.CharField(max_length=180, blank=True, db_index=True)

    def __unicode__(self):
        return self.username

    def __iter__(self):
        _dict = self.to_dict(exclude=['password'])
        return _dict.iteritems()

    class Meta:
        db_table = 'User'
        verbose_name = _('user')
        verbose_name_plural = _('users')


class UserPermittedGroup(BaseModel):
    """
    用户的管理范围，以学校为单位。如需管理某市下面的所有学校，

    需要把学校节点都勾选上。
    """

    user = models.ForeignKey('User', to_field='uuid',
                             db_column='user_uuid', db_index=True)
    group = models.ForeignKey('Group', to_field='uuid',
                              db_column='group_uuid', db_index=True)

    class Meta:
        db_table = 'UserPermittedGroup'


class UsbkeyTeacher(models.Model):
    usbkey_uuid = models.CharField(max_length=180,
                                   db_column='usbkey_uuid',
                                   primary_key=True,
                                   db_index=True)
    teacher_uuid = models.CharField(max_length=40,
                                    db_column='teacher_uuid',
                                    db_index=True)
    sync_uploaded = models.BooleanField(default=False,
                                        db_index=True)

    @staticmethod
    def add_log(instance, log_type):
        data = serializers.serialize('json', [instance, ],
                                     fields=('usbkey_uuid', 'teacher_uuid'))
        SyncLog.objects.create(operation_type=log_type,
                               operation_content=data)

    class Meta:
        db_table = 'usbkey_teachers'


class CourseWare(BaseModel):
    md5 = models.CharField(u'MD5验证码', max_length=255)
    create_time = models.DateTimeField(u'创建时间', auto_now_add=True)
    title = models.CharField(u'课件标题', max_length=50, blank=True, null=True)
    size = models.CharField(u'课件大小', max_length=20, blank=True, null=True)
    use_times = models.IntegerField(u'课件使用次数', default=0)
    download_times = models.IntegerField(u'课件下载次数', default=0)
    file_name = models.FileField(u'课件本地存储', upload_to=constants.UPLOAD_TMP_ROOT, blank=True, null=True)
    qiniu_url = models.CharField(u'七牛存储地址', max_length=255, blank=True, null=True)
    teacherloginlog = models.ManyToManyField('TeacherLoginLog', through='TeacherLoginLogCourseWare')

    def __unicode__(self):
        return u'%s-%s' % (self.title, self.md5)

    class Meta:
        db_table = 'CourseWare'


class TeacherLoginLogCourseWare(BaseModel):
    school_year = models.CharField(max_length=20, blank=True, null=True)
    term_type = models.CharField(max_length=20, blank=True, null=True)
    courseware = models.ForeignKey('CourseWare', to_field='uuid', db_column='courseware_uuid', db_index=True)
    teacherloginlog = models.ForeignKey('TeacherLoginLog', to_field='uuid', db_column='teacherloginlog_uuid', db_index=True)

    def save(self, *args, **kwargs):
        self.school_year = self.teacherloginlog.term_school_year
        self.term_type = self.teacherloginlog.term_type
        super(TeacherLoginLogCourseWare, self).save(*args, **kwargs)

    class Meta:
        db_table = 'TeacherLoginLogCourseWare'
        index_together = [
            ('school_year', 'term_type',),
        ]


@receiver(signals.pre_delete)
def my_pre_delete(sender, instance, using, **kwargs):
    if isinstance(instance, BaseModel):
        SyncLog.add_log(instance, 'delete')
    elif isinstance(instance, CountryToSchoolBaseModel):
        # 仅县级服务器
        if Setting.getvalue('server_type') == 'country':
            CountryToSchoolSyncLog.add_log(instance, 'delete')
    else:
        return

    modelname = sender.__name__

    if modelname == 'Node':
        try:
            key = 'sync_%s' % instance.uuid
            Setting.objects.get(name=key).delete()
        except Exception:
            pass


@receiver(signals.post_delete)
def my_post_delete(sender, instance, using, **kwargs):
    modelname = sender.__name__
    if modelname == 'LessonTeacher':
        # 重新计算TotalTeachers
        try:
            LessonTeacher.calculate_total_teachers(instance)
        except:
            pass
    if constants.BANBANTONG_USE_MONGODB:
        if modelname == 'Class':
            conn = mongo._get_conn()
            conn.banbantong.classes.remove(mongo.class_to_dict(instance))
            conn.close()
