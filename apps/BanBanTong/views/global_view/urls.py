# coding=utf-8
from django.conf.urls import url
import login_status
import desktop_preview
import global_overview


# 基础信息
urlpatterns = [
    # global/
    # 实时概况>登录状态
    url(r'^login-status/?$', login_status.list_class),
    # 实时概况>桌面预览
    url(r'^desktop-preview/?$', desktop_preview.realtime),
    url(r'^desktop-preview/computer-class/?$', desktop_preview.computerclass_realtime),
    # global-statistic/
    # 实时概况>全局数据
    # url(r'^global_statistic/?$', BanBanTong.views.global_view.global_overview.global_statistic),
    url(r'^$', global_overview.global_statistic),
    url(r'^computer-class/?$', global_overview.global_statistic_computerclass),
]
