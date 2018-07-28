# coding=utf-8
import bz2
import ConfigParser
import inspect
import json
import logging
import os
import os.path
import platform
import pypinyin
import traceback
import urllib
import urllib2
import zipfile
from django.conf import settings
from django.db import connection
from django.db import models as django_models
from django.template import loader
from django.http.response import HttpResponse
from django.http.response import HttpResponseRedirect
from BanBanTong import constants
from BanBanTong.db import models
from machine_time_used import models as new_models
from BanBanTong.forms.class_mac import ClassFormSet
from BanBanTong.forms.class_mac import ClassUploadForm
from BanBanTong.forms.lesson_name import LessonNameFormSet
from BanBanTong.forms.lesson_name import LessonNameUploadForm
from BanBanTong.forms.lesson_period import LessonPeriodFormSet
from BanBanTong.forms.lesson_period import LessonPeriodUploadForm
from BanBanTong.forms.lesson_schedule import LessonScheduleUploadForm
from BanBanTong.forms.lesson_teacher import LessonTeacherUploadForm
from BanBanTong.forms.node import NodeForm
from BanBanTong.forms.setting import ServerInfoForm
from BanBanTong.forms.setting import StepForm
from BanBanTong.forms.teacher import TeacherUploadForm
from BanBanTong.forms.term import TermFormSet
from BanBanTong.forms.term import TermUploadForm
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import model_list_to_dict


logger = logging.getLogger(__name__)


def index(request, *args, **kwargs):
    if models.Setting.getvalue('installed') == 'True':
        return HttpResponseRedirect('/')
    template = loader.get_template('install.html')
    return HttpResponse(template.render({}))


def grade_class(request, *args, **kwargs):
    if request.method == 'POST':
        if models.Setting.getvalue('installed') == 'True':
            failure = '您已经配置过本服务器，无法重新配置！'
            return create_failure_dict(msg=failure)

        f = ClassFormSet(request.POST)
        if f.is_valid():
            # 删除旧数据进行全新安装
            cursor = connection.cursor()
            cursor.execute('DELETE FROM `Class`')
            cursor.execute('DELETE FROM `Grade`')
            for i in f.forms:
                i.save()
            install_step = models.Setting.objects.get(name='install_step')
            install_step.value = request.POST['install_step']
            install_step.save()
            return create_success_dict(msg='安装成功！')

        return create_failure_dict(msg='安装失败！',
                                   errors=f.errors)

    elif request.method == 'GET':
        if models.Setting.getvalue('installed') == 'True':
            return HttpResponseRedirect('/')

        q = models.Class.objects.all().values('grade__name', 'name')
        return create_success_dict(data=model_list_to_dict(q))


def grade_class_import(request, *args, **kwargs):
    if request.method == 'POST':
        if models.Setting.getvalue('installed') == 'True':
            failure = '您已经配置过本服务器，无法重新配置！'
            return create_failure_dict(msg=failure)
        f = ClassUploadForm(request.POST, request.FILES)
        if f.is_valid():
            classes = f.save()
            return create_success_dict(data=model_list_to_dict(classes))

        return create_failure_dict(msg='导入学校年级班级失败！',
                                   errors=f.errors)


def group_get_children(request):
    if request.method == 'GET':
        if models.Setting.getvalue('installed') == 'True':
            failure = '您已经配置过本服务器，无法重新配置！'
            return create_failure_dict(msg=failure)
        province_name = request.GET.get('province_name')
        city_name = request.GET.get('city_name')
        country_name = request.GET.get('country_name')
        q = None
        if province_name and city_name and country_name:
            q = models.GroupTB.objects.filter(parent__name=country_name,
                                              parent__parent__name=city_name)
            q = q.filter(parent__parent__parent__name=province_name)
            q = q.values('name')
        elif province_name and city_name:
            q = models.GroupTB.objects.filter(parent__name=city_name)
            q = q.filter(parent__parent__name=province_name)
            q = q.values('name')
        elif province_name:
            q = models.GroupTB.objects.filter(parent__name=province_name)
            q = q.values('name')
        else:
            q = models.GroupTB.objects.filter(parent_id__isnull=True)
            q = q.values('name')
        return create_success_dict(data={'children': model_list_to_dict(q)})


