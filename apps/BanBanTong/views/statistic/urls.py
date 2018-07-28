# coding=utf-8
from django.conf.urls import url

import resource_from
import resource
import resource_type
import teacher_active
import teaching_analysis
import teaching_time
import time_used


# 基础信息
urlpatterns = [
    # 教师授课>班班通授课综合分析
    # 1 班班通授课综合分析
    url(r'^teaching-analysis/lesson-count/?$', teaching_analysis.url_has_been_abandoned),
    url(r'^teaching-analysis/total-time/?$', teaching_analysis.url_has_been_abandoned),
    url(r'^teaching-analysis/lesson-name/?$', teaching_analysis.url_has_been_abandoned),
    url(r'^teaching-analysis/count/by-lesson/?$', teaching_analysis.lesson_count),
    url(r'^teaching-analysis/count/by-grade/?$', teaching_analysis.grade_count),
    url(r'^teaching-analysis/count/by-week/?$', teaching_analysis.week_count),
    url(r'^teaching-analysis/count/by-week/average/?$', teaching_analysis.week_count_average),
    url(r'^teaching-analysis/time/by-week/?$', teaching_analysis.week_time),
    url(r'^teaching-analysis/time/by-week/average/?$', teaching_analysis.week_time_average),
    url(r'^teaching-analysis/count/total/?$', teaching_analysis.week_count_total),
    url(r'^teaching-analysis/count/total/average/?$', teaching_analysis.week_count_total_average),
    url(r'^teaching-analysis/time/total/?$', teaching_analysis.week_time_total),
    url(r'^teaching-analysis/time/total/average/?$', teaching_analysis.week_time_total_average),

    # 教师授课>班班通授课次数比例统计
    url(r'^teaching-time/by-country/?$', teaching_time.by_country),
    url(r'^teaching-time/by-town/?$', teaching_time.by_town),
    url(r'^teaching-time/by-school/?$', teaching_time.by_school),
    url(r'^teaching-time/by-grade/?$', teaching_time.by_grade),
    url(r'^teaching-time/by-class/?$', teaching_time.by_class),
    url(r'^teaching-time/by-lessonteacher/?$', teaching_time.by_lessonteacher),
    url(r'^teaching-time/by-teacher/?$', teaching_time.by_teacher),
    url(r'^teaching-time/by-country/export/?$', teaching_time.by_country_export),
    url(r'^teaching-time/by-town/export/?$', teaching_time.by_town_export),
    url(r'^teaching-time/by-school/export/?$', teaching_time.by_school_export),
    url(r'^teaching-time/by-grade/export/?$', teaching_time.by_grade_export),
    url(r'^teaching-time/by-class/export/?$', teaching_time.by_class_export),
    url(r'^teaching-time/by-lessonteacher/export/?$', teaching_time.by_lessonteacher_export),
    url(r'^teaching-time/by-teacher/export/?$', teaching_time.by_teacher_export),

    # 教师授课>班班通授课时长统计
    url(r'^time-used/by-country/?$', time_used.by_country),
    url(r'^time-used/by-country/export/?$', time_used.by_country_export),
    url(r'^time-used/by-town/?$', time_used.by_town),
    url(r'^time-used/by-town/export/?$', time_used.by_town_export),
    url(r'^time-used/by-school/?$', time_used.by_school),
    url(r'^time-used/by-school/export/?$', time_used.by_school_export),
    url(r'^time-used/by-grade/?$', time_used.by_grade),
    url(r'^time-used/by-grade/export/?$', time_used.by_grade_export),
    url(r'^time-used/by-class/?$', time_used.by_class),
    url(r'^time-used/by-class/export/?$', time_used.by_class_export),
    url(r'^time-used/by-teacher/?$', time_used.by_teacher),
    url(r'^time-used/by-teacher/export/?$', time_used.by_teacher_export),
    url(r'^time-used/by-lessonteacher/?$', time_used.by_lessonteacher),
    url(r'^time-used/by-lessonteacher/export/?$', time_used.by_lessonteacher_export),

    # 教师授课>教师授课人数比例统计
    url(r'^teacher-active/by-country/?$', teacher_active.by_country),
    url(r'^teacher-active/by-country/export/?$', teacher_active.by_country_export),
    url(r'^teacher-active/by-grade/?$', teacher_active.by_grade),
    url(r'^teacher-active/by-grade/export/?$', teacher_active.by_grade_export),
    url(r'^teacher-active/by-lesson/?$', teacher_active.by_lesson),
    url(r'^teacher-active/by-lesson/export/?$', teacher_active.by_lesson_export),
    url(r'^teacher-active/by-lessongrade/?$', teacher_active.by_lessongrade),
    url(r'^teacher-active/by-lessongrade/export/?$', teacher_active.by_lessongrade_export),
    url(r'^teacher-active/by-school/?$', teacher_active.by_school),
    url(r'^teacher-active/by-school/export/?$', teacher_active.by_school_export),
    url(r'^teacher-active/by-town/?$', teacher_active.by_town),
    url(r'^teacher-active/by-town/export/?$', teacher_active.by_town_export),

    # 统计分析->授课资源使用统计
    # url(r'^resource/resource-from/?$',    #    resource.resource_from),
    # url(r'^resource/resource-from/export/?$',    #    resource.resource_from_export),
    # url(r'^resource/resource-type/?$',    #    resource.resource_type),
    # url(r'^resource/resource-type/export/?$',    #    resource.resource_type_export),
    # url(r'^resource/teacher/?$',    #    resource.teacher),
    # url(r'^resource/teacher/export/?$',    #    resource.teacher_export),
    # url(r'^resource/lesson/?$',    #    resource.lesson),
    # url(r'^resource/lesson/export/?$',    #    resource.lesson_export),

    # 资源使用>资源使用综合分析
    url(r'^resource-global/?$', resource.resource_global),
    # 资源使用>资源来源使用分析
    url(r'^resource-from/town/?$', resource_from.by_town),
    url(r'^resource-from/town/export/?$', resource_from.by_town_export),
    url(r'^resource-from/school/?$', resource_from.by_school),
    url(r'^resource-from/school/export/?$', resource_from.by_school_export),
    url(r'^resource-from/class/?$', resource_from.by_class),
    url(r'^resource-from/class/export/?$', resource_from.by_class_export),
    url(r'^resource-from/lesson/?$', resource_from.by_lesson),
    url(r'^resource-from/lesson/export/?$', resource_from.by_lesson_export),
    url(r'^resource-from/teacher/?$', resource_from.by_teacher),
    url(r'^resource-from/teacher/export/?$', resource_from.by_teacher_export),
    # 资源使用>资源类型使用分析
    url(r'^resource-type/town/?$', resource_type.by_town),
    url(r'^resource-type/town/export/?$', resource_type.by_town_export),
    url(r'^resource-type/school/?$', resource_type.by_school),
    url(r'^resource-type/school/export/?$', resource_type.by_school_export),
    url(r'^resource-type/class/?$', resource_type.by_class),
    url(r'^resource-type/class/export/?$', resource_type.by_class_export),
    url(r'^resource-type/lesson/?$', resource_type.by_lesson),
    url(r'^resource-type/lesson/export/?$', resource_type.by_lesson_export),
    url(r'^resource-type/teacher/?$', resource_type.by_teacher),
    url(r'^resource-type/teacher/export/?$', resource_type.by_teacher_export),

    # 教师授课>教师未登录班班通统计
    # url(r'statistic.teacher-absent/by-country/?$', BanBanTong.views.statistic.teacher_absent.by_country),
    # url(r'statistic.teacher-absent/by-country/export/?$', BanBanTong.views.statistic.teacher_absent.by_country_export),
    # url(r'statistic.teacher-absent/by-grade/?$', BanBanTong.views.statistic.teacher_absent.by_grade),
    # url(r'statistic.teacher-absent/by-grade/export/?$', BanBanTong.views.statistic.teacher_absent.by_grade_export),
    # url(r'statistic.teacher-absent/by-lesson/?$', BanBanTong.views.statistic.teacher_absent.by_lesson),
    # url(r'statistic.teacher-absent/by-lesson/export/?$', BanBanTong.views.statistic.teacher_absent.by_lesson_export),
    # url(r'statistic.teacher-absent/by-lessongrade/?$', BanBanTong.views.statistic.teacher_absent.by_lessongrade),
    # url(r'statistic.teacher-absent/by-lessongrade/export/?$', BanBanTong.views.statistic.teacher_absent.by_lessongrade_export),
    # url(r'statistic.teacher-absent/by-school/?$', BanBanTong.views.statistic.teacher_absent.by_school),
    # url(r'statistic.teacher-absent/by-school/export/?$', BanBanTong.views.statistic.teacher_absent.by_school_export),
    # url(r'statistic.teacher-absent/by-town/?$', BanBanTong.views.statistic.teacher_absent.by_town),
    # url(r'statistic.teacher-absent/by-town/export/?$', BanBanTong.views.statistic.teacher_absent.by_town_export),
]
