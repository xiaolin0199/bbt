# coding=utf-8
from django.conf import settings
from django.conf.urls import url
from django.views.generic import RedirectView
from django.views import static


import BanBanTong.views.list.api

import BanBanTong.views.resource_collect.index
import BanBanTong.commands.management.commands.calculate_teaching_analysis
import BanBanTong.commands.management.commands.create_statistic_items
import BanBanTong.commands.management.commands.generate_node_setting_cachefiles
import BanBanTong.commands.management.commands.recreate_fks_for_loginlogs
import BanBanTong.commands.management.commands.update_current_statistic_items
import edu_point.management.commands.inherit_items_from_last_term
import BanBanTong.views.system.lesson_period

import BanBanTong.views.download
import BanBanTong.views.static
import BanBanTong.views.system.class_mac
import BanBanTong.views.system.install
import BanBanTong.views.index
import BanBanTong.tasks

urlpatterns = [
    url(r'^favicon\.ico$', RedirectView.as_view(url='/public/images/favicon.ico')),

    url(r'^$', BanBanTong.views.index.index),
    url(r'^login/?$', BanBanTong.views.index.login, name='login'),
    url(r'^logout/?$', BanBanTong.views.index.logout, name='logout'),
    url(r'^version/?$', BanBanTong.views.index.version),
    url(r'^server_info/?$', BanBanTong.views.index.server_info),
    url(r'^classes/?$', BanBanTong.views.index.classes),
    url(r'^classes1/?$', BanBanTong.views.index.classes1),
    url(r'^group/?$', BanBanTong.views.index.group),
    url(r'^details/?$', BanBanTong.views.index.details),
    url(r'^privileges/?$', BanBanTong.views.index.privileges),


    # 供测试用的一些
    url(r'^test4lessonperiod/?$', BanBanTong.views.system.lesson_period.create_lesson_period4test),
    url(r'^test/run/calculate_teaching_analysis/?$', BanBanTong.commands.management.commands.calculate_teaching_analysis.run_by_http),
    url(r'^test/run/create_statistic_items/?$', BanBanTong.commands.management.commands.create_statistic_items.run_by_http),
    url(r'^test/run/calculate_statistic/?$', BanBanTong.commands.management.commands.create_statistic_items.run_by_http),
    url(r'^test/run/generate_node_setting_cachefiles/?$', BanBanTong.commands.management.commands.generate_node_setting_cachefiles.run_by_http),
    url(r'^test/run/recreate_fks_for_loginlogs/?$', BanBanTong.commands.management.commands.recreate_fks_for_loginlogs.run_by_http),
    url(r'^test/run/update_current_statistic_items/?$', BanBanTong.commands.management.commands.update_current_statistic_items.run_by_http),
    url(r'^test/run/inherit_items_from_last_term/?$', edu_point.management.commands.inherit_items_from_last_term.run_by_http),


    url(r'^resource-collect/?$', BanBanTong.views.resource_collect.index.index),
    url(r'^public/(?P<path>.*)/?$', static.serve, {'document_root': settings.PUBLIC_ROOT}),
    url(r'^logs/(?P<path>.*)/?$', static.serve, {'document_root': BanBanTong.constants.LOG_PATH}),
    # url(r'^templates/(?P<path>.*)/?$',static.serve,     {'document_root': settings.TEMPLATE_DIRS[0]}),
    # 客户端升级文件
    url(r'^software/updates(?P<static_file>/.+\..+)\?*.*/?$', BanBanTong.views.static.serve_software_update),
    url(r'^software/edufiles(?P<static_file>/.+\..+)\?*.*/?$', BanBanTong.views.static.serve_software_edufiles),

    # 前端通用>
    url(r'^classes/available-choices/?$', BanBanTong.views.system.class_mac.get_choices),
    url(r'^group_get_children/?$', BanBanTong.views.system.install.group_get_children),

    # 前端通用>前端查询条件联动API
    url(r'^list/get-grade-class/?$', BanBanTong.views.list.api.get_grade_class),
    url(r'^list/get-lesson-period/?$', BanBanTong.views.list.api.get_lesson_period),
    url(r'^list/get-lesson-name/?$', BanBanTong.views.list.api.get_lesson_name),

    url(r'^xls_download/(?P<cached_id>.*)/(?P<name>.*)/?$', BanBanTong.views.download.xls_download, name='xls_download'),
    url(r'^download/(?P<name>.*)/?$', BanBanTong.views.download.download),
    url(r'^run-task/(?P<name>.*)/?$', BanBanTong.tasks.run_task),
]


# #!/usr/bin/env python
# # coding=utf-8
# from django.conf import settings
# from django.conf.urls import include, url
# from django.views.generic import RedirectView
# # from BanBanTong.utils import zmq_service
# from django.views import static
# import BanBanTong.constants
# import BanBanTong.views.activity
# import BanBanTong.views.api
# import BanBanTong.views.asset
# import BanBanTong.views.global_view
# import BanBanTong.views.install.sync_server
# import BanBanTong.views.list
# import BanBanTong.views.maintain
# import BanBanTong.views.resource_collect
# import BanBanTong.views.statistic


# import BanBanTong.views.list.api
# import BanBanTong.views.global_view.global_overview
# import BanBanTong.views.global_view.login_status
# import BanBanTong.views.global_view.desktop_preview
# import BanBanTong.views.activity.logged_in
# import BanBanTong.views.activity.not_logged_in
# import BanBanTong.views.activity.desktop_preview
# import BanBanTong.views.statistic.teaching_analysis
# import BanBanTong.views.statistic.teaching_time
# import BanBanTong.views.statistic.time_used
# import BanBanTong.views.statistic.teacher_active
# import BanBanTong.views.statistic.teacher_absent
# import BanBanTong.views.statistic.resource
# import BanBanTong.views.statistic.resource_from
# import BanBanTong.views.statistic.resource_type
# import BanBanTong.views.asset.asset
# import BanBanTong.views.asset.asset_log
# import BanBanTong.views.asset.asset_repair


# import BanBanTong.views.system.about
# import BanBanTong.views.system.baseinfo
# import BanBanTong.views.system.class_mac
# import BanBanTong.views.system.computer_class_mac
# import BanBanTong.views.system.desktop_preview
# import BanBanTong.views.system.__init__
# import BanBanTong.views.system.install
# import BanBanTong.views.system.lesson_name
# import BanBanTong.views.system.lesson_period
# import BanBanTong.views.system.lesson_schedule
# import BanBanTong.views.system.lesson_teacher
# import BanBanTong.views.system.maintain
# import BanBanTong.views.system.maintenance
# import BanBanTong.views.system.new_lesson_name
# import BanBanTong.views.system.newterm
# import BanBanTong.views.system.node
# import BanBanTong.views.system.remote
# import BanBanTong.views.system.resource
# import BanBanTong.views.system.restore
# import BanBanTong.views.system.role
# import BanBanTong.views.system.school_server_setting
# import BanBanTong.views.system.syllabus
# import BanBanTong.views.system.sync_server
# import BanBanTong.views.system.teacher
# import BanBanTong.views.system.term
# import BanBanTong.views.system.user
# import BanBanTong.views.system.util

