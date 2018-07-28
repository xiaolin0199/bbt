# coding=utf-8
import datetime
import os
import hashlib
import cPickle as pickle
import platform
import json
import socket

from django.db.models import Q
from django.core.cache import cache
from django.http.response import HttpResponse
from django.template import loader

from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import model_list_to_dict
from BanBanTong.utils.zmq_service import send_msg


def _get_status(c):
    '''
        获取指定班级的登录状态（X年级X班、是否在线、MAC）
    '''
    ret = {'grade_name': c.grade.name, 'class_name': c.name,
           'online': False, 'mac': None, 'ip': None, 'token': None,
           'teacher': u'', 'lesson_name': u'', 'inclass': False}

    # 1 电脑教室客户端
    if c.grade.number == 13:
        now = datetime.datetime.now()
        key = 'class-%s-active-time' % c.uuid
        value = cache.get(key)
        if value:
            ret['online'] = True

        try:
            ret['mac'] = c.mac()
            ret['ip'] = c.ip()
            token = '%s-%s-%s-%s' % ('class', c.mac(), c.ip(), str(now))
            token = hashlib.sha1(token).hexdigest()
            ret['token'] = token

            cc = models.ComputerClass.objects.get(class_bind_to=c)
            started, log = cc.get_status()
            if started:
                ret['teacher'] = log.teacher.name
                ret['lesson_name'] = log.lesson_name
                ret['inclass'] = True
        except Exception as e:
            ret['#error'] = str(e)
            pass

        return ret

    # 2 普通教室的客户端
    now = datetime.datetime.now()
    # cache内有状态（90秒内活动）的班级都判定为在线
    key = 'class-%s-active-time' % c.uuid
    value = cache.get(key)
    if value:
        try:
            value = json.loads(value)
            if value.get('class_client_online', False):
                ret['online'] = True

        except Exception as e:
            ret['#error'] = str(e)
            pass

    # MAC(申报了的就会绑定MAC)
    try:
        obj = models.ClassMacV2.objects.get(class_uuid=c)
        ret['mac'] = obj.mac
        ret['ip'] = obj.ip
        token = '%s-%s-%s-%s' % ('class', obj.mac, obj.ip, str(now))
        token = hashlib.sha1(token).hexdigest()
        ret['token'] = token

        # is_current, ls = simplecache.LessonSchedule.get_current(c)
        # if ls:
        #     q = models.LessonTeacher.objects.filter(class_uuid=c,
        #                                             lesson_name__name=ls['lesson_name__name'])
        #     if q.count() == 0:
        #         teacher = u''
        #     else:
        #         teacher = q[0].teacher.name
        #
        #     ret['teacher'] = teacher
        #     ret['lesson_name'] = ls['lesson_name__name']
        #
        #     #登陆了是否上课
        #     now = datetime.datetime.now()
        #     s = datetime.datetime.combine(now.date(), datetime.time.min)
        #     e = datetime.datetime.combine(now.date(), datetime.time.max)
        #     q = models.TeacherLoginLog.objects.filter(created_at__range=(s, e),
        #                  lesson_period_start_time__lte=now.time(),
        #                  lesson_period_end_time__gte=now.time(),
        #                  class_uuid=c)
        #     if q.exists() and ret['online']:
        #         ret['inclass'] = True
        started, log = c.get_status()
        if started:
            ret['teacher'] = log.teacher.name
            ret['lesson_name'] = log.lesson_name
            ret['inclass'] = True

    except Exception as e:
        ret['#error'] = str(e)
        pass

    return ret


def list_system(request):
    '''
        终端远程关机重启功能列表
    '''
    # TODO 2015-03-23
    # 基于浏览器对所有校内终端进行远程操作，具体功能包括：远程关机、远程重启、
    # 终端定时关机设置(新)
    #
    # 点击按钮执行功能时，有管理员二次确认是否执行操作对话框；管理员二次询问时，
    # 对话框中有终端执行执行方式选择框【终端咨询模式（默认）、强制执行模式】；
    # 终端咨询模式时，终端在接到服务器重启或关机指令后，会弹出提示框倒计时30秒
    # 功能执行提示，终端用户可选择取消执行；强制执行模式时，终端则弹出提示框倒计
    # 时30秒功能执行提示，终端不可取消执行。
    #
    # 定时关机功能对所有申报成功的终端生效，用户可选择开启或关闭该功能，
    # 默认为关闭。本功能可设置所有连线终端，在下次某指定时间以某模式
    #【终端咨询模式（默认）、强制执行模式】执行关机操作，或者每日循环执行；
    if models.Setting.getvalue('server_type') != 'school':
        return create_failure_dict(msg='仅校服务器可用')

    try:
        school = models.Group.objects.get(group_type='school')
    except:
        return create_failure_dict(msg='学校获取失败')

    try:
        term = models.Term.get_current_term_list(school)[0]
    except:
        return create_failure_dict(msg='当前时间不在任何学期内')

    grade_name = request.GET.get('grade_name', '')

    # 获取当前学年学期的班级(包括电脑教室)
    q = models.Class.objects.filter(grade__term=term)

    if grade_name:
        q = q.filter(grade__name=grade_name)

    records = []

    for i in q:
        records.append(_get_status(i))

    data = {'records': records}

    return create_success_dict(data=data)