def lesson_name(request, *args, **kwargs):
    if request.method == 'POST':
        if models.Setting.getvalue('installed') == 'True':
            failure = '您已经配置过本服务器，无法重新配置！'
            return create_failure_dict(failure)

        f = LessonNameFormSet(request.POST)
        if f.is_valid():
            models.LessonName.objects.all().delete()  # 删除旧数据进行全新安装
            school = models.Group.objects.get(group_type='school')
            for i in f.forms:
                obj = i.save(commit=False)
                obj.school = school
                obj.save()
            install_step = models.Setting.objects.get(name='install_step')
            install_step.value = request.POST['install_step']
            install_step.save()
            return create_success_dict(msg='安装成功！')

        return create_failure_dict(msg='安装失败！',
                                   errors=f.errors)
    elif request.method == 'GET':
        if models.Setting.getvalue('installed') == 'True':
            return HttpResponseRedirect('/')

        q = models.LessonName.objects.all().values('name')
        return create_success_dict(data=model_list_to_dict(q))


def lesson_name_import(request, *args, **kwargs):
    if request.method == 'POST':
        if models.Setting.getvalue('installed') == 'True':
            failure = '您已经配置过本服务器，无法重新配置！'
            return create_failure_dict(msg=failure)
        f = LessonNameUploadForm(request.POST, request.FILES)
        if f.is_valid():
            lesson_names = f.save()
            return create_success_dict(data=model_list_to_dict(lesson_names))

        return create_failure_dict(msg='导入学校开课课程失败！',
                                   errors=f.errors)


def lesson_period(request, *args, **kwargs):
    if request.method == 'POST':
        if models.Setting.getvalue('installed') == 'True':
            failure = '您已经配置过本服务器，无法重新配置！'
            return create_failure_dict(failure)

        f = LessonPeriodFormSet(request.POST)
        if f.is_valid():
            models.LessonPeriod.objects.all().delete()  # 删除旧数据进行全新安装
            for i in f.forms:
                i.save()
            install_step = models.Setting.objects.get(name='install_step')
            install_step.value = request.POST['install_step']
            install_step.save()
            return create_success_dict(msg='安装成功！')

        return create_failure_dict(msg='安装失败！',
                                   errors=f.errors)
    elif request.method == 'GET':
        if models.Setting.getvalue('installed') == 'True':
            return HttpResponseRedirect('/')

        q = models.LessonPeriod.objects.all().values('sequence',
                                                     'start_time',
                                                     'end_time')
        return create_success_dict(data=model_list_to_dict(q))


def lesson_period_import(request, *args, **kwargs):
    if request.method == 'POST':
        if models.Setting.getvalue('installed') == 'True':
            failure = '您已经配置过本服务器，无法重新配置！'
            return create_failure_dict(msg=failure)
        f = LessonPeriodUploadForm(request.POST, request.FILES)
        if f.is_valid():
            objs = f.save()
            return create_success_dict(data=model_list_to_dict(objs))

        return create_failure_dict(msg='导入学校作息时间失败！',
                                   errors=f.errors)


def lesson_schedule_import(request, *args, **kwargs):
    if request.method == 'POST':
        if models.Setting.getvalue('installed') == 'True':
            failure = '您已经配置过本服务器，无法重新配置！'
            return create_failure_dict(msg=failure)
        f = LessonScheduleUploadForm(request.POST, request.FILES)
        if f.is_valid():
            objs = f.save()
            return create_success_dict(data=model_list_to_dict(objs))

        return create_failure_dict(msg='导入班级课程表失败！',
                                   errors=f.errors)


def lesson_teacher_import(request, *args, **kwargs):
    if request.method == 'POST':
        if models.Setting.getvalue('installed') == 'True':
            failure = '您已经配置过本服务器，无法重新配置！'
            return create_failure_dict(msg=failure)
        f = LessonTeacherUploadForm(request.POST, request.FILES)
        if f.is_valid():
            objs = f.save()
            return create_success_dict(data=model_list_to_dict(objs))

        return create_failure_dict(msg='导入班级课程授课老师失败！',
                                   errors=f.errors)