# import BanBanTong.views.maintain.desktop_preview
# import BanBanTong.views.maintain.resync

# import BanBanTong.views.api.interfaces.index
# import BanBanTong.views.api.interfaces.lesson
# import BanBanTong.views.api.interfaces.computerclass_client
# import BanBanTong.views.api.interfaces.client
# import BanBanTong.views.api.interfaces.class_mac
# import BanBanTong.views.api.interfaces.teacher
# import BanBanTong.views.api.interfaces.desktop_preview
# import BanBanTong.views.api.interfaces.courseware
# import BanBanTong.views.api.interfaces.class_mac
# import BanBanTong.views.api.interfaces.client
# import BanBanTong.views.api.interfaces.client_sync
# import BanBanTong.views.api.interfaces.client_utils
# import BanBanTong.views.api.interfaces.computerclass_client
# import BanBanTong.views.api.interfaces.country_to_school
# import BanBanTong.views.api.interfaces.courseware
# import BanBanTong.views.api.interfaces.desktop_preview
# import BanBanTong.views.api.interfaces.index
# import BanBanTong.views.api.interfaces.lesson_new
# import BanBanTong.views.api.interfaces.lesson
# import BanBanTong.views.api.interfaces.restore
# import BanBanTong.views.api.interfaces.sync_server
# import BanBanTong.views.api.interfaces.teacher
# import BanBanTong.views.api.interfaces.term_lesson_resource

# import BanBanTong.views.api.third_party.morningcloud
# import BanBanTong.views.api.third_party.songda
# import BanBanTong.views.resource_collect.index
# import BanBanTong.commands.management.commands.calculate_teaching_analysis
# import BanBanTong.commands.management.commands.create_statistic_items
# import BanBanTong.commands.management.commands.generate_node_setting_cachefiles
# import BanBanTong.commands.management.commands.recreate_fks_for_loginlogs
# import BanBanTong.commands.management.commands.update_current_statistic_items
# import edu_point.management.commands.inherit_items_from_last_term


# import BanBanTong.views.asset.asset_type
# import BanBanTong.views.index
# import BanBanTong.views.download
# import BanBanTong.views.static
# import BanBanTong.views.api.interfaces.sync_server
# import edu_point

# # 启动PUB端发布服务
# # zmq_service.start_publisher()

# urlpatterns = [
#     url(r'^/?$', BanBanTong.views.index.index),
#     url(r'^favicon\.ico/?$', RedirectView.as_view(url='/public/images/favicon.ico')),
#     url(r'^login/?$', BanBanTong.views.index.login, name='login'),
#     url(r'^logout/?$', BanBanTong.views.index.logout, name='logout'),

#     # 机器时长
#     url(r'^terminal/', include('machine_time_used.urls')),
#     # 教学点
#     url(r'^edu-unit/', include('edu_point.urls')),
#     # 授权信息
#     url(r'^activation/', include('activation.urls')),
# ]


# # 系统安装
# urlpatterns += [
#     # 系统安装>初始化
#     url(r'^install/?$', BanBanTong.views.system.install.index),
#     url(r'^install/step/?$', BanBanTong.views.system.install.step),
#     url(r'^install/serverinfo/?$', BanBanTong.views.system.install.serverinfo),
#     url(r'^install/grade_class/?$', BanBanTong.views.system.install.grade_class),
#     url(r'^install/node/?$', BanBanTong.views.system.install.node),

#     # 系统安装>校级服务器连接测试
#     url(r'^install/sync-server/verify/?$',
#         BanBanTong.views.install.sync_server.verify),
#     url(r'^api/sync-server/verify/?$',
#         BanBanTong.views.api.interfaces.sync_server.verify),

#     # 系统安装>校级服务器保存上级服务器设置
#     url(r'^install/sync-server/set/?$',
#         BanBanTong.views.install.sync_server.set),
#     url(r'^api/sync-server/check-data/?$',
#         BanBanTong.views.api.interfaces.sync_server.check_data),

#     # 系统安装>校级服务器获取上级服务器省市区信息
#     url(r'^install/sync-server/get-group/?$',
#         BanBanTong.views.install.sync_server.get_group),
#     url(r'^api/sync-server/get-group/?$',
#         BanBanTong.views.api.interfaces.sync_server.get_group),

#     # 校级从县级获取NODE ID
#     url(r'^api/sync-server/get_node_id/?$', BanBanTong.views.system.node.get_node_id),
# ]

# # 前端通用
# urlpatterns += [
#     # 前端通用>
#     url(r'^server_info/?$', BanBanTong.views.index.server_info),
#     url(r'^classes/?$', BanBanTong.views.index.classes),
#     url(r'^classes1/?$', BanBanTong.views.index.classes1),
#     url(r'^classes/available-choices/?$', BanBanTong.views.system.class_mac.get_choices),
#     url(r'^group/?$', BanBanTong.views.index.group),
#     url(r'^details/?$', BanBanTong.views.index.details),
#     url(r'^privileges/?$', BanBanTong.views.index.privileges),
#     url(r'^group_get_children/?$', BanBanTong.views.system.install.group_get_children),
#     url(r'^system/lesson-period/list-sequence/?$',
#         BanBanTong.views.system.lesson_period.list_sequence),
#     url(r'^system/term/current-or-next/?$', BanBanTong.views.system.term.get_current_or_next_term),
#     url(r'^system/term/nearest-one/?$', BanBanTong.views.system.term.get_nearest_term),
#     url(r'^system/term/current/?$', BanBanTong.views.system.term.get_current_term),
#     url(r'^system/lesson_teacher/remain_time/?$',
#         BanBanTong.views.system.lesson_teacher.get_remain_time),

#     # 前端通用>前端查询条件联动API
#     url(r'^list/get-grade-class/?$', BanBanTong.views.list.api.get_grade_class),
#     url(r'^list/get-lesson-period/?$', BanBanTong.views.list.api.get_lesson_period),
#     url(r'^list/get-lesson-name/?$', BanBanTong.views.list.api.get_lesson_name),

#     # 前端其他API
#     # 危险操作需要用户输入admin密码再确认
#     url(r'^system/sudo/?$', BanBanTong.views.system.util.sudo),

