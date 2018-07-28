# coding=utf-8
import datetime
import logging
import hashlib
import os
import StringIO
from django import forms
from django.http.response import HttpResponse
from django.template import loader
from BanBanTong.db import models
from BanBanTong.utils import cloud_service
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from django.conf import settings
DEBUG = settings.DEBUG
logger = logging.getLogger(__name__)


class ComputerclassUploadForm(forms.ModelForm):
    #teacherloginlog = forms.CharField()
    class_mac = forms.CharField()

    class Meta:
        model = models.CourseWare
        fields = ['title', 'file_name']

    def clean_mac(self):
        mac = self.cleaned_data['class_mac']

        if models.ClassMacV2.objects.filter(mac=mac).count() == 0:
            if models.ClassMacV2.objects.filter(class_uuid=mac).count() == 0:
                raise forms.ValidationError(u'不存在该绑定班级MAC')

        return mac


# class UploadForm(forms.Form):
#    mac = forms.CharField()
#    courseware = forms.FileField()

class UploadForm(forms.ModelForm):
    #teacherloginlog = forms.CharField()
    mac = forms.CharField()

    class Meta:
        model = models.CourseWare
        fields = ['title', 'file_name']

    def clean_mac(self):
        mac = self.cleaned_data['mac']

        if models.ClassMacV2.objects.filter(mac=mac).count() == 0:
            if models.ClassMacV2.objects.filter(class_uuid=mac).count() == 0:
                raise forms.ValidationError(u'不存在该绑定班级MAC')

        return mac

    # def clean_teacherloginlog(self):
    #    teacherloginlog = self.cleaned_data['teacherloginlog']
    #
    #    if models.TeacherLoginLog.objects.filter(uuid=teacherloginlog).count() != 1:
    #        raise forms.ValidationError(u'不存在该老师登录记录')

    #    return teacherloginlog


def upload_test(request):
    template = loader.get_template('courseware.html')

    #last_obj = models.TeacherLoginLog.objects.last()

    form = UploadForm(initial={'title': u'测试TITLE', 'mac': u'08-00-27-3C-E3-13'})

    return HttpResponse(template.render({'form': form}))


def check_md5(request):
    '''
        前端校验课件是否有处理过
        # existing : 0(无文件无纪录) , 1(有文件无纪录) , 2(有文件有纪录)
    '''
    md5 = request.GET.get('md5').strip().upper()
    mac = request.GET.get('mac').strip().upper()
    term_uuid = request.GET.get('term_uuid', make_term_uuid())

    if not courseware_exist(md5):
        # print '无重复的md5，可以上传'
        return create_success_dict(existing=0,
                                   md5=md5,
                                   mac=mac,
                                   msg='无重复的md5，可以上传')
    else:
        if not teacherloginlogcourseware_exist(md5, mac, term_uuid):
            # print '有md5，但无该老师上课纪录'
            return create_success_dict(existing=1,
                                       md5=md5,
                                       mac=mac,
                                       msg='有md5，但无该老师上课纪录')
        else:
            # print '有md5，同时也有该老师上课纪录'
            return create_success_dict(existing=2,
                                       md5=md5,
                                       mac=mac,
                                       msg='有md5，同时也有该老师上课纪录')


# def _save_file(file_path, file_obj):
#    with open(file_path, 'wb') as f:
#        for chunk in file_obj.chunks():
#            f.write(chunk)


def make_md5_from_file(file_obj):
    '''计算上传文件的MD5'''
    data = StringIO.StringIO(file_obj.read())

    m = hashlib.md5()

    m.update(data.read())

    return m.hexdigest().upper()


def courseware_exist(md5):
    '''课件是否存在'''
    try:
        return models.CourseWare.objects.get(md5=md5)
    except Exception:
        return None


