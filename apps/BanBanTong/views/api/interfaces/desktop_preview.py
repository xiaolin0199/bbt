# coding=utf-8
import datetime
import ftplib
import logging
import os
import pypinyin
import random
import time
import upyun
from django import forms
from django.conf import settings
from django.http.response import HttpResponse
from django.template import loader
from BanBanTong.db import models
from BanBanTong.utils import cloud_service
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import str_util
DEBUG = settings.DEBUG


logger = logging.getLogger(__name__)


class ComputerclassUploadForm(forms.Form):
    class_mac = forms.CharField()
    pic = forms.FileField()


class UploadForm(forms.Form):
    mac = forms.CharField()
    pic = forms.FileField()


def _get_class(cc):
    """获取当前在电脑教室上课的普通班级"""
    tag = models.TeacherLoginLogTag.objects.filter(created_at=cc)
    uu = tag.values_list('bind_to', flat=True)
    log = models.TeacherLoginLog.objects.filter(uuid__in=uu)
    lp = models.LessonPeriod.get_current_or_next_period()
    if not lp:
        return None
    log = log.filter(lesson_period=lp).order_by('-created_at')
    if log.exists():
        log = log[0]
        return log.class_uuid


def file_upload(request):
    try:
        template = loader.get_template('upload.html')
        return HttpResponse(template.render({}))
    except:

        logger.exception('')


def get_settings(request):
    try:
        server_type = models.Setting.getvalue('server_type')
        func = models.Setting.objects.get
        if server_type == 'school':
            obj = func(name='desktop-preview-interval')
            interval = int(obj.value)
            data = {'desktop-preview-interval': interval}
        elif server_type == 'country':
            interval = int(func(name='desktop-preview-interval').value)
            days = int(func(name='desktop-preview-days-to-keep').value)
            sp = func(name='cloud-service-provider').value
            username = func(name='cloud-service-username').value
            password = func(name='cloud-service-password').value
            data = {
                'desktop-preview-interval': interval,
                'desktop-preview-days-to-keep': days,
                'cloud-service-provider': sp,
                'cloud-service-username': username,
                'cloud-service-password': password,
            }
        else:
            return create_failure_dict(msg='错误的服务器级别')
        return create_success_dict(data=data)
    except:
        return create_failure_dict(msg='管理员尚未设置参数')


def _upload_file_http(bucket, username, password, f, town, school, now):
    data = ''
    for chunk in f.chunks():
        data += chunk
    up = upyun.UpYun(bucket, username, password, endpoint=upyun.ED_AUTO)
    try:
        up.usage()
    except upyun.UpYunServiceException:
        bucket = 'oe-test1'
        del up
        up = upyun.UpYun(bucket, username, password)
    ext = os.path.splitext(f.name)[1]
    town_pinyin = '-'.join(pypinyin.lazy_pinyin(town.name))
    school_pinyin = '-'.join(pypinyin.lazy_pinyin(school.name))
    # /year-month-day/school/time.ms.ext
    path = '/%04d-%02d-%02d/%s/%s/%.06f%s' % (now.year, now.month, now.day,
                                              town_pinyin, school_pinyin,
                                              time.time(), ext)
    # print 'save_file: uploading %s to upyun' % path
    try:
        up.put(path, data)
    except upyun.UpYunClientException:
        up = upyun.UpYun(bucket, username, password, endpoint=upyun.ED_CNC)
        up.put(path, data)
    # if DEBUG:
    #     print u'DEBUG screen_upload ---5'
    return path


def _upload_file_ftp(bucket, username, password, f, town, school, now):
    ftp = ftplib.FTP()
    ftp.connect(upyun.ED_CNC)
    ftp.login('%s/%s' % (username, bucket), password)
    year = '%04d' % now.year
    month = '%02d' % now.month
    day = '%02d' % now.day
    ext = os.path.splitext(f.name)[1]
    ftp.mkd(year)
    ftp.cwd(year)
    ftp.mkd(month)
    ftp.cwd(month)
    ftp.mkd(day)
    ftp.cwd(day)
    town_pinyin = '-'.join(pypinyin.lazy_pinyin(town.name))
    ftp.mkd(town_pinyin)
    ftp.cwd(town_pinyin)
    school_pinyin = '-'.join(pypinyin.lazy_pinyin(school.name))
    ftp.mkd(school_pinyin)
    ftp.cwd(school_pinyin)
    filename = '%.06f%s' % (time.time(), ext)
    ftp.storbinary('STOR %s' % filename, f)
    path = '/%04d-%02d-%02d/%s/%s/%.06f%s' % (now.year, now.month, now.day,
                                              town_pinyin, school_pinyin,
                                              time.time(), ext)
    return path