#     url(r'^xls_download/(?P<cached_id>.*)/(?P<name>.*)/?$',
#         BanBanTong.views.download.xls_download, name='xls_download'),
#     url(r'^download/(?P<name>.*)/?$', BanBanTong.views.download.download),
# ]

# # 实时概况
# urlpatterns += [
#     # 实时概况>全局数据
#     url(r'^global_statistic/?$',  # old
#         BanBanTong.views.global_view.global_overview.global_statistic),
#     url(r'^global-statistic/?$',  # new
#         BanBanTong.views.global_view.global_overview.global_statistic),
#     url(r'^global-statistic/computer-class/?$',
#         BanBanTong.views.global_view.global_overview.global_statistic_computerclass),

#     # 实时概况>登录状态
#     url(r'^global/login-status/?$',
#         BanBanTong.views.global_view.login_status.list_class),

#     # 实时概况>桌面预览
#     url(r'^global/desktop-preview/?$',
#         BanBanTong.views.global_view.desktop_preview.realtime),
#     url(r'^global/desktop-preview/computer-class/?$',
#         BanBanTong.views.global_view.desktop_preview.computerclass_realtime),
# ]

# # 运维管理
# urlpatterns += [
#     url(r'^system/maintenance/list-system/?$', BanBanTong.views.system.maintenance.list_system),
#     url(r'^system/maintenance/scheduler-shutdown/get/?$',
#         BanBanTong.views.system.maintenance.scheduler_shutdown_get),
#     url(r'^system/maintenance/scheduler-shutdown/?$',
#         BanBanTong.views.system.maintenance.scheduler_shutdown),
#     url(r'^system/maintenance/run-shutdown/?$', BanBanTong.views.system.maintenance.run_shutdown),
#     url(r'^system/maintenance/run-reboot/?$', BanBanTong.views.system.maintenance.run_reboot),

#     url(r'^system/maintenance/list-vnc/?$', BanBanTong.views.system.maintenance.list_vnc),
#     url(r'^system/maintenance/run-vnc/?$', BanBanTong.views.system.maintenance.run_vnc),

#     url(r'^system/maintenance/school-post/api/?$',
#         BanBanTong.views.system.maintenance.api_school_post),
#     url(r'^system/maintenance/school-post/list/?$',
#         BanBanTong.views.system.maintenance.list_school_post),
#     url(r'^system/maintenance/school-post/add/?$',
#         BanBanTong.views.system.maintenance.add_school_post),
#     url(r'^system/maintenance/school-post/edit/?$',
#         BanBanTong.views.system.maintenance.edit_school_post),
#     url(r'^system/maintenance/school-post/del/?$',
#         BanBanTong.views.system.maintenance.del_school_post),

#     # url(r'^system/maintenance/recv-msg/?$', BanBanTong.views.system.maintenance.recv),
#     url(r'^system/maintenance/run-play-video/?$', BanBanTong.views.system.maintenance.run_play_video),
# ]

# # 教师授课
# urlpatterns += [
#     # 教师授课>班班通登录日志、未登录日志、桌面使用日志
#     url(r'^activity/logged-in/?$',
#         BanBanTong.views.activity.logged_in.get),
#     url(r'^activity/logged-in/computer-class/?$',
#         BanBanTong.views.activity.logged_in.computerclass_loged_info),
#     url(r'^activity/not-logged-in/?$',
#         BanBanTong.views.activity.not_logged_in.grid_data),
#     url(r'^activity/desktop-preview/groups/?$',
#         BanBanTong.views.activity.desktop_preview.get_node_info),
#     url(r'^activity/desktop-preview/by-date/?$',
#         BanBanTong.views.activity.desktop_preview.get_pics_info_by_date),
#     url(r'^activity/desktop-preview/list-everyday/?$',
#         BanBanTong.views.activity.desktop_preview.get_pics_count_by_date),

#     # 教师授课>电脑教室登录日志、桌面使用日志
#     url(r'^activity/logged-in/computer-class/?$',
#         BanBanTong.views.activity.logged_in.computerclass_loged_info),

#     # 教师授课>班班通授课综合分析
#     # 1 班班通授课综合分析
#     url(r'statistic/teaching-analysis/lesson-count/?$',
#         BanBanTong.views.statistic.teaching_analysis.url_has_been_abandoned),
#     url(r'statistic/teaching-analysis/total-time/?$',
#         BanBanTong.views.statistic.teaching_analysis.url_has_been_abandoned),
#     url(r'statistic/teaching-analysis/lesson-name/?$',
#         BanBanTong.views.statistic.teaching_analysis.url_has_been_abandoned),
#     url(r'statistic/teaching-analysis/count/by-lesson/?$',
#         BanBanTong.views.statistic.teaching_analysis.lesson_count),
#     url(r'statistic/teaching-analysis/count/by-grade/?$',
#         BanBanTong.views.statistic.teaching_analysis.grade_count),
#     url(r'statistic/teaching-analysis/count/by-week/?$',
#         BanBanTong.views.statistic.teaching_analysis.week_count),
#     url(r'statistic/teaching-analysis/count/by-week/average/?$',
#         BanBanTong.views.statistic.teaching_analysis.week_count_average),
#     url(r'statistic/teaching-analysis/time/by-week/?$',
#         BanBanTong.views.statistic.teaching_analysis.week_time),
#     url(r'statistic/teaching-analysis/time/by-week/average/?$',
#         BanBanTong.views.statistic.teaching_analysis.week_time_average),
#     url(r'statistic/teaching-analysis/count/total/?$',
#         BanBanTong.views.statistic.teaching_analysis.week_count_total),
#     url(r'statistic/teaching-analysis/count/total/average/?$',
#         BanBanTong.views.statistic.teaching_analysis.week_count_total_average),
#     url(r'statistic/teaching-analysis/time/total/?$',
#         BanBanTong.views.statistic.teaching_analysis.week_time_total),
#     url(r'statistic/teaching-analysis/time/total/average/?$',
#         BanBanTong.views.statistic.teaching_analysis.week_time_total_average),

#     # 教师授课>班班通授课次数比例统计
#     url(r'^statistic/teaching-time/by-country/?$',
#         BanBanTong.views.statistic.teaching_time.by_country),
#     url(r'^statistic/teaching-time/by-town/?$', BanBanTong.views.statistic.teaching_time.by_town),
#     url(r'^statistic/teaching-time/by-school/?$', BanBanTong.views.statistic.teaching_time.by_school),
#     url(r'^statistic/teaching-time/by-grade/?$', BanBanTong.views.statistic.teaching_time.by_grade),
#     url(r'^statistic/teaching-time/by-class/?$', BanBanTong.views.statistic.teaching_time.by_class),
#     url(r'^statistic/teaching-time/by-lessonteacher/?$',
#         BanBanTong.views.statistic.teaching_time.by_lessonteacher),
#     url(r'^statistic/teaching-time/by-teacher/?$',
#         BanBanTong.views.statistic.teaching_time.by_teacher),