def node(request):
    if request.method == 'POST':
        if models.Setting.getvalue('installed') == 'True':
            failure = '您已经配置过本服务器，无法重新配置！'
            return create_failure_dict(msg=failure)
        f = NodeForm(request.POST)
        if f.is_valid():
            f.save()
            try:
                install_step = models.Setting.objects.get(name='install_step')
                install_step.value = request.POST.get('install_step')
                install_step.save()
            except:
                pass
            return create_success_dict(msg='安装成功！')
        return create_failure_dict(msg='安装失败！',
                                   errors=f.errors)


def _truncate_tables():
    def _work(cursor, modelbase, classname):
        m = getattr(modelbase, classname)
        if m.objects.exists():
            logger.debug('truncating %s', classname)
            cursor.execute('TRUNCATE TABLE `%s`' % m._meta.db_table)

    logger.debug('will truncate tables...')
    # 清空数据进行全新安装
    cursor = connection.cursor()
    cursor.execute('SET FOREIGN_KEY_CHECKS=0')
    tables = []
    # 分离各app后,这里的models就会有多个,采用遍历models的方式获取models list
    model_lst = (models, new_models)

    for current_model in model_lst:
        for k in current_model.__dict__:
            if k in ('InitModel', 'BaseModel', 'NewBaseModel',
                     'CountryToSchoolBaseModel', 'GroupTB',
                     'Setting', 'TeachLog'):
                continue
            m = getattr(current_model, k)
            if not inspect.isclass(m):
                continue
            if issubclass(m, (models.BaseModel, new_models.NewBaseModel, models.CountryToSchoolBaseModel,
                              django_models.Model)):
                tables.append(k)

        while tables:
            _work(cursor, current_model, tables.pop())

    sql = """DELETE FROM Setting WHERE name NOT IN
      ('migration_step', 'sync_server_host',
      'sync_server_port', 'sync_server_key',
      'host', 'host_new', 'port', 'sync_node_id')"""
    cursor.execute(sql)
    cursor.execute('SET FOREIGN_KEY_CHECKS=1')


def restore(request, *args, **kwargs):
    '''系统重装后，输入上级服务器信息，从上级恢复旧数据'''
    if request.method == 'POST':
        if models.Setting.getvalue('installed') == 'True':
            failure = '您已经配置过本服务器，无法重新配置！'
            return create_failure_dict(msg=failure)
        try:
            host = request.POST.get('host')
            port = request.POST.get('port')
            key = request.POST.get('key')
            if not host or not port or not key:
                return create_failure_dict(msg='缺少参数！')
            url = 'http://%s:%s/system/node/download/' % (host, port)
            data = {'communicate_key': key}
            ret = urllib2.urlopen(url, urllib.urlencode(data)).read()
            data = bz2.decompress(ret)
            lines = data.split('\n')
            # 清空数据库
            _truncate_tables()
            meta = {}
            for line in lines:
                if len(line) == 0:
                    continue
                if line.startswith('meta:'):
                    meta = json.loads(line[5:])
                else:
                    models.SyncLogPack.unpack_log('add', line)
            # 清空SyncLog
            models.SyncLog.objects.all().delete()
            # 设置SyncLog AUTO_INCREMENT
            cursor = connection.__cursor()
            n = meta['last_upload_id'] + 1
            cursor.execute('ALTER TABLE SyncLog AUTO_INCREMENT=%d' % n)
            return HttpResponseRedirect('/')
        except:
            traceback.print_exc()


