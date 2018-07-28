# coding=utf-8
from django.conf.urls import url

import logged_in
import not_logged_in
import desktop_preview


# 教师授课
urlpatterns = [
    # 教师授课>班班通登录日志、未登录日志、桌面使用日志
    url(r'^logged-in/?$', logged_in.get),
    url(r'^logged-in/computer-class/?$', logged_in.computerclass_loged_info),
    url(r'^not-logged-in/?$', not_logged_in.grid_data),
    url(r'^desktop-preview/groups/?$', desktop_preview.get_node_info),
    url(r'^desktop-preview/by-date/?$', desktop_preview.get_pics_info_by_date),
    url(r'^desktop-preview/list-everyday/?$', desktop_preview.get_pics_count_by_date),
    # 教师授课>电脑教室登录日志、桌面使用日志
    url(r'^logged-in/computer-class/?$', logged_in.computerclass_loged_info),
]
