# coding=utf-8
from BanBanTong.db import models
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.views.system import install


@decorator.authorized_user_with_redirect
def get(request, *args, **kwargs):
    if request.method == 'GET':
        try:
            host = models.Setting.objects.get(name='host')
            host = host.value
        except:
            host = ''
        try:
            port = models.Setting.objects.get(name='port')
            # port = port.value
            # FIXME
            # 初始化安装的时候,前端请求默认端口(websocket等)
            # 这里直接后台固定为 11111
            port = '11111'
        except:
            port = ''
        try:
            o = models.Setting.objects.get(name='show_download_btn')
            show_download_btn = str(o.value).lower()
        except:
            show_download_btn = 'true'
        try:
            o = models.Setting.objects.get(name='html_title')
            html_title = o.value
        except:
            html_title = u'噢易班班通管理分析系统'

        return create_success_dict(data={
            'host': host,
            'port': port,
            'show_download_btn': show_download_btn,
            'html_title': html_title
        })


@decorator.authorized_user_with_redirect
def set(request, *args, **kwargs):
    if request.method == 'POST':
        host = request.POST.get('host')
        port = request.POST.get('port')
        show_download_btn = request.POST.get('show_download_btn', False)
        html_title = request.POST.get('html_title')
        if host:
            i, c = models.Setting.objects.get_or_create(name='host')
            if i.value != host:
                i.value = host
                i.save()
        if port:
            i, c = models.Setting.objects.get_or_create(name='port')
            if i.value != port:
                i.value = port
                i.save()
        obj, c = models.Setting.objects.get_or_create(name='show_download_btn')
        obj.value = show_download_btn == 'true' and True or False
        obj.save()

        if html_title:
            obj, c = models.Setting.objects.get_or_create(
                name='html_title'
            )
            obj.value = html_title
            obj.save()

        install._package_client_file()
        return create_success_dict(msg='修改成功')