#     url(r'^statistic/teaching-time/by-country/export/?$',
#         BanBanTong.views.statistic.teaching_time.by_country_export),
#     url(r'^statistic/teaching-time/by-town/export/?$',
#         BanBanTong.views.statistic.teaching_time.by_town_export),
#     url(r'^statistic/teaching-time/by-school/export/?$',
#         BanBanTong.views.statistic.teaching_time.by_school_export),
#     url(r'^statistic/teaching-time/by-grade/export/?$',
#         BanBanTong.views.statistic.teaching_time.by_grade_export),
#     url(r'^statistic/teaching-time/by-class/export/?$',
#         BanBanTong.views.statistic.teaching_time.by_class_export),
#     url(r'^statistic/teaching-time/by-lessonteacher/export/?$',
#         BanBanTong.views.statistic.teaching_time.by_lessonteacher_export),
#     url(r'^statistic/teaching-time/by-teacher/export/?$',
#         BanBanTong.views.statistic.teaching_time.by_teacher_export),


#     # 教师授课>班班通授课时长统计
#     url(r'^statistic/time-used/by-country/?$',
#         BanBanTong.views.statistic.time_used.by_country),
#     url(r'^statistic/time-used/by-country/export/?$',
#         BanBanTong.views.statistic.time_used.by_country_export),
#     url(r'^statistic/time-used/by-town/?$',
#         BanBanTong.views.statistic.time_used.by_town),
#     url(r'^statistic/time-used/by-town/export/?$',
#         BanBanTong.views.statistic.time_used.by_town_export),
#     url(r'^statistic/time-used/by-school/?$',
#         BanBanTong.views.statistic.time_used.by_school),
#     url(r'^statistic/time-used/by-school/export/?$',
#         BanBanTong.views.statistic.time_used.by_school_export),
#     url(r'^statistic/time-used/by-grade/?$',
#         BanBanTong.views.statistic.time_used.by_grade),
#     url(r'^statistic/time-used/by-grade/export/?$',
#         BanBanTong.views.statistic.time_used.by_grade_export),
#     url(r'^statistic/time-used/by-class/?$',
#         BanBanTong.views.statistic.time_used.by_class),
#     url(r'^statistic/time-used/by-class/export/?$',
#         BanBanTong.views.statistic.time_used.by_class_export),
#     url(r'^statistic/time-used/by-teacher/?$',
#         BanBanTong.views.statistic.time_used.by_teacher),
#     url(r'^statistic/time-used/by-teacher/export/?$',
#         BanBanTong.views.statistic.time_used.by_teacher_export),
#     url(r'^statistic/time-used/by-lessonteacher/?$',
#         BanBanTong.views.statistic.time_used.by_lessonteacher),
#     url(r'^statistic/time-used/by-lessonteacher/export/?$',
#         BanBanTong.views.statistic.time_used.by_lessonteacher_export),

#     # 教师授课>教师授课人数比例统计
#     url(r'^statistic/teacher-active/by-country/?$',
#         BanBanTong.views.statistic.teacher_active.by_country),
#     url(r'^statistic/teacher-active/by-country/export/?$',
#         BanBanTong.views.statistic.teacher_active.by_country_export),
#     url(r'^statistic/teacher-active/by-grade/?$',
#         BanBanTong.views.statistic.teacher_active.by_grade),
#     url(r'^statistic/teacher-active/by-grade/export/?$',
#         BanBanTong.views.statistic.teacher_active.by_grade_export),
#     url(r'^statistic/teacher-active/by-lesson/?$',
#         BanBanTong.views.statistic.teacher_active.by_lesson),
#     url(r'^statistic/teacher-active/by-lesson/export/?$',
#         BanBanTong.views.statistic.teacher_active.by_lesson_export),
#     url(r'^statistic/teacher-active/by-lessongrade/?$',
#         BanBanTong.views.statistic.teacher_active.by_lessongrade),
#     url(r'^statistic/teacher-active/by-lessongrade/export/?$',
#         BanBanTong.views.statistic.teacher_active.by_lessongrade_export),
#     url(r'^statistic/teacher-active/by-school/?$',
#         BanBanTong.views.statistic.teacher_active.by_school),
#     url(r'^statistic/teacher-active/by-school/export/?$',
#         BanBanTong.views.statistic.teacher_active.by_school_export),
#     url(r'^statistic/teacher-active/by-town/?$',
#         BanBanTong.views.statistic.teacher_active.by_town),
#     url(r'^statistic/teacher-active/by-town/export/?$',
#         BanBanTong.views.statistic.teacher_active.by_town_export),

#     # 统计分析->授课资源使用统计
#     # url(r'^statistic/resource/resource-from/?$',
#     #    BanBanTong.views.statistic.resource.resource_from),
#     # url(r'^statistic/resource/resource-from/export/?$',
#     #    BanBanTong.views.statistic.resource.resource_from_export),
#     # url(r'^statistic/resource/resource-type/?$',
#     #    BanBanTong.views.statistic.resource.resource_type),
#     # url(r'^statistic/resource/resource-type/export/?$',
#     #    BanBanTong.views.statistic.resource.resource_type_export),
#     # url(r'^statistic/resource/teacher/?$',
#     #    BanBanTong.views.statistic.resource.teacher),
#     # url(r'^statistic/resource/teacher/export/?$',
#     #    BanBanTong.views.statistic.resource.teacher_export),
#     # url(r'^statistic/resource/lesson/?$',
#     #    BanBanTong.views.statistic.resource.lesson),
#     # url(r'^statistic/resource/lesson/export/?$',
#     #    BanBanTong.views.statistic.resource.lesson_export),

#     # 教师授课>教师未登录班班通统计
#     url(r'statistic.teacher-absent/by-country/?$',
#         BanBanTong.views.statistic.teacher_absent.by_country),
#     url(r'statistic.teacher-absent/by-country/export/?$',
#         BanBanTong.views.statistic.teacher_absent.by_country_export),
#     url(r'statistic.teacher-absent/by-grade/?$',
#         BanBanTong.views.statistic.teacher_absent.by_grade),
#     url(r'statistic.teacher-absent/by-grade/export/?$',
#         BanBanTong.views.statistic.teacher_absent.by_grade_export),
#     url(r'statistic.teacher-absent/by-lesson/?$',
#         BanBanTong.views.statistic.teacher_absent.by_lesson),
#     url(r'statistic.teacher-absent/by-lesson/export/?$',
#         BanBanTong.views.statistic.teacher_absent.by_lesson_export),
#     url(r'statistic.teacher-absent/by-lessongrade/?$',
#         BanBanTong.views.statistic.teacher_absent.by_lessongrade),
#     url(r'statistic.teacher-absent/by-lessongrade/export/?$',
#         BanBanTong.views.statistic.teacher_absent.by_lessongrade_export),
#     url(r'statistic.teacher-absent/by-school/?$',
#         BanBanTong.views.statistic.teacher_absent.by_school),
#     url(r'statistic.teacher-absent/by-school/export/?$',
#         BanBanTong.views.statistic.teacher_absent.by_school_export),
#     url(r'statistic.teacher-absent/by-town/?$',
#         BanBanTong.views.statistic.teacher_absent.by_town),
#     url(r'statistic.teacher-absent/by-town/export/?$',
#         BanBanTong.views.statistic.teacher_absent.by_town_export),
# ]