def scheduler_shutdown_get(request):
    '''
        前端使用api,返回数据库的定时关机设置
    '''
    if models.Setting.getvalue('server_type') != 'school':
        return create_failure_dict(msg='仅校服务器可用')

    data = {}

    data['scheduler_shutdown_switch'] = models.Setting.getvalue('scheduler_shutdown_switch')
    data['scheduler_shutdown_clock'] = models.Setting.getvalue('scheduler_shutdown_clock')
    data['scheduler_shutdown_delay'] = models.Setting.getvalue('scheduler_shutdown_delay')
    data['scheduler_shutdown_next_run'] = models.Setting.getvalue('scheduler_shutdown_next_run')

    return create_success_dict(data=data)


def scheduler_shutdown(request):
    '''
        定时关机信息设置
        scheduler_shutdown_switch  定时开关(默认为0不开启)
        scheduler_shutdown_clock  定时关机日期(如19:00)
        Scheduler_shutdown_delay  定时关机执行时延时(0为即时, 默认为30秒交互模式)
    '''
    if models.Setting.getvalue('server_type') != 'school':
        return create_failure_dict(msg='仅校服务器可用')

    if request.method == 'POST':
        post_data = request.POST.copy()

        scheduler_shutdown_switch = post_data.get('scheduler_shutdown_switch', '0')
        scheduler_shutdown_clock = post_data.get('scheduler_shutdown_clock', '12:00:00')
        scheduler_shutdown_delay = post_data.get('scheduler_shutdown_delay', '30')

        if not isinstance(scheduler_shutdown_switch, str):
            scheduler_shutdown_switch = str(scheduler_shutdown_switch)

        if isinstance(scheduler_shutdown_clock, datetime.time):
            scheduler_shutdown_clock = datetime.time.strftime(scheduler_shutdown_clock, '%H:%M:%S')

        if not isinstance(scheduler_shutdown_delay, str):
            scheduler_shutdown_delay = str(scheduler_shutdown_delay)

        if scheduler_shutdown_clock:  # 如果没有定时关机日期则不操作
            # 计算出下次运行时间
            now = datetime.datetime.now()
            now_date = now.date()
            clock = datetime.datetime.strptime(scheduler_shutdown_clock, '%H:%M:%S').time()

            next_run = datetime.datetime(year=now_date.year, month=now_date.month, day=now_date.day, hour=clock.hour, minute=clock.minute, second=clock.second)
            # 如果当前时间已超过了定时，则下次运行推到明天
            if now > next_run:
                next_run += datetime.timedelta(days=1)

            # 下次关机时间
            post_data['scheduler_shutdown_next_run'] = datetime.datetime.strftime(next_run, '%Y-%m-%d %H:%M:%S')

            # 实际情况就是当switch==‘0’时，只改变这个值，其他的设置不变
            if scheduler_shutdown_switch == '0':
                post_data = {}
                post_data['scheduler_shutdown_switch'] = '0'

            # 保存前台更新设置信息
            for key, value in post_data.iteritems():
                obj, c = models.Setting.objects.get_or_create(
                    name=key,
                    defaults={
                        'value': value
                    }
                )
                if not c:
                    setattr(obj, 'value', value)
                    obj.save()

            return create_success_dict(msg=u'定时关机设置成功', data=post_data)

        return create_failure_dict(msg='定时关机的时间必须指定')