def save_file(mac, f, in_computerclass=False, computerclass=None):
    # 获取云存储参数
    username = models.Setting.getvalue('cloud-service-username')
    password = models.Setting.getvalue('cloud-service-password')
    if not username or not password:
        if DEBUG:
            print u'获取云存储参数失败'
        return (False, u'获取云存储参数失败')
    if DEBUG:
        print u'DEBUG screen_upload ---4'
    # 根据mac查找班级
    if models.Setting.getvalue('desktop-preview-test') == 'True':
        test_flag = True
    else:
        test_flag = False
    try:
        if test_flag:
            q = models.Class.objects.all()
            c = q[random.randint(0, q.count() - 1)]
        else:
            t = models.Term.get_current_term_list()[0]
            try:
                c = models.Class.objects.get(classmacv2__mac=mac, grade__term=t)
            except:
                c = models.Class.objects.get(uuid=mac, grade__term=t)
            if c.grade.number == 13:
                # 前端的第一次截图是按照普通教室的标准传值
                computerclass = c.uuid
                in_computerclass = True
                c = _get_class(c)
                if not c:
                    return create_failure_dict(msg='上课班级获取失败')
        if DEBUG:
            print u'DEBUG screen_upload ---5'
    except Exception as e:
        logger.exception('')
        return (False, u'上课班级获取失败,客户端传的是上课的班级的Mac或UUID?')

    # 客户端上传文件的内容
    school = models.Group.objects.get(group_type='school')
    town = models.Group.objects.get(group_type='town')
    now = datetime.datetime.now()
    # 写入数据库记录
    grade = c.grade
    grade_number = str_util.grade_name_to_number(grade.name)
    class_number = str_util.class_name_to_number(c.name)
    s = datetime.datetime.combine(now.date(), datetime.time.min)
    e = datetime.datetime.combine(now.date(), datetime.time.max)

    if test_flag:
        objs = models.TeacherAbsentLog.objects.all()
    else:
        objs = models.TeacherLoginLog.objects.filter(
            lesson_period_start_time__lte=now.time(),
            lesson_period_end_time__gte=now.time(),
            weekday=now.strftime('%a').lower(),
            grade_name=grade.name,
            class_name=c.name,
            created_at__range=(s, e)
        )
    if not objs.exists():
        logger.warning('No TeacherLoginLog Exist class=%s, s=%s, e=%s', c.pk, s, e)
        return False, 'No TeacherLoginLog Exist'

    # 保存到upyun
    bucket = cloud_service.generate_bucket_name()
    path = _upload_file_http(bucket, username, password, f, town, school, now)

    try:
        if test_flag:
            q = objs[random.randint(0, q.count() - 1)]
        else:
            q = objs.first()
        if DEBUG:
            print u'DEBUG screen_upload ---6'
    except Exception as e:
        logger.exception('')
        return (False, u'教师登录记录获取失败,客户端传的是上课的班级的Mac或UUID?')

    lesson_name = q.lesson_name
    teacher_name = q.teacher_name
    lesson_period_sequence = q.lesson_period_sequence

    host = bucket + '.b0.upaiyun.com'
    url = path
    created_at = now
    pic = models.DesktopPicInfo(school=school, grade=grade,
                                grade_number=grade_number, class_uuid=c,
                                class_number=class_number,
                                lesson_name=lesson_name,
                                teacher_name=teacher_name,
                                lesson_period_sequence=lesson_period_sequence,
                                host=host,
                                url=url, created_at=created_at)
    pic.save()
    # 更新DesktopGlobalPreview
    q = models.DesktopGlobalPreview.objects.all()
    q = q.filter(pic__school=school, pic__grade=grade, pic__class_uuid=c)
    q.delete()
    dgp = models.DesktopGlobalPreview(pic=pic)
    dgp.save()

    if in_computerclass:
        if DEBUG:
            print u'DEBUG screen_upload ---6-1 in computerclass'
        # 电脑教室的截屏会在DesktopPicInfoTag表中生成一条记录
        # 同时也会在DesktopGlobalPreviewTag表生成实时时数据
        try:
            cc = models.Class.objects.get(uuid=computerclass)
            tag = models.DesktopPicInfoTag(bind_to=pic, created_by=cc)
            tag.save()
            models.DesktopGlobalPreviewTag(bind_to=dgp).save()
            if DEBUG:
                print u'DEBUG screen_upload ---6-1 success'
        except Exception as e:
            pass
    if DEBUG:
        print u'DEBUG screen_upload ---7'
        print u'save_file: 年级:', grade.name
        print u'save_file: 班级:', c.name
        print u'save_file: 课程:', lesson_name
        print u'save_file: 教师:', teacher_name
        print u'save_file: 星期:', now.strftime('%a').lower()
        print u'save_file: 节次:', lesson_period_sequence
    return (True, host + url)


def screen_upload(request, *args, **kwargs):
    if DEBUG:
        print u'DEBUG screen_upload ---0 --request'
        print u'DEBUG requesst.GET:', request.GET
        print u'DEBUG requesst.POST:', request.POST
        print u'DEBUG requesst.FILES:', request.FILES, '\n'
        print u'DEBUG screen_upload ---1 --begin'

    computerclass = request.POST.get('computer_class_uuid', request.POST.get('computerclass', None))
    if models.Setting.getvalue('server_type') != 'school':
        return create_failure_dict(msg='错误的服务器级别')
    try:
        if computerclass:
            f = ComputerclassUploadForm(request.POST, request.FILES)
            mac = request.POST.get('class_mac')
            in_computerclass = True
            if DEBUG:
                print u'DEBUG screen_upload ---2.1'
        else:
            f = UploadForm(request.POST, request.FILES)
            mac = request.POST.get('mac')
            in_computerclass = False
            if DEBUG:
                print u'DEBUG screen_upload ---2.2'

        if f.is_valid():
            if DEBUG:
                print u'DEBUG screen_upload ---3'
            is_success, url = save_file(mac, request.FILES['pic'], in_computerclass, computerclass)
            if is_success:
                if DEBUG:
                    print u'DEBUG screen_upload ---8 --end'
                url = 'http://' + url
                return create_success_dict(msg='upload successful!', url=url)
            if DEBUG:
                print u'DEBUG screen_upload failed -- 1'
            return create_failure_dict(msg=url)
        if DEBUG:
            print u'DEBUG screen_upload failed -- 2'
        return create_failure_dict(msg='form not valid', errors=f.errors)
    except upyun.UpYunServiceException, e:
        if DEBUG:
            print e
        return create_failure_dict(msg=e.err)
    except upyun.UpYunClientException, e:
        if DEBUG:
            print e
        return create_failure_dict(msg=str(e))
    except Exception as e:
        if DEBUG:
            print e
        logger.exception('')
        return create_failure_dict(msg=str(e))