# # 资源使用
# urlpatterns += [
#     # 资源使用>资源使用综合分析
#     url(r'^statistic/resource-global/?$',
#         BanBanTong.views.statistic.resource.resource_global),

#     # 资源使用>资源来源使用分析
#     url(r'^statistic/resource-from/town/?$',
#         BanBanTong.views.statistic.resource_from.by_town),
#     url(r'^statistic/resource-from/town/export/?$',
#         BanBanTong.views.statistic.resource_from.by_town_export),
#     url(r'^statistic/resource-from/school/?$',
#         BanBanTong.views.statistic.resource_from.by_school),
#     url(r'^statistic/resource-from/school/export/?$',
#         BanBanTong.views.statistic.resource_from.by_school_export),
#     url(r'^statistic/resource-from/class/?$',
#         BanBanTong.views.statistic.resource_from.by_class),
#     url(r'^statistic/resource-from/class/export/?$',
#         BanBanTong.views.statistic.resource_from.by_class_export),
#     url(r'^statistic/resource-from/lesson/?$',
#         BanBanTong.views.statistic.resource_from.by_lesson),
#     url(r'^statistic/resource-from/lesson/export/?$',
#         BanBanTong.views.statistic.resource_from.by_lesson_export),
#     url(r'^statistic/resource-from/teacher/?$',
#         BanBanTong.views.statistic.resource_from.by_teacher),
#     url(r'^statistic/resource-from/teacher/export/?$',
#         BanBanTong.views.statistic.resource_from.by_teacher_export),

#     # 资源使用>资源类型使用分析
#     url(r'^statistic/resource-type/town/?$',
#         BanBanTong.views.statistic.resource_type.by_town),
#     url(r'^statistic/resource-type/town/export/?$',
#         BanBanTong.views.statistic.resource_type.by_town_export),
#     url(r'^statistic/resource-type/school/?$',
#         BanBanTong.views.statistic.resource_type.by_school),
#     url(r'^statistic/resource-type/school/export/?$',
#         BanBanTong.views.statistic.resource_type.by_school_export),
#     url(r'^statistic/resource-type/class/?$',
#         BanBanTong.views.statistic.resource_type.by_class),
#     url(r'^statistic/resource-type/class/export/?$',
#         BanBanTong.views.statistic.resource_type.by_class_export),
#     url(r'^statistic/resource-type/lesson/?$',
#         BanBanTong.views.statistic.resource_type.by_lesson),
#     url(r'^statistic/resource-type/lesson/export/?$',
#         BanBanTong.views.statistic.resource_type.by_lesson_export),
#     url(r'^statistic/resource-type/teacher/?$',
#         BanBanTong.views.statistic.resource_type.by_teacher),
#     url(r'^statistic/resource-type/teacher/export/?$',
#         BanBanTong.views.statistic.resource_type.by_teacher_export),
# ]

# # 资产管理
# urlpatterns += [
#     # 资产管理->资产统计与申报
#     url(r'^asset/asset-type/?$', BanBanTong.views.asset.asset_type.list_current),
#     url(r'^asset/asset-type/aggregate/?$',
#         BanBanTong.views.asset.asset_type.aggregate),
#     url(r'^asset/asset-type/export/?$', BanBanTong.views.asset.asset_type.export),
#     url(r'^asset/add/?$', BanBanTong.views.asset.asset.add),
#     url(r'^asset/delete/?$', BanBanTong.views.asset.asset.delete),
#     url(r'^asset/export/?$', BanBanTong.views.asset.asset.export),
#     url(r'^asset/?$', BanBanTong.views.asset.asset.list_current),
#     url(r'^asset/aggregate/?$', BanBanTong.views.asset.asset.aggregate),

#     # 资产管理>申报记录查询
#     url(r'^asset/asset-log/export/?$', BanBanTong.views.asset.asset_log.export),
#     url(r'^asset/asset-log/?$', BanBanTong.views.asset.asset_log.list_current),

#     # 资产管理>资产维修管理
#     url(r'^asset/asset-repair/add/?$',
#         BanBanTong.views.asset.asset_repair.add),
#     url(r'^asset/asset-repair/export/?$',
#         BanBanTong.views.asset.asset_repair.export),
#     url(r'^asset/asset-repair/?$',
#         BanBanTong.views.asset.asset_repair.list_current),
#     url(r'^asset/get-devicemodel-by-assettype/?$',
#         BanBanTong.views.asset.asset.get_devicemodel_by_assettype),
#     url(r'^asset/asset-type/get-assettype-for-repair/?$',
#         BanBanTong.views.asset.asset_type.get_assettype_for_repair),
# ]

# # 系统设置
# urlpatterns += [
#     # 系统设置>用户管理
#     url(r'^system/user/list/?$', BanBanTong.views.system.user.list_current),
#     url(r'^system/user/add/?$', BanBanTong.views.system.user.add),
#     url(r'^system/user/detail/?$', BanBanTong.views.system.user.detail),
#     url(r'^system/user/edit/?$', BanBanTong.views.system.user.edit),
#     url(r'^system/user/delete/?$', BanBanTong.views.system.user.delete),

#     # 系统设置>角色管理
#     url(r'^system/role/list/?$', BanBanTong.views.system.role.list_current),
#     url(r'^system/role/add/?$', BanBanTong.views.system.role.add),
#     url(r'^system/role/detail/?$', BanBanTong.views.system.role.detail),
#     url(r'^system/role/edit/?$', BanBanTong.views.system.role.edit),
#     url(r'^system/role/delete/?$', BanBanTong.views.system.role.delete),

#     # 系统设置>校级服务器设置
#     url(r'^system/school-server-setting/get/?$',
#         BanBanTong.views.system.school_server_setting.get),
#     url(r'^system/school-server-setting/set/?$',
#         BanBanTong.views.system.school_server_setting.set),