def run_shutdown(request):
    '''
        服务器端发送运维指令 (关机)
    '''
    if request.method == 'POST':
        post_data = request.POST

        # mac 集合
        macfilter = post_data.getlist('mac')
        delay = post_data.get('delay', '30')  # 0为NOW 比如 30为 延时30秒
        # PUB shutdown msg to zmq
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 9528))

        # time.sleep(2)
        msg = 'shutdown###%s###%s' % (delay, pickle.dumps(macfilter))
        sock.send(msg)
        # sock.send('shutdown')

        #send_msg(type='shutdown', macfilter=macfilter)

        return create_success_dict(msg=u'关机指令发送成功', data=post_data)


def run_reboot(request):
    '''
        服务器端发送运维指令 (重启)
    '''
    if request.method == 'POST':
        post_data = request.POST

        # mac 集合
        macfilter = post_data.getlist('mac')
        delay = post_data.get('delay', '30')  # 0为NOW 比如 30为 延时30秒
        # PUB shutdown msg to zmq
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 9528))

        # time.sleep(2)
        # 将type='reboot', macfilter=macfilter整合成一个字串
        msg = 'reboot###%s###%s' % (delay, pickle.dumps(macfilter))
        sock.send(msg)
        #send_msg(type='reboot', macfilter=macfilter)

        return create_success_dict(msg=u'重启指令发送成功', data=post_data)


def list_vnc(request):
    '''
        终端协助功能列表
    '''
    # TODO 2015-03-23
    # 视图界面默认显示在线终端，并可按年级分组进行过滤显示(新)，
    # 另可选择显示所有已经申报的教室终端。
    if models.Setting.getvalue('server_type') != 'school':
        return create_failure_dict(msg='仅校服务器可用')

    try:
        school = models.Group.objects.get(group_type='school')
    except:
        return create_failure_dict(msg='学校获取失败')

    try:
        term = models.Term.get_current_term_list(school)[0]
    except:
        return create_failure_dict(msg='当前时间不在任何学期内')

    grade_name = request.GET.get('grade_name', '')

    q = models.Class.objects.filter(grade__term=term)

    if grade_name:
        q = q.filter(grade__name=grade_name)

    records = []
    others = []
    now = datetime.datetime.now()

    if platform.system() == 'Linux':
        platform_system = 'linux'
    else:
        platform_system = 'win'

    # 已申报的返回各种状态
    for i in q:
        if i.classmacv2_set.all():
            records.append(_get_status(i))

    # 未申请的IP心跳, 如果有分类过滤的话，则不显示未申报的终端
    if not grade_name:
        value = cache.get('class_noreport_heartbeat_ip')
        if value:
            value = pickle.loads(value)
            for ip in value:
                token = '%s-%s-%s' % ('class', ip, str(now))
                token = hashlib.sha1(token).hexdigest()
                others.append({'token': token, 'ip': ip, 'online': True})

        records.extend(others)

    # 生成最新的 vnc_tokens 文件
    ini_file = os.path.join(constants.VNC_INI_PATH, 'vnc.ini')
    # 首先找到ini文件已存在的IP，这样不改变token
    # 解析配置文件
    current_ini_ip = {}

    try:
        with open(ini_file, 'r') as f:
            for line in f.readlines():
                token, ip_port = line.split(' ')
                ip, port = ip_port.split(':')
                token = token.replace(':', '')
                #####
                current_ini_ip[str(ip)] = token
    except Exception:
        pass

    with open(ini_file, 'w') as f:
        for one in records:
            if not one['online']:
                continue

            token = one['token']
            ip = one['ip']

            # 已存在的IP不改变token
            if str(ip) in current_ini_ip.keys():
                token = current_ini_ip[str(ip)]
                one['token'] = token

            if token and ip:
                line = '%s: %s:5900' % (token, ip)
                f.write(line)
                f.write('\n')

    data = {'platform_system': platform_system, 'records': records}
    return create_success_dict(data=data)


def run_vnc(request):
    '''
        调用VNC代理进行远程控制
    '''
    template = loader.get_template('vnc_auto.html')

    token = request.GET.get('token', '')  # 用来判断不同的访问机器
    view_only = request.GET.get('view_only', 'false')  # false可以控制 or true只能查看

    # 代理服务器 IP及端口 , 这个一般都用校服务器局域网IP (127.0.0.1， 6080是默认端口)
    host = models.Setting.getvalue('host')
    port = constants.VNC_PROXY_PORT
    return HttpResponse(template.render({'token': token, 'host': host, 'port': port, 'view_only': view_only}))


