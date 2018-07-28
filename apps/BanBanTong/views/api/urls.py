# coding=utf-8
from django.conf.urls import url
import interfaces.sync_server
import interfaces.computerclass_client
import interfaces.index
import interfaces.client
import interfaces.teacher
import interfaces.lesson
import interfaces.desktop_preview
import interfaces.courseware
import interfaces.client_sync
import interfaces.class_mac
import interfaces.restore
import interfaces.term_lesson_resource
import interfaces.country_to_school
import third_party.songda
import third_party.morningcloud
import BanBanTong.views.system.node

urlpatterns = [
    url(r'^sync-server/verify/?$', interfaces.sync_server.verify),
    url(r'^sync-server/check-data/?$', interfaces.sync_server.check_data),

    # 客户端
    # 系统安装>校级服务器获取上级服务器省市区信息
    url(r'^sync-server/get-group/?$', interfaces.sync_server.get_group),
    # 系统安装>校级从县级获取NODE ID
    url(r'^sync-server/get_node_id/?$', BanBanTong.views.system.node.get_node_id),

    # 客户端>普通教室
    url(r'^server_settings/?$', interfaces.index.server_settings),
    url(r'^lesson/status/?$', interfaces.lesson.status),
    # 客户端>电脑教室
    url(r'^server_settings/computer-class/?$', interfaces.computerclass_client.get_current_or_nextlesson),
    url(r'^lesson/status/computer-class/?$', interfaces.computerclass_client.get_lessonstatus),
    url(r'^computer-class/all/?$', interfaces.computerclass_client.get_unreported),
    url(r'^computer-class/classes/?$', interfaces.computerclass_client.get_baseinfo),
    # 客户端>通用
    url(r'^grade-class/?$', interfaces.computerclass_client.get_grade_class),
    url(r'^resource/from/?$', interfaces.index.get_resourcefrom),
    url(r'^resource/type/?$', interfaces.index.get_resourcetypes),
    url(r'^client/clean-token/?$', interfaces.client.clean_token),
    url(r'^client-status/?$', interfaces.client.get_client_status),
    url(r'^user_login/?$', interfaces.class_mac.user_login),
    url(r'^get_mac_status/?$', interfaces.class_mac.get_mac_status),
    url(r'^report_mac/?$', interfaces.class_mac.report_mac),
    url(r'^usb_check/?$', interfaces.teacher.usb_check),
    url(r'^lesson/start/?$', interfaces.lesson.start),
    url(r'^lesson/start_status/?$', interfaces.lesson.start_status),
    url(r'^lesson/syllabus-content/?$', interfaces.lesson.syllabus_content),
    url(r'^screen-upload/?$', interfaces.desktop_preview.screen_upload),
    url(r'^desktop-preview/get/?$', interfaces.desktop_preview.get_settings),
    url(r'^pic/?$', interfaces.desktop_preview.file_upload),
    url(r'^courseware/check-md5/?$', interfaces.courseware.check_md5),
    url(r'^courseware/upload/?$', interfaces.courseware.upload),
    url(r'^courseware/upload-test/?$', interfaces.courseware.upload_test),

    # 服务器端
    # 服务器同步
    url(r'^sync/login/?$', interfaces.client_sync.login),
    url(r'^sync/school/?$', interfaces.client_sync.school),
    url(r'^sync/last_active/?$', interfaces.client_sync.last_active),
    url(r'^sync/login_status/?$', interfaces.client_sync.login_status),
    url(r'^sync/status/?$', interfaces.client_sync.status),
    url(r'^sync/upload/(?P<token>.*)/?$', interfaces.client_sync.upload),
    # 下级服务器传递在线状态给上级
    url(r'^class/set-active-status/?$', interfaces.class_mac.set_active_status),
    # 上级服务器数据恢复
    url(r'^restore/?$', interfaces.restore.restore),
    url(r'^restore/test/?$', interfaces.restore.restore_test),
    # 校级从县级获取学期课程资源
    url(r'^term-lesson-resource/?$', interfaces.term_lesson_resource.getall),
    # 校级从县级获取教材大纲
    url(r'^sync/country-to-school/?$', interfaces.country_to_school.get),
    # 第三方API
    # 颂大
    url(r'^songda-login/?$', third_party.songda.login),
    # 辰云
    url(r'^morningcloud/login/?$', third_party.morningcloud.login),
]