#     # 系统设置>基础信息同步查看
#     url(r'^system/baseinfo/term/?$',
#         BanBanTong.views.system.baseinfo.term),
#     url(r'^system/baseinfo/lesson-name/?$',
#         BanBanTong.views.system.baseinfo.lesson_name),
#     url(r'^system/baseinfo/resource-from/?$',
#         BanBanTong.views.system.baseinfo.resource_from),
#     url(r'^system/baseinfo/resource-type/?$',
#         BanBanTong.views.system.baseinfo.resource_type),

#     # 系统设置>桌面预览设置
#     url(r'^system/desktop-preview/get/?$',
#         BanBanTong.views.system.desktop_preview.get),
#     url(r'^system/desktop-preview/set/?$',
#         BanBanTong.views.system.desktop_preview.set),
#     url(r'^system/desktop-preview/verify/?$',
#         BanBanTong.views.system.desktop_preview.verify),

#     # 系统设置>资源管理
#     url(r'^system/resource/resource-from/?$',
#         BanBanTong.views.system.resource.resource_from),
#     url(r'^system/resource/resource-from/add/?$',
#         BanBanTong.views.system.resource.resource_from_add),
#     url(r'^system/resource/resource-from/delete/?$',
#         BanBanTong.views.system.resource.resource_from_delete),
#     url(r'^system/resource/resource-type/?$',
#         BanBanTong.views.system.resource.resource_type),
#     url(r'^system/resource/resource-type/add/?$',
#         BanBanTong.views.system.resource.resource_type_add),
#     url(r'^system/resource/resource-type/delete/?$',
#         BanBanTong.views.system.resource.resource_type_delete),

#     # 系统设置>教职人员信息管理
#     url(r'^system/teacher/list/?$',
#         BanBanTong.views.system.teacher.list_current),
#     url(r'^system/teacher/add/?$', BanBanTong.views.system.teacher.add),
#     url(r'^system/teacher/edit/?$', BanBanTong.views.system.teacher.edit),
#     url(r'^system/teacher/delete/?$', BanBanTong.views.system.teacher.delete),
#     url(r'^system/teacher/export/?$',
#         BanBanTong.views.system.teacher.export),
#     url(r'^system/teacher/import/?$',
#         BanBanTong.views.system.teacher.import_from),
#     url(r'^system/teacher/verify/?$',
#         BanBanTong.views.system.teacher.verify),
#     url(r'^system/teacher/password-reset/?$',
#         BanBanTong.views.system.teacher.reset_pwd),

#     # 系统设置>学校开课课程管理
#     url(r'^system/lesson-name/list/?$',
#         BanBanTong.views.system.lesson_name.list_current),
#     url(r'^system/lesson-name/list/class/?$',
#         BanBanTong.views.system.lesson_name.list_current_class),
#     url(r'^system/lesson_name/add/?$',
#         BanBanTong.views.system.lesson_name.add),
#     url(r'^system/lesson_name/delete/?$',
#         BanBanTong.views.system.lesson_name.delete),
#     url(r'^system/lesson_name/import/?$',
#         BanBanTong.views.system.lesson_name.import_from),
#     url(r'^system/lesson_name/verify/?$',
#         BanBanTong.views.system.lesson_name.verify),

#     # 系统设置>学校开课课程管理(区县)
#     url(r'^system/new_lesson_name/list/?$',
#         BanBanTong.views.system.new_lesson_name.list_current),
#     url(r'^system/new_lesson_name/add/?$',
#         BanBanTong.views.system.new_lesson_name.add),
#     url(r'^system/new_lesson_name/edit/?$',
#         BanBanTong.views.system.new_lesson_name.edit),
#     url(r'^system/new_lesson_name/delete/?$',
#         BanBanTong.views.system.new_lesson_name.delete),
#     url(r'^system/new_lesson_name/import/?$',
#         BanBanTong.views.system.new_lesson_name.import_from),
#     url(r'^system/new_lesson_name/verify/?$',
#         BanBanTong.views.system.new_lesson_name.verify),

#     # 系统设置>学年学期管理
#     url(r'^system/term/list/?$', BanBanTong.views.system.term.list_current),
#     url(r'^system/term/add/?$', BanBanTong.views.system.term.add),
#     url(r'^system/term/edit/?$', BanBanTong.views.system.term.edit),
#     url(r'^system/term/finish/?$', BanBanTong.views.system.term.finish),
#     url(r'^system/term/import/?$', BanBanTong.views.system.term.import_from),
#     url(r'^system/term/list_school_year/?$',
#         BanBanTong.views.system.term.list_school_year),
#     url(r'^system/term/verify/?$', BanBanTong.views.system.term.verify),

#     # 系统设置>学年学期管理(区县)
#     url(r'^system/newterm/list/?$', BanBanTong.views.system.newterm.list_current),
#     url(r'^system/newterm/current-or-next/?$', BanBanTong.views.system.newterm.list_current_or_next),
#     url(r'^system/newterm/add/?$', BanBanTong.views.system.newterm.add),
#     url(r'^system/newterm/edit/?$', BanBanTong.views.system.newterm.edit),
#     url(r'^system/newterm/import/?$', BanBanTong.views.system.newterm.import_from),
#     url(r'^system/newterm/finish/?$', BanBanTong.views.system.newterm.finish),
#     url(r'^system/newterm/list_school_year/?$',
#         BanBanTong.views.system.newterm.list_school_year),
#     url(r'^system/newterm/verify/?$', BanBanTong.views.system.newterm.verify),

#     # 系统设置>学年学期管理>关联教材大纲
#     url(r'^system/term/syllabus/grade-list/?$',
#         BanBanTong.views.system.syllabus.grade_list),
#     url(r'^system/term/syllabus/grade-set/?$',
#         BanBanTong.views.system.syllabus.grade_set),
#     url(r'^system/term/syllabus/grade-enable/?$',
#         BanBanTong.views.system.syllabus.grade_enable),
#     url(r'^system/term/syllabus/lesson-enable/?$',
#         BanBanTong.views.system.syllabus.lesson_enable),
#     url(r'^system/term/syllabus/lesson-list/?$',
#         BanBanTong.views.system.syllabus.lesson_list),
#     url(r'^system/term/syllabus/lesson-del/?$',
#         BanBanTong.views.system.syllabus.lesson_del),
#     url(r'^system/term/syllabus/content-list/?$',
#         BanBanTong.views.system.syllabus.content_list),
#     url(r'^system/term/syllabus/courseware-list/?$',
#         BanBanTong.views.system.syllabus.courseware_list),
#     url(r'^system/term/syllabus/remote-get/?$',
#         BanBanTong.views.system.syllabus.remote_get),