def api_school_post(request):
    '''
        客户端获取有效的校园公告列表
    '''
    if models.Setting.getvalue('server_type') != 'school':
        return create_failure_dict(msg='仅校服务器可用')

    now = datetime.datetime.now()
    data = models.SchoolPost.objects.filter(Q(expire_date__isnull=True) | Q(expire_date__gte=now), active=True).values(
        'title', 'content', 'active', 'create_date', 'expire_date', 'update_date')

    return create_success_dict(data=model_list_to_dict(data))


def list_school_post(request):
    '''
        校园公告列表
    '''
    if models.Setting.getvalue('server_type') != 'school':
        return create_failure_dict(msg='仅校服务器可用')

    #now = datetime.datetime.now()
    #data = models.SchoolPost.objects.filter(Q(expire_date__isnull=True)|Q(expire_date__gte=now), active=True).values('title', 'content', 'active', 'create_date', 'expire_date')
    data = models.SchoolPost.objects.all().values('title', 'content', 'active', 'create_date', 'expire_date', 'update_date')

    return create_success_dict(data=model_list_to_dict(data))


def add_school_post(request):
    '''
        添加校园公告
    '''
    if models.Setting.getvalue('server_type') != 'school':
        return create_failure_dict(msg='仅校服务器可用')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        active = request.POST.get('active', False)
        active = bool(active in ('on', True, '1'))

        #now = datetime.datetime.now()

        # 暂时公告只需要一条数据
        olds = models.SchoolPost.objects.all()
        if olds.exists():
            old = olds[0]
            if active:
                if title:
                    #olds.update(title=title, content=content, active=active)
                    old.title = title
                    old.content = content
                    old.active = active
                    old.save()
                else:
                    return create_failure_dict(msg=u'公告标题是必须的')
            else:
                old.title = u''
                old.content = u''
                old.active = active
                old.save()
                # olds.update(active=active)
        else:
            #expire_date = now + datetime.timedelta(days=7)
            #models.SchoolPost.objects.create(title=title, content=content, active=active, expire_date=expire_date)
            if active:
                if title:
                    models.SchoolPost.objects.create(title=title, content=content, active=active)
                else:
                    return create_failure_dict(msg=u'公告标题是必须的')
            else:
                return create_failure_dict(msg=u'不能添加空的未启用公告')

        return create_success_dict(msg=u'添加校园公告成功')

    return create_failure_dict(msg=u'添加校园公告失败')


def edit_school_post(request):
    '''
        编辑校园公告
    '''
    if models.Setting.getvalue('server_type') != 'school':
        return create_failure_dict(msg='仅校服务器可用')

    if request.method == 'POST':
        id = request.POST.get('id', None)
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        active = request.POST.get('active', False)

        try:
            obj = models.SchoolPost.objects.get(pk=id)
        except Exception:
            return create_failure_dict(msg=u'没有该校园公告')

        obj.title = title
        obj.content = content
        obj.active = active

        obj.save()

        return create_success_dict(msg=u'编辑校园公告成功')

    return create_failure_dict(msg=u'编辑校园公告失败')


def del_school_post(request):
    '''
        删除校园公告
    '''
    if models.Setting.getvalue('server_type') != 'school':
        return create_failure_dict(msg='仅校服务器可用')

    if request.method == 'POST':
        id = request.POST.get('id', None)

        try:
            obj = models.SchoolPost.objects.get(pk=id)
        except Exception:
            return create_failure_dict(msg=u'没有该校园公告')

        obj.delete()

        return create_success_dict(msg=u'删除校园公告成功')

    return create_failure_dict(msg=u'删除校园公告失败')


def run_play_video(request):
    '''
        服务器端发送运维指令 (播放视频)
    '''
    if request.method == 'POST':
        post_data = request.POST

        # mac 集合
        macfilter = post_data.getlist('mac')

        # 保存视频文件
        file = request.FILES['file']
        filename = file['filename']
        with open('%s/%s' % (constants.UPLOAD_TMP_ROOT, filename), 'wb') as fd:
            fd.write(file['content'])

        # PUB play video msg to zmq
        send_msg(type='play-video', macfilter=macfilter, filename=filename)

        return create_success_dict(msg=u'视频播放指令发送成功', data=post_data)


"""
def recv(request):
    '''
        客户端连接发布池获取运维指令
    '''
    if request.method == 'POST':
        para_data = request.POST
    else:
        para_data = request.GET

    mac = para_data.get('mac', '')

    msg = recv_msg(mac=mac)
"""