def teacherloginlogcourseware_exist(md5, mac, term_uuid):
    '''课件对应的登录信息是否存在'''
    try:
        return models.TeacherLoginLogCourseWare.objects.get(courseware__md5=md5, teacherloginlog=get_teacherloginlog(mac, term_uuid))
    except Exception:
        return None


def get_teacherloginlog(mac, term_uuid):
    '''
        通过MAC来找到对应的老师登录信息
        mac -> class
        1.先找到该班级的所有登录记录
        2.再去看当天登录的信息
        3.再匹配当前节次
    '''
    try:
        class_uuid = models.ClassMacV2.objects.get(mac=mac, class_uuid__grade__term__uuid=term_uuid).class_uuid
        # 通过mac找到teacherloginlog
        now = datetime.datetime.now()
        tomorrow = now + datetime.timedelta(days=1)
        logs = models.TeacherLoginLog.objects.filter(class_uuid=class_uuid)
        teacherloginlog = logs.get(created_at__range=(now.date(), tomorrow.date()), lesson_period_start_time__lte=now.time(), lesson_period_end_time__gte=now.time())
    except Exception:
        teacherloginlog = None

    return teacherloginlog


def make_term_uuid():
    if models.Setting.getvalue('server_type') == 'school':
        try:
            school = models.Group.objects.get(group_type='school')
        except Exception:
            return create_failure_dict(msg='学校错误')
        terms = models.Term.get_current_term_list(school=school)
        if terms:
            return terms[0].uuid
    else:
        return create_failure_dict(msg='非校级服务器!')


def upload(request, *args, **kwargs):
    # if models.Setting.getvalue('server_type') != 'school':
    #    print '错误的服务器级别'
    #    return create_failure_dict(msg='错误的服务器级别')
    # print request.POST
    # print request.FILES
    computerclass = request.POST.get('computer_class_uuid', request.POST.get('computerclass', None))
    # if DEBUG:
    #     print u'DEBUG 课件上传'
    #     print u'DEBUG requests'
    #     print request.POST
    #     print request.GET
    #     print request.FILES
    #     print '\n\n\n'
    try:
        if computerclass:
            f = ComputerclassUploadForm(request.POST)
        else:
            #f = UploadForm(request.POST, request.FILES)
            f = UploadForm(request.POST)
        if f.is_valid():
            file_obj = request.FILES['file_name']
            #teacherloginlog_uuid = request.POST['teacherloginlog']
            title = request.POST.get('title', u'')
            mac = request.POST.get('mac', u'')
            md5 = request.POST.get('md5', make_md5_from_file(file_obj))
            term_uuid = request.POST.get('term_uuid', make_term_uuid())

            courseware = courseware_exist(md5)
            if not courseware:
                courseware = f.save()
                courseware.md5 = md5
                #courseware.size = u'%sB' % os.path.getsize(courseware.file_name.name)
                courseware.size = u'%sB' % file_obj.size
                ext = os.path.splitext(title)[1]
                key = cloud_service.qiniu_upload_fileobj(file_obj, 'oebbt-sqlbak', ext)
                url = 'http://oebbt-sqlbak.qiniudn.com/' + key
                courseware.qiniu_url = url
                courseware.save()
                # 上传到七牛
                # print '文件上传成功'

            if teacherloginlogcourseware_exist(md5, mac, term_uuid):
                return create_failure_dict(msg='该节次上的课件信息已存在!')
            else:
                # 关联 teacherloginlog
                teacherloginlog_obj = get_teacherloginlog(mac, term_uuid)
                if teacherloginlog_obj:
                    models.TeacherLoginLogCourseWare.objects.create(courseware=courseware, teacherloginlog=teacherloginlog_obj)
                    return create_success_dict(msg='成功纪录该节次的课件信息.')
                else:
                    return create_failure_dict(msg='无上课登录信息')
        else:
            # print '参数错误:', f.errors
            return create_failure_dict(msg='参数错误', errors=f.errors)
    except Exception as e:
        logger.exception(e)
        return create_failure_dict(msg=str(e))