#     # 系统设置>学校作息时间管理
#     url(r'^system/lesson_period/list/?$',
#         BanBanTong.views.system.lesson_period.list_current),
#     url(r'^system/lesson_period/add/?$',
#         BanBanTong.views.system.lesson_period.add),
#     url(r'^system/lesson_period/edit/?$',
#         BanBanTong.views.system.lesson_period.edit),
#     url(r'^system/lesson_period/delete/?$',
#         BanBanTong.views.system.lesson_period.delete),
#     url(r'^system/lesson_period/import/?$',
#         BanBanTong.views.system.lesson_period.import_from),
#     url(r'^system/lesson_period/verify/?$',
#         BanBanTong.views.system.lesson_period.verify),

#     # 系统设置>年级班级管理>班班通教室
#     url(r'^system/class/list/?$',
#         BanBanTong.views.system.class_mac.list_current),
#     url(r'^system/class/add/?$',
#         BanBanTong.views.system.class_mac.add),
#     url(r'^system/class/batch_add/?$',
#         BanBanTong.views.system.class_mac.batch_add),
#     url(r'^system/class/delete/?$',
#         BanBanTong.views.system.class_mac.delete),
#     url(r'^system/class/clear_mac/?$',
#         BanBanTong.views.system.class_mac.clear_mac),
#     url(r'^system/class/import/?$',
#         BanBanTong.views.system.class_mac.import_from),
#     url(r'^system/class/verify/?$',
#         BanBanTong.views.system.class_mac.verify),
#     url(r'^system/class/edit/?$',
#         BanBanTong.views.system.class_mac.edit),

#     # 系统设置>年级班级管理>电脑教室
#     url(r'^system/computer-class/all/?$',
#         BanBanTong.views.system.computer_class_mac.list_current),
#     url(r'^system/computer-class/add/?$',
#         BanBanTong.views.system.computer_class_mac.add),
#     url(r'^system/computer-class/edit/?$',
#         BanBanTong.views.system.computer_class_mac.edit),
#     url(r'^system/computer-class/delete/?$',
#         BanBanTong.views.system.computer_class_mac.delete),
#     url(r'^system/computer-class/clear_mac/?$',
#         BanBanTong.views.system.computer_class_mac.clear_mac),
#     url(r'^system/computer-class/curriculum/?$',
#         BanBanTong.views.system.computer_class_mac.view_curriculum),

#     # 系统设置>班级课程综合管理>班级课程表管理
#     url(r'^system/lesson_schedule/list/?$',
#         BanBanTong.views.system.lesson_schedule.list_current),
#     url(r'^system/lesson_schedule/import/?$',
#         BanBanTong.views.system.lesson_schedule.import_from),
#     url(r'^system/lesson-schedule/export/?$',
#         BanBanTong.views.system.lesson_schedule.export),
#     url(r'^system/lesson_schedule/verify/?$',
#         BanBanTong.views.system.lesson_schedule.verify),

#     # 系统设置>班级课程综合管理>班级课程授课老师管理
#     url(r'^system/lesson_teacher/list/?$',
#         BanBanTong.views.system.lesson_teacher.list_current),
#     url(r'^system/lesson_teacher/add/?$',
#         BanBanTong.views.system.lesson_teacher.add),
#     url(r'^system/lesson_teacher/delete/?$',
#         BanBanTong.views.system.lesson_teacher.delete),
#     url(r'^system/lesson_teacher/edit/?$',
#         BanBanTong.views.system.lesson_teacher.edit),
#     url(r'^system/lesson_teacher/import/?$',
#         BanBanTong.views.system.lesson_teacher.import_from),
#     url(r'^system/lesson_teacher/export/?$',
#         BanBanTong.views.system.lesson_teacher.export),
#     url(r'^system/lesson_teacher/verify/?$',
#         BanBanTong.views.system.lesson_teacher.verify),

#     # 系统设置>上级服务器设置
#     url(r'^system/sync_server/add/?$', BanBanTong.views.system.sync_server.add),
#     url(r'^system/sync_server/list/?$', BanBanTong.views.system.sync_server.list_current),
#     url(r'^system/setting/get/?$', BanBanTong.views.system.sync_server.get_settinginfo),

#     # 系统设置>数据恢复
#     url(r'^system/restore/?$',
#         BanBanTong.views.system.restore.restore),

#     # 系统设置>服务器汇聚管理
#     url(r'^system/node/add/?$',
#         BanBanTong.views.system.node.add),
#     url(r'^system/node/delete/?$',
#         BanBanTong.views.system.node.delete),
#     url(r'^system/node/edit/?$',
#         BanBanTong.views.system.node.edit),
#     url(r'^system/node/list/?$',
#         BanBanTong.views.system.node.list_current),
#     url(r'^system/node/backup/?$',
#         BanBanTong.views.system.node.backup),
#     url(r'^what-is-the-meaning-of/(?P<status>\w+)/?$',
#         BanBanTong.views.system.node.what_is_the_meaning_of),
#     url(r'^what-is-the-meaning-of/-(?P<status>\w+)/?$', BanBanTong.views.system.node.what_is_the_meaning_of, {'foo': -1}),

#     # 帮助>关于
#     url(r'^system/about/?$',
#         BanBanTong.views.system.about.about),
#     # 帮助>授权信息
#     url(r'^system/activation/?$',
#         BanBanTong.views.system.about.activation),
#     url(r'^system/keys/(?P<seed>\w+)/?$',
#         BanBanTong.views.system.util.get_unlock_key),
# ]

# # 客户端
# urlpatterns += [
#     # 客户端>普通教室
#     url(r'^api/server_settings/?$', BanBanTong.views.api.interfaces.index.server_settings),
#     url(r'^api/lesson/status/?$', BanBanTong.views.api.interfaces.lesson.status),

#     # 客户端>电脑教室
#     url(r'^api/server_settings/computer-class/?$',
#         BanBanTong.views.api.interfaces.computerclass_client.get_current_or_nextlesson),
#     url(r'^api/lesson/status/computer-class/?$',
#         BanBanTong.views.api.interfaces.computerclass_client.get_lessonstatus),
#     url(r'^api/computer-class/all/?$', BanBanTong.views.api.interfaces.computerclass_client.get_unreported),
#     url(r'^api/computer-class/classes/?$',
#         BanBanTong.views.api.interfaces.computerclass_client.get_baseinfo),