def _package_client_file(client_file_name='DadsTerminalSetup.exe'):
    host = models.Setting.objects.get(name='host').value
    port = models.Setting.objects.get(name='port').value
    conf_file = os.path.join(settings.PUBLIC_ROOT, 'settings.ini')
    f = open(conf_file, 'w')
    f.write('[server]\nip=%s\nport=%s\nrequest_times=3' % (host, port))
    f.close()
    zip_file = os.path.join(settings.PUBLIC_ROOT, 'client.zip')
    client_file = os.path.join(settings.PUBLIC_ROOT, client_file_name)
    z = zipfile.ZipFile(zip_file, 'w')
    z.write(conf_file, os.path.basename(conf_file))
    try:
        z.write(client_file, os.path.basename(client_file))
    except:
        pass
    z.close()
    # 打包USBKey文件
    zip_file = os.path.join(settings.PUBLIC_ROOT, 'usbkey.zip')
    client_file = os.path.join(settings.PUBLIC_ROOT, 'OeCreatekey.exe')
    z = zipfile.ZipFile(zip_file, 'w')
    z.write(conf_file, os.path.basename(conf_file))
    try:
        z.write(client_file, os.path.basename(client_file))
    except:
        pass
    z.close()


def _create_default_assettype():
    if models.Setting.getvalue('server_type') != 'school':
        return
    school = models.Group.objects.get(group_type='school')
    models.AssetType(name='台式计算机', icon='pc', unit_name='台',
                     school=school).save()
    models.AssetType(name='电子白板', icon='whiteboard', unit_name='块',
                     school=school).save()
    models.AssetType(name='投影仪', icon='projector', unit_name='台',
                     school=school).save()
    models.AssetType(name='大屏显示器', icon='lfd', unit_name='台',
                     school=school).save()
    models.AssetType(name='大屏一体机', icon='yitiji', unit_name='台',
                     school=school).save()
    models.AssetType(name='视频展台', icon='visual_presenter', unit_name='台',
                     school=school).save()
    models.AssetType(name='教室中控台', icon='center_console', unit_name='台',
                     school=school).save()
    models.AssetType(name='笔记本', icon='notebook', unit_name='台',
                     school=school).save()
    models.AssetType(name='打印机', icon='printer', unit_name='台',
                     school=school).save()
    models.AssetType(name='瘦终端', icon='thin_terminal', unit_name='台',
                     school=school).save()
    models.AssetType(name='网络交换机', icon='switchboard', unit_name='台',
                     school=school).save()
    models.AssetType(name='路由器', icon='router', unit_name='台',
                     school=school).save()
    models.AssetType(name='服务器', icon='server', unit_name='台',
                     school=school).save()
    models.AssetType(name='平板电脑', icon='pad', unit_name='台',
                     school=school).save()

# 2014-06-25 初始化区县时添加 newlessontype


def _create_default_newlessontype():
    if models.Setting.getvalue('server_type') not in ('country',):
        return

    country = models.Group.objects.get(group_type='country')

    models.NewLessonType(name='小学', country=country).save()
    models.NewLessonType(name='初中', country=country).save()
    models.NewLessonType(name='高中', country=country).save()


def _create_default_newlessonname():
    from BanBanTong.forms.new_lesson_name import NewLessonNameForm
    if models.Setting.getvalue('server_type') not in ('country',):
        return
    newlessonnames = [
        (u'科学', u'小学'),
        (u'品德与生活', u'小学'),
        (u'品德与社会', u'小学'),
        (u'综合实践活动', u'小学'),

        (u'语文', u'小学', u'初中', u'高中'),
        (u'数学', u'小学', u'初中', u'高中'),
        (u'英语', u'小学', u'初中', u'高中'),
        (u'音乐', u'小学', u'初中', u'高中'),
        (u'体育', u'小学', u'初中', u'高中'),
        (u'美术', u'小学', u'初中', u'高中'),
        (u'信息技术', u'小学', u'初中', u'高中'),

        (u'物理', u'初中', u'高中'),
        (u'化学', u'初中', u'高中'),
        (u'生物', u'初中', u'高中'),
        (u'历史', u'初中', u'高中'),
        (u'地理', u'初中', u'高中'),
        (u'思想品德', u'初中', u'高中')
    ]

    for item in newlessonnames:
        f = NewLessonNameForm({'name': item[0]})
        if f.is_valid():
            obj = f.save()
            types = item[1:]
            for type in types:
                m = models.NewLessonNameType(newlessonname=obj,
                                             newlessontype=models.NewLessonType.objects.get(name=type))
                m.save()


