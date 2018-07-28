# coding=utf-8
import datetime

from django.db import models
from django.db.models import Q
from BanBanTong.utils.str_util import generate_node_key as _generate_key


class EduPoint(models.Model):
    '''教学点'''
    school_year = models.CharField(u'学年', max_length=100)
    term_type = models.CharField(u'学期', max_length=100)
    province_name = models.CharField(u'省', max_length=100, blank=True)
    city_name = models.CharField(u'市', max_length=100, blank=True)
    country_name = models.CharField(u'县', max_length=100, blank=True)
    town_name = models.CharField(u'乡镇街道', max_length=100, blank=True)
    point_name = models.CharField(u'教学点名称', max_length=100)
    number = models.IntegerField(u'教室终端数量', default=1)
    create_time = models.DateTimeField(u'创建日期', auto_now_add=True)
    update_time = models.DateTimeField(u'更新日期', auto_now=True)
    remark = models.CharField(u'备注', max_length=255, blank=True)

    def has_delete(self, *args, **kwargs):
        '''
            检查该教学下的所有教室是否有绑定，
            如果有绑定返回False(不能删除),否则返回True(可以删除)
        '''
        objs = self.edupointdetail_set.exclude(Q(cpuID__isnull=True) | Q(cpuID=''))
        if objs.count():
            return False

        return True

    def delete(self, *args, **kwargs):
        # 卫星资源接收日志
        self.edupointresourcerecelog_set.all().delete()

        # 教学点机器使用时长统计日志
        self.edupointmachinetimeused_set.all().delete()

        # 教学点终端使用日志
        # self.edupointdetailuselog_set.all().delete()

        # 教学点终端桌面截图日志
        self.edupointdetaildesktopviewlog_set.all().delete()

        # 教学点教室终端
        self.edupointdetail_set.all().delete()

        super(EduPoint, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.pk:
            create_detail = True
        else:
            create_detail = False

        super(EduPoint, self).save(*args, **kwargs)

        if create_detail:
            # 每创建一个教学点时默认生成一个卫星接收终端
            EduPointDetail.objects.create(edupoint=self, type='moon', communicate_key=_generate_key(), name='1')
            # 每创建一个教学点时默认生成number个教室终端
            for i in range(1, self.number + 1):
                EduPointDetail.objects.create(edupoint=self, type='room', communicate_key=_generate_key(), name=str(i))
        else:
            old_number = self.edupointdetail_set.filter(type='room').count()
            if self.number > old_number:
                last_obj = self.edupointdetail_set.filter(type='room').last()
                for i in range(1, self.number - old_number + 1):
                    name = str(int(last_obj.name) + i)
                    EduPointDetail.objects.create(edupoint=self, type='room', communicate_key=_generate_key(), name=name)

    def __unicode__(self):
        return self.point_name


class EduPointResourceCatalog(models.Model):
    '''教学点资源接收目录'''
    edupoint = models.ForeignKey(EduPoint)
    catalog = models.CharField(u'教学点资源接收目录', max_length=255)


class EduPointDetail(models.Model):
    '''教学点教室终端'''
    EDU_POINT_TYPE = (
        ('moon', u'卫星终端'),
        ('room', u'教学点教室')
    )

    edupoint = models.ForeignKey(EduPoint)
    type = models.CharField(u'终端类型', max_length=20, choices=EDU_POINT_TYPE)
    name = models.CharField(u'教室终端编号', max_length=20)
    communicate_key = models.CharField(u'同步密钥', max_length=100, blank=True)
    cpuID = models.CharField(u'绑定cpuID', max_length=100, blank=True)
    last_active_time = models.DateTimeField(u'连接服务器时间', null=True, blank=True)
    last_upload_time = models.DateTimeField(u'数据同步时间', null=True, blank=True)

    # def delete(self, *args, **kwargs):
    #    # 只有一个教学点有多个教室时才可以做单独删除
    #    if self.type == 'room':
    #        self.edupoint.number -= 1
    #        self.edupoint.save()
    #
    #    super(EduPointDetail, self).delete(*args, **kwargs)


class EduPointResourceReceLog(models.Model):
    '''卫星资源接收日志'''
    school_year = models.CharField(u'学年', max_length=100)
    term_type = models.CharField(u'学期', max_length=100)
    province_name = models.CharField(u'省', max_length=100, blank=True)
    city_name = models.CharField(u'市', max_length=100, blank=True)
    country_name = models.CharField(u'县', max_length=100, blank=True)
    town_name = models.CharField(u'乡镇街道', max_length=100, blank=True)
    point_name = models.CharField(u'教学点名称', max_length=100)
    edupoint = models.ForeignKey(EduPoint, blank=True, null=True)
    rece_time = models.DateField(u'资源接收时间', blank=True, null=True)
    rece_count = models.BigIntegerField(u'资源接收文件总个数', default=0)
    rece_size = models.BigIntegerField(u'资源接收文件总大小', default=0)
    rece_type = models.BigIntegerField(u'资源接收类型总数量', default=0)

    def save(self, *args, **kwargs):
        super(EduPointResourceReceLog, self).save(*args, **kwargs)
        # 更新edupointdetail
        if self.edupoint:
            now = datetime.datetime.now()
            EduPointDetail.objects.filter(edupoint=self.edupoint, type='moon').update(last_upload_time=now)

    def delete(self, *args, **kwargs):
        # 先删除EduPointResourceReceLogDetail数据
        self.edupointresourcerecelogdetail_set.all().delete()

        super(EduPointResourceReceLog, self).delete(*args, **kwargs)


class EduPointResourceReceLogDetail(models.Model):
    '''卫星资源接收日志详细'''
    edu_point_resource_rece_log = models.ForeignKey(EduPointResourceReceLog)
    type = models.CharField(u'资源类型', max_length=100)
    size = models.BigIntegerField(u'该资源类型拥有文件大小')
    count = models.BigIntegerField(u'该资源类型拥有文件数量')

    def delete(self, *args, **kwargs):

        self.edu_point_resource_rece_log.rece_size -= self.size
        self.edu_point_resource_rece_log.rece_count -= self.count
        self.edu_point_resource_rece_log.rece_type -= 1
        self.edu_point_resource_rece_log.save()

        super(EduPointResourceReceLogDetail, self).delete(*args, **kwargs)


class EduPointMachineTimeUsed(models.Model):
    '''教学点终端机器时长(一天一条)'''
    school_year = models.CharField(u'学年', max_length=100)
    term_type = models.CharField(u'学期', max_length=100)
    province_name = models.CharField(u'省', max_length=100, blank=True)
    city_name = models.CharField(u'市', max_length=100, blank=True)
    country_name = models.CharField(u'县', max_length=100, blank=True)
    town_name = models.CharField(u'乡镇街道', max_length=100, blank=True)
    point_name = models.CharField(u'教学点名称', max_length=100)
    number = models.CharField(u'教学点教室编号', max_length=100)
    edupoint = models.ForeignKey(EduPoint, blank=True, null=True)
    edupointdetail = models.ForeignKey(EduPointDetail, blank=True, null=True)
    create_time = models.DateField(u'创建日期', auto_now_add=True)
    update_time = models.DateTimeField(u'最后更新时间', auto_now=True)
    use_time = models.IntegerField(u'使用时长(分钟)', default=0)
    boot_time = models.IntegerField(u'开机时长(分钟)', default=0)
    boot_count = models.IntegerField(u'开机次数', default=0)

    def save(self, *args, **kwargs):
        super(EduPointMachineTimeUsed, self).save(*args, **kwargs)
        # 更新EduPointDetail的last_upload_time字段
        if self.edupointdetail:
            now = datetime.datetime.now()
            self.edupointdetail.last_upload_time = now
            self.edupointdetail.save()

# class EduPointDetailUseLog(models.Model):
#    '''教学点终端使用日志(一天一条)'''
#    school_year = models.CharField(u'学年', max_length=100)
#    term_type = models.CharField(u'学期', max_length=100)
#    province_name = models.CharField(u'省', max_length=100, blank=True)
#    city_name = models.CharField(u'市', max_length=100, blank=True)
#    country_name = models.CharField(u'县', max_length=100, blank=True)
#    town_name = models.CharField(u'乡镇街道', max_length=100, blank=True)
#    point_name = models.CharField(u'教学点名称', max_length=100)
#    number = models.CharField(u'教学点教室编号', max_length=100)
#    edupoint = models.ForeignKey(EduPoint, blank=True, null=True)
#    edupointdetail = models.ForeignKey(EduPointDetail, blank=True, null=True)
#    date = models.DateField(u'使用日期', blank=True, null=True)
#    use_time = models.IntegerField(u'使用时长')
#    #boot_time = models.IntegerField(u'开机时长')


class EduPointDetailDesktopViewLog(models.Model):
    '''教学点终端桌面截图日志'''
    school_year = models.CharField(u'学年', max_length=100)
    term_type = models.CharField(u'学期', max_length=100)
    province_name = models.CharField(u'省', max_length=100, blank=True)
    city_name = models.CharField(u'市', max_length=100, blank=True)
    country_name = models.CharField(u'县', max_length=100, blank=True)
    town_name = models.CharField(u'乡镇街道', max_length=100, blank=True)
    point_name = models.CharField(u'教学点名称', max_length=100)
    number = models.CharField(u'教学点教室编号', max_length=100)
    edupoint = models.ForeignKey(EduPoint, blank=True, null=True)
    edupointdetail = models.ForeignKey(EduPointDetail, blank=True, null=True)
    create_time = models.DateTimeField(u'图片创建日期', blank=True, null=True)
    date = models.DateTimeField(u'添加日期', auto_now_add=True)
    pic = models.CharField(u'网络URL', max_length=255, blank=True)
    host = models.CharField(u'网络URL域名', max_length=255, blank=True)
