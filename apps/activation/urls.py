# coding=utf-8
from django.conf.urls import url

import views
import serverside

urlpatterns = [

    # 是否激活授权
    url(r'^api/has_activate/?$', views.api_has_activate),
    # 已使用授权点数
    url(r'^api/get_use_activate/?$', views.api_get_use_activate),
    # 未使用授权点数
    url(r'^api/get_none_activate/?$', views.api_get_none_activate),
    # 已使用授权点数 (返回详细)
    url(r'^api/get_use_activate_with_detail/?$', views.api_get_use_activate_with_detail),

    # 激活授权
    url(r'^activate/?$', serverside.activate),
]
