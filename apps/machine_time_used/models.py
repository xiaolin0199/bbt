# coding=utf-8
import time
import requests
import logging

from django.db import models
from django.db import connection
from django.core.cache import cache
from django.db import IntegrityError, OperationalError

from BanBanTong.db.models import InitModel
from BanBanTong.db.models import Group, Setting

logger = logging.getLogger(__name__)


def _make_new_uuid(obj):
    '''
    1. 自定义BigIngeter
        整个主键是19位数字
        其中前10位采用time.time()的整数部分，中间3位用该学校在县级的node_id
        末6位由该学校自己生成，一般使用唯一自增id

        校级服务器当前时间是：
        >>> import time
        >>> time.time()
        1417743673.263424
        前10位就是1417743673

        该学校在县级的node id是66
        中间3位就是066

        该学校需要新增一条models.NewTimeUsed数据，
        目前已有的NewTimeUsed数据最大id是14xxxxxxxxyyy003529，
        那么新增数据的末6位就是003530

        综上，新增数据的id是：1417743673066003530
    '''
    first_part = int(time.time())
    third_part = _get_third_part(obj)
    second_part = _get_second_part()

    # 组合
    c = u'%10d%03d%06d' % (first_part, second_part, third_part)

    return int(c)


def _get_second_part():
    '''
        去上级服务器取得NODE ID
        并放到缓存里
    '''
    cursor = connection.cursor()
    cursor.execute('Lock TABLES setting WRITE;')

    node_id = Setting.getvalue('sync_node_id')

    cursor.execute('UNLOCK TABLES;')
    cursor.close()

    return int(node_id)

    #  old version
    school_uuid = Group.objects.get(group_type='school').uuid
    cache_key = 'school-%s-node-id' % (school_uuid)
    node_id = cache.get(cache_key)
    if not node_id:
        # 获取上级服务器的HOST，PORT，KEY
        host = Setting.getvalue('sync_server_host')
        port = Setting.getvalue('sync_server_port')
        key = Setting.getvalue('sync_server_key')
        data = {
            'key': key
        }
        try:
            url = u'http://%s:%s/terminal/api/get_node_id/' % (host, port)

            ret = requests.post(url, data=data, timeout=60)
            ret = ret.json()
            node_id = ret['data']['node_id']
            if node_id:
                cache.set(cache_key, node_id, 60 * 60 * 24)
        except:
            node_id = None

    return node_id


def _get_third_part(obj):
    '''
        去BigIntSyncID找到obj对应模型的第三部分ID
    '''
    app_label = obj._meta.app_label
    model = obj._meta.object_name

    cursor = connection.cursor()

    cursor.execute('Lock TABLES machine_time_used_bigintsyncid WRITE;')

    try:
        # with transaction.atomic():
        o, created = BigIntSyncID.objects.get_or_create(app_label=app_label, model=model)
    except IntegrityError, e:
        # print 'IntegrityError, @@@@@@@@@@@@@@@@@ %s' %(e.args[0])
        # 主键冲突
        if e.args[0] == 1062:
            o = BigIntSyncID.objects.get(app_label=app_label, model=model)
        else:
            o = None
    except OperationalError, e:
        # print 'OperationalError, #################### %s' %(e.args[0])
        # 死锁
        if e.args[0] == 1213:
            o = BigIntSyncID.objects.get(app_label=app_label, model=model)
        else:
            o = None
    except Exception as e:
        # print 'Exception, #################### %s' %(e.args[0])
        logger.exception('except %s %s', e.args, e.message)
        o = None

    if o:
        o.sync_id += 1
        o.save()

        sync_id = o.sync_id
    else:
        sync_id = 0

    cursor.execute('UNLOCK TABLES;')
    cursor.close()

    return sync_id


class NewBaseModel(InitModel):
    uuid = models.BigIntegerField(primary_key=True)

    def save(self, *args, **kwargs):
        # if 'force_insert' in kwargs and kwargs['force_insert']:
        #    self.uuid = self.pk
        # elif 'force_update' in kwargs and kwargs['force_update']:
        #    self.uuid = self.pk
        # else:
        #    if self._state.adding:
        #        self.uuid = _make_new_uuid(self)
        #    else:
        #        self.uuid = self.pk
        if self.pk:
            self.uuid = self.pk
        else:
            self.uuid = _make_new_uuid(self)

        super(NewBaseModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class BigIntSyncID(models.Model):
    app_label = models.CharField(u'App label', max_length=100)
    model = models.CharField(u'Model name', max_length=100)
    sync_id = models.IntegerField(u'Next use id', default=0)

    def __unicode__(self):
        return u'%s/%s' % (self.app_label, self.model)

    class Meta:
        unique_together = ('app_label', 'model')


class MachineTimeUsed(NewBaseModel):
    term_school_year = models.CharField(u'学年', max_length=20, blank=True)
    term_type = models.CharField(u'学期', max_length=20, blank=True)
    province_name = models.CharField(u'省', max_length=100, blank=True)
    city_name = models.CharField(u'市', max_length=100, blank=True)
    country_name = models.CharField(u'区县', max_length=100, blank=True)
    town_name = models.CharField(u'街道', max_length=100, blank=True)
    school_name = models.CharField(u'学校', max_length=100, blank=True)
    grade_name = models.CharField(u'年级', max_length=20, blank=True)
    class_name = models.CharField(u'班级', max_length=20, blank=True)
    mac = models.CharField(u'MAC', max_length=20, blank=True)
    school = models.ForeignKey(Group, to_field='uuid', db_column='school_uuid', null=True, blank=True)
    create_time = models.DateTimeField(u'开始使用日期', blank=True)
    use_time = models.IntegerField(u'开机时长(分钟)', default=0)
    use_count = models.IntegerField(u'开机次数', default=0)
    # last_shutdown_datetime = models.DateTimeField(u'最后关机时间', blank=True)

    def __unicode__(self):
        return u'%s: 开机次数(%s) 开机时长(%s)' % (self.create_time, self.use_time, self.use_count)

    class Meta:
        index_together = [
            ('term_school_year', 'term_type', 'town_name', 'school_name', 'grade_name', 'class_name',),
            #('term_school_year', 'term_type', 'grade_name', 'class_name',),
            ('create_time', 'town_name', 'school_name', 'grade_name', 'class_name',),
            #('create_time', 'grade_name', 'class_name',),
        ]