def _create_default_resourcefrom_resourcetype():
    if models.Setting.getvalue('server_type') not in ('country'):
        return

    country = models.Group.objects.get(group_type='country')
    models.ResourceFrom(country=country, value='中央电化教育馆教学资源库').save()
    models.ResourceFrom(country=country, value='互联网资源').save()
    models.ResourceFrom(country=country, value='课内网资源').save()
    models.ResourceFrom(country=country, value='国家基础教育资源网').save()
    models.ResourceFrom(country=country, value='优课网资源').save()
    models.ResourceFrom(country=country, value='凯瑞教学资源').save()
    models.ResourceFrom(country=country, value='电信网教育资源').save()
    models.ResourceFrom(country=country, value='教材配套自带').save()
    models.ResourceFrom(country=country, value='农村中小学现代远程教育资源').save()
    models.ResourceFrom(country=country, value='教学点数字教育资源全覆盖').save()
    models.ResourceFrom(country=country, value='自制课件').save()
    models.ResourceFrom(country=country, value='其他资源').save()

    models.ResourceType(country=country, value='音频').save()
    models.ResourceType(country=country, value='音视频').save()
    models.ResourceType(country=country, value='PPT幻灯片').save()
    models.ResourceType(country=country, value='文档').save()
    models.ResourceType(country=country, value='动画片').save()
    models.ResourceType(country=country, value='互动课件').save()
    models.ResourceType(country=country, value='其他').save()

    # if models.Setting.getvalue('server_type') != 'school':
    #    return
    #school = models.Group.objects.get(group_type='school')
    #models.ResourceFrom(school=school, value='课内网资源').save()
    #models.ResourceFrom(school=school, value='国家基础教育资源').save()
    #models.ResourceFrom(school=school, value='优课网资源').save()
    #models.ResourceFrom(school=school, value='凯瑞教学资源').save()
    #models.ResourceFrom(school=school, value='电信网教育资源').save()
    #models.ResourceFrom(school=school, value='教材配套光盘').save()
    #models.ResourceFrom(school=school, value='现代远程教育资源').save()
    #models.ResourceFrom(school=school, value='自制课件').save()
    #models.ResourceFrom(school=school, value='其他资源').save()
    #models.ResourceType(school=school, value='音频').save()
    #models.ResourceType(school=school, value='音视频').save()
    #models.ResourceType(school=school, value='PPT幻灯片').save()
    #models.ResourceType(school=school, value='文档').save()
    #models.ResourceType(school=school, value='动画片').save()
    #models.ResourceType(school=school, value='互动课件').save()
    #models.ResourceType(school=school, value='其他').save()


def _modify_update_path(province, city, country):
    """根据配置完成的省市区县来修改升级路径"""
    if platform.system() == 'Linux':
        return
    path = constants.BANBANTONG_VERSION_FILE
    config_file = ConfigParser.RawConfigParser()
    config_file.read(path)
    version = config_file.get('Version', 'Version number')
    version = version.split('.')[0]
    path = constants.DADS_SETTING_FILE
    logger.debug('DADS_SETTING_FILE: %s', path)
    config_file = ConfigParser.RawConfigParser()
    config_file.read(path)
    # ip=update.os-easy.com/bbt/OeWebServer
    # ip=update.os-easy.com/bbt/v3/hubeisheng/wuhanshi/jianganqu/OeWebServer
    ip = config_file.get('server', 'ip')
    if ''.join(pypinyin.lazy_pinyin(province)) in ip:
        # 已经修改过升级路径
        return
    segments = ip.split('/')
    last_seg = segments[-1]
    segments = segments[:-1]
    segments.append(version)
    segments.append(''.join(pypinyin.lazy_pinyin(province)))
    if city:
        segments.append(''.join(pypinyin.lazy_pinyin(city)))
    if country:
        segments.append(''.join(pypinyin.lazy_pinyin(country)))
    segments.append(last_seg)
    config_file.set('server', 'ip', '/'.join(segments))
    with open(path, 'w') as new_config_file:
        config_file.write(new_config_file)


