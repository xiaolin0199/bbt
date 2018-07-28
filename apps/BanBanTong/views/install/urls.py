# coding=utf-8
from django.conf.urls import url
import BanBanTong.views.system.install
import BanBanTong.views.system.remote
import sync_server


urlpatterns = [
    # 系统安装>初始化
    url(r'^$', BanBanTong.views.system.install.index),
    url(r'^step/?$', BanBanTong.views.system.install.step),
    url(r'^serverinfo/?$', BanBanTong.views.system.install.serverinfo),
    url(r'^grade_class/?$', BanBanTong.views.system.install.grade_class),
    url(r'^node/?$', BanBanTong.views.system.install.node),

    # 系统安装>校级服务器连接测试
    url(r'^sync-server/verify/?$', sync_server.verify),
    # 系统安装>校级服务器保存上级服务器设置
    url(r'^sync-server/set/?$', BanBanTong.views.install.sync_server.set),
    # 系统安装>校级服务器获取上级服务器省市区信息
    url(r'^sync-server/get-group/?$', BanBanTong.views.install.sync_server.get_group),


    # 下级服务器数据恢复
    url(r'^remote/setting/?$', BanBanTong.views.system.remote.restore),
    url(r'^remote/setting/test/?$', BanBanTong.views.system.remote.restore_test),
    url(r'^remote/status/?$', BanBanTong.views.system.remote.status),
]
