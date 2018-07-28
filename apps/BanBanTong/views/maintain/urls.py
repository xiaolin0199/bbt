# coding=utf-8
from django.conf.urls import url
import BanBanTong.views.system.maintain
import resync
import desktop_preview


# 基础信息
urlpatterns = [
    url(r'^$', BanBanTong.views.system.maintain.index),
    url(r'^auth/?$', BanBanTong.views.system.maintain.auth),
    url(r'^info/?$', BanBanTong.views.system.maintain.info),
    url(r'^log/?$', BanBanTong.views.system.maintain.log),
    url(r'^log/download/?$', BanBanTong.views.system.maintain.log_download),
    url(r'^desktop-preview/network-diagnose/?$', desktop_preview.network_diagnose),
    url(r'^resync/set/?$', resync.set),
]