#     # 客户端>通用
#     url(r'^api/grade-class/?$', BanBanTong.views.api.interfaces.computerclass_client.get_grade_class),
#     url(r'^api/resource/from/?$', BanBanTong.views.api.interfaces.index.get_resourcefrom),
#     url(r'^api/resource/type/?$', BanBanTong.views.api.interfaces.index.get_resourcetypes),
#     url(r'^api/client/clean-token/?$', BanBanTong.views.api.interfaces.client.clean_token),
#     url(r'^api/client-status/?$', BanBanTong.views.api.interfaces.client.get_client_status),
#     url(r'^api/user_login/?$', BanBanTong.views.api.interfaces.class_mac.user_login),
#     url(r'^api/get_mac_status/?$', BanBanTong.views.api.interfaces.class_mac.get_mac_status),
#     url(r'^api/report_mac/?$', BanBanTong.views.api.interfaces.class_mac.report_mac),
#     url(r'^api/usb_check/?$', BanBanTong.views.api.interfaces.teacher.usb_check),
#     url(r'^api/lesson/start/?$', BanBanTong.views.api.interfaces.lesson.start),
#     url(r'^api/lesson/start_status/?$', BanBanTong.views.api.interfaces.lesson.start_status),
#     url(r'^api/lesson/syllabus-content/?$', BanBanTong.views.api.interfaces.lesson.syllabus_content),
#     url(r'^api/screen-upload/?$', BanBanTong.views.api.interfaces.desktop_preview.screen_upload),
#     url(r'^api/desktop-preview/get/?$', BanBanTong.views.api.interfaces.desktop_preview.get_settings),
#     url(r'^api/pic/?$', BanBanTong.views.api.interfaces.desktop_preview.file_upload),
#     url(r'^api/courseware/check-md5/?$', BanBanTong.views.api.interfaces.courseware.check_md5),
#     url(r'^api/courseware/upload/?$', BanBanTong.views.api.interfaces.courseware.upload),
#     url(r'^api/courseware/upload-test/?$', BanBanTong.views.api.interfaces.courseware.upload_test),
# ]

# # 服务器端
# urlpatterns += [
#     # 服务器同步
#     url(r'^api/sync/login/?$',
#         BanBanTong.views.api.interfaces.client_sync.login),
#     url(r'^api/sync/school/?$',
#         BanBanTong.views.api.interfaces.client_sync.school),
#     url(r'^api/sync/last_active/?$',
#         BanBanTong.views.api.interfaces.client_sync.last_active),
#     url(r'^api/sync/login_status/?$',
#         BanBanTong.views.api.interfaces.client_sync.login_status),
#     url(r'^api/sync/status/?$',
#         BanBanTong.views.api.interfaces.client_sync.status),
#     url(r'^api/sync/upload/(?P<token>.*)/?$',
#         BanBanTong.views.api.interfaces.client_sync.upload),

#     # 下级服务器传递在线状态给上级
#     url(r'^api/class/set-active-status/?$',
#         BanBanTong.views.api.interfaces.class_mac.set_active_status),

#     # 下级服务器数据恢复
#     url(r'^install/remote/setting/?$',
#         BanBanTong.views.system.remote.restore),
#     url(r'^install/remote/setting/test/?$',
#         BanBanTong.views.system.remote.restore_test),
#     url(r'^install/remote/status/?$',
#         BanBanTong.views.system.remote.status),

#     # 上级服务器数据恢复
#     url(r'^api/restore/?$',
#         BanBanTong.views.api.interfaces.restore.restore),
#     url(r'^api/restore/test/?$',
#         BanBanTong.views.api.interfaces.restore.restore_test),

#     # 校级从县级获取学期课程资源
#     url(r'^api/term-lesson-resource/?$',
#         BanBanTong.views.api.interfaces.term_lesson_resource.getall),

#     # 校级从县级获取教材大纲
#     url(r'^api/sync/country-to-school/?$',
#         BanBanTong.views.api.interfaces.country_to_school.get),

#     # 第三方API
#     # 颂大
#     url(r'^api/songda-login/?$',
#         BanBanTong.views.api.third_party.songda.login),
#     # 辰云
#     url(r'^api/morningcloud/login/?$',
#         BanBanTong.views.api.third_party.morningcloud.login),

#     # 调试API
#     url(r'^version/?$', BanBanTong.views.index.version),
#     url(r'^maintain/?$', BanBanTong.views.system.maintain.index),
#     url(r'^maintain/auth/?$', BanBanTong.views.system.maintain.auth),
#     url(r'^maintain/info/?$', BanBanTong.views.system.maintain.info),
#     url(r'^maintain/log/?$', BanBanTong.views.system.maintain.log),
#     url(r'^maintain/log/download/?$',
#         BanBanTong.views.system.maintain.log_download),
#     url(r'^maintain/desktop-preview/network-diagnose/?$',
#         BanBanTong.views.maintain.desktop_preview.network_diagnose),
#     url(r'^resource-collect/?$',
#         BanBanTong.views.resource_collect.index.index),
#     url(r'^maintain/resync/set/?$', BanBanTong.views.maintain.resync.set),
# ]

# urlpatterns += [
#     url(r'^public/(?P<path>.*)/?$', static.serve,
#         {'document_root': settings.PUBLIC_ROOT}),
#     url(r'^logs/(?P<path>.*)/?$', static.serve,
#         {'document_root': BanBanTong.constants.LOG_PATH}),
#     # url(r'^templates/(?P<path>.*)/?$', static.serve,
#     #     {'document_root': settings.TEMPLATE_DIRS[0]}),
# ]

# # 客户端升级文件
# urlpatterns += [
#     url(r'^software/updates(?P<static_file>/.+\..+)\?*.*/?$', BanBanTong.views.static.serve_software_update),
#     url(r'^software/edufiles(?P<static_file>/.+\..+)\?*.*/?$', BanBanTong.views.static.serve_software_edufiles),
# ]

# # 供测试用的一些
# urlpatterns += [
#     url(r'^test4lessonperiod/?$', BanBanTong.views.system.lesson_period.create_lesson_period4test),
#     url(r'^test/run/calculate_teaching_analysis/',
#         BanBanTong.commands.management.commands.calculate_teaching_analysis.run_by_http),
#     url(r'^test/run/create_statistic_items/',
#         BanBanTong.commands.management.commands.create_statistic_items.run_by_http),
#     url(r'^test/run/calculate_statistic/',
#         BanBanTong.commands.management.commands.create_statistic_items.run_by_http),
#     url(r'^test/run/generate_node_setting_cachefiles/',
#         BanBanTong.commands.management.commands.generate_node_setting_cachefiles.run_by_http),
#     url(r'^test/run/recreate_fks_for_loginlogs/',
#         BanBanTong.commands.management.commands.recreate_fks_for_loginlogs.run_by_http),
#     url(r'^test/run/update_current_statistic_items/',
#         BanBanTong.commands.management.commands.update_current_statistic_items.run_by_http),
#     url(r'^test/run/inherit_items_from_last_term/',
#         edu_point.management.commands.inherit_items_from_last_term.run_by_http),
# ]
