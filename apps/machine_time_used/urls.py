# coding=utf-8
from django.conf.urls import url
import views.client
import views.server
import views.api

urlpatterns = [
    # 资产管理>终端开机使用统计
    url(r'^time-used/by-town/?$', views.server.by_town),
    url(r'^time-used/by-school/?$', views.server.by_school),
    url(r'^time-used/by-grade/?$', views.server.by_grade),
    url(r'^time-used/by-class/?$', views.server.by_class),

    # 资产管理>终端开机使用统计>导出
    url(r'^time-used/by-town/export/?$', views.server.by_town_export),
    url(r'^time-used/by-school/export/?$', views.server.by_school_export),
    url(r'^time-used/by-grade/export/?$', views.server.by_grade_export),
    url(r'^time-used/by-class/export/?$', views.server.by_class_export),

    # 资产管理>终端开机使用日志
    url(r'^time-used/log/?$', views.server.terminal_time_used_log),
    url(r'^time-used/log/export/?$', views.server.terminal_time_used_log_export),


    # 客户端>终端开机使用时长
    url(r'^api/time-used/status/?$', views.client.get_status),
    url(r'^api/time-used/upload/?$', views.client.upload),


    # 校级从县级获取NODE ID
    url(r'^api/get_node_id/?$', views.api.get_node_id),
]
