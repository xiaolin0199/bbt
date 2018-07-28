#!/usr/bin/env python
# coding=utf-8
privileges_general = {
    'key': 'general', 'name': '实时概况',
    'privileges': [
        {'key': 'global_statistic', 'name': '全局数据'},
        {'key': 'global_desktop_preview', 'name': '桌面预览'},
    ]
}
privileges_maintenance = {
    'key': 'maintenance', 'name': '运维管理',
    'privileges': [
        {'key': 'maintenance_reset', 'name': '终端远程关机重启'},
        {'key': 'maintenance_vnc', 'name': '远程桌面协助'},
        {'key': 'maintenance_post', 'name': '校园电子公告'},
    ]
}
privileges_activity = {
    'key': 'activity', 'name': '教师授课',
    'privileges': [
        {'key': 'teacher_lesson_statistic', 'name': '班班通授课次数统计'},
        {'key': 'time_used_statistic', 'name': '班班通授课时长统计'},
        {'key': 'teacher_number_statistic', 'name': '班班通授课人数统计'},
        {'key': 'activity_desktop_preview', 'name': '班班通桌面使用日志'},
        {'key': 'logged_in', 'name': '学校终端登录日志'},
    ]
}
privileges_resource = {
    'key': 'resource', 'name': '资源使用',
    'privileges': [
        {'key': 'resource_global_statistic', 'name': '资源使用综合分析'},
        {'key': 'resource_from_statistic', 'name': '资源来源使用统计'},
        {'key': 'resource_type_statistic', 'name': '资源类型使用统计'},
    ]
}
privileges_asset = {
    'key': 'asset', 'name': '资产管理',
    'privileges': [
        {'key': 'machine_time_used_statistic', 'name': '学校终端开机统计'},
        {'key': 'machine_time_used_log', 'name': '终端开机日志'},
        {'key': 'asset_log', 'name': '资产统计与申报'},
        {'key': 'asset_report_log', 'name': '资产申报记录查询'},
        {'key': 'asset_repair', 'name': '资产维修管理'},
    ]
}
privileges_system = {
    'key': 'system', 'name': '系统设置',
    'privileges': [
        {'key': 'system_user', 'name': '用户管理'},
        {'key': 'system_role', 'name': '角色管理'},
        {'key': 'system_school_server_setting', 'name': '校级服务器设置'},
        {'key': 'system_baseinfo', 'name': '基础信息同步查看'},
        {'key': 'system_teacher', 'name': '教职人员信息管理'},
        {'key': 'system_lesson_period', 'name': '学校作息时间管理'},
        {'key': 'system_grade_class', 'name': '年级班级管理'},
        {'key': 'system_class_lesson', 'name': '班级课程综合管理'},
        {'key': 'system_sync_server', 'name': '上级服务器设置'},
        # {'key': 'unlock_key', 'name': '超级密码'},
        # {'key': 'uninstall_key', 'name': '客户端卸载密码'},
    ]
}
privileges_help = {
    'key': 'help', 'name': '帮助',
    'privileges': [
        {'key': 'system_activation', 'name': '授权信息'},
        {'key': 'system_about', 'name': '关于'},
    ]
}
PRIVILEGES = {}
PRIVILEGES['school'] = [
    privileges_general,
    privileges_maintenance,
    privileges_activity,
    privileges_resource,
    # privileges_statistic,
    privileges_asset,
    privileges_system,
    privileges_help,
]

privileges_general = {
    'key': 'general', 'name': '实时概况',
    'privileges': [
        {'key': 'global_statistic', 'name': '班班通全局数据'},
        {'key': 'global_computer_room', 'name': '电脑教室全局数据'},
        {'key': 'global_login_status', 'name': '班班通登录状态'},
        {'key': 'global_desktop_preview', 'name': '班班通桌面预览'},
        {'key': 'global_computer_room_desktop_preview', 'name': '电脑教室桌面预览'},
    ]
}
privileges_activity = {
    'key': 'activity', 'name': '教师授课',
    'privileges': [
        {'key': 'teaching_analysis', 'name': '班班通授课综合分析'},
        {'key': 'teacher_lesson_statistic', 'name': '班班通授课次数统计'},
        {'key': 'time_used_statistic', 'name': '班班通授课时长统计'},
        {'key': 'teacher_number_statistic', 'name': '班班通授课人数统计'},
        {'key': 'edu_unit_classroom_statistic', 'name': '教学点教室使用统计'},
        {'key': 'activity_desktop_preview', 'name': '班班通桌面使用日志'},
        {'key': 'activity_edu_unit_preview', 'name': '教学点桌面使用日志'},
        {'key': 'logged_in', 'name': '学校终端登录日志'},
        {'key': 'edu_unit_logged_in', 'name': '教学点终端使用日志'},
    ]
}
privileges_resource = {
    'key': 'resource', 'name': '资源使用',
    'privileges': [
        {'key': 'resource_global_statistic', 'name': '资源使用综合分析'},
        {'key': 'resource_from_statistic', 'name': '资源来源使用统计'},
        {'key': 'resource_type_statistic', 'name': '资源类型使用统计'},
        {'key': 'resource_satellite_statistic', 'name': '卫星资源接收统计'},
        {'key': 'resource_satellite_log', 'name': '卫星资源接收日志'},
    ]
}
privileges_asset = {
    'key': 'asset', 'name': '资产管理',
    'privileges': [
        {'key': 'machine_time_used_statistic', 'name': '学校终端开机统计'},
        {'key': 'edu_unit_machine_time_used_statistic', 'name': '教学点终端开机统计'},
        {'key': 'machine_time_used_log', 'name': '终端开机日志'},
        {'key': 'asset_log', 'name': '资产统计'},
        {'key': 'asset_report_log', 'name': '资产申报记录查询'},
        {'key': 'asset_repair', 'name': '资产维修查询'},
    ]
}
privileges_system = {
    'key': 'system', 'name': '系统设置',
    'privileges': [
        {'key': 'system_user', 'name': '用户管理'},
        {'key': 'system_role', 'name': '角色管理'},
        {'key': 'system_country_server_setting', 'name': '区县市级服务器设置'},
        {'key': 'system_resource', 'name': '资源管理'},
        {'key': 'system_newterm', 'name': '学年学期管理'},
        {'key': 'system_new_lesson_name', 'name': '学校开课课程管理'},
        {'key': 'system_desktop_preview', 'name': '桌面预览设置'},
        {'key': 'system_edu_unit', 'name': '教学点管理'},
        {'key': 'system_node', 'name': '服务器汇聚管理'},
        {'key': 'system_sync_server', 'name': '上级服务器设置'},
    ]
}
privileges_help = {
    'key': 'help', 'name': '帮助',
    'privileges': [
        {'key': 'system_activation', 'name': '授权信息'},
        {'key': 'system_about', 'name': '关于'},
    ]
}
PRIVILEGES['country'] = [
    privileges_general,
    privileges_activity,
    privileges_resource,
    privileges_asset,
    privileges_system,
    privileges_help,
]