def serverinfo(request, *args, **kwargs):
    '''安装第一步：设置服务器类型和地区'''
    if request.method == 'POST':
        if models.Setting.getvalue('installed') == 'True':
            failure = '您已经配置过本服务器，无法重新配置！'
            return create_failure_dict(msg=failure)

        # 清空数据进行全新安装
        _truncate_tables()
        f = ServerInfoForm(request.POST)
        if f.is_valid():
            f.save()
            _create_default_assettype()
            _create_default_resourcefrom_resourcetype()
            # 2014-06-26 init newlessontype
            _create_default_newlessontype()
            _create_default_newlessonname()
            province = request.POST.get('province')
            city = request.POST.get('city')
            country = request.POST.get('country')
            if not constants.NO_MODIFY_UPDATE_PATH:
                _modify_update_path(province, city, country)
            if models.Setting.getvalue('server_type') != 'school':
                return create_success_dict(msg='安装成功！')
            _package_client_file()
            return create_success_dict(msg='安装成功！')
        else:
            logger.debug('安装失败：%s', str(f.errors))
            return create_failure_dict(msg='安装失败！',
                                       errors=f.errors)

    elif request.method == "GET":
        if models.Setting.getvalue('installed') == 'True':
            return HttpResponseRedirect('/')

        condition = ['server_type', 'school', 'province', 'city',
                     'country', 'town', 'host', 'port']
        q = models.Setting.objects.filter(name__in=condition).values('name',
                                                                     'value')
        return create_success_dict(data=model_list_to_dict(q))


def step(request, *args, **kwargs):
    if request.method == 'POST':
        if models.Setting.getvalue('installed') == 'True':
            failure = '您已经配置过本服务器，无法重新配置！'
            return create_failure_dict(msg=failure)

        f = StepForm(request.POST)
        if f.is_valid():
            f.save()
            return create_success_dict(msg='安装成功！')

        return create_failure_dict(msg='安装失败！',
                                   errors=f.errors)

    elif request.method == 'GET':
        install_step = models.Setting.getvalue('install_step')
        return create_success_dict(install_step=install_step)


def teacher_import(request, *args, **kwargs):
    if request.method == 'POST':
        if models.Setting.getvalue('installed') == 'True':
            failure = '您已经配置过本服务器，无法重新配置！'
            return create_failure_dict(msg=failure)
        try:
            f = TeacherUploadForm(request.POST, request.FILES)
            if f.is_valid():
                teachers = f.save()
                ret = create_success_dict(data=model_list_to_dict(teachers))
                return ret
            else:
                return create_failure_dict(msg='导入教职人员基础信息失败！',
                                           errors=f.errors)
        except:
            traceback.print_exc()


def term(request, *args, **kwargs):
    if request.method == 'POST':
        if models.Setting.getvalue('installed') == 'True':
            failure = '您已经配置过本服务器，无法重新配置！'
            return create_failure_dict(msg=failure)

        f = TermFormSet(request.POST)
        if f.is_valid():
            models.Term.objects.all().delete()  # 删除旧数据进行全新安装
            for i in f.forms:
                i.save()
            install_step = models.Setting.objects.get(name='install_step')
            install_step.value = request.POST['install_step']
            install_step.save()
            return create_success_dict(msg='安装成功！')

        return create_failure_dict(msg='安装失败！',
                                   errors=f.errors)

    elif request.method == "GET":
        if models.Setting.getvalue('installed') == 'True':
            return HttpResponseRedirect('/')

        q = models.Term.objects.all().values('term_type', 'start_date',
                                             'end_date', 'school_year')
        return create_success_dict(data=model_list_to_dict(q))


def term_import(request, *args, **kwargs):
    if request.method == 'POST':
        if models.Setting.getvalue('installed') == 'True':
            failure = '您已经配置过本服务器，无法重新配置！'
            return create_failure_dict(msg=failure)
        f = TermUploadForm(request.POST, request.FILES)
        if f.is_valid():
            terms = f.save()
            return create_success_dict(data=model_list_to_dict(terms))

        return create_failure_dict(msg='导入学年学期失败！',
                                   errors=f.errors)
