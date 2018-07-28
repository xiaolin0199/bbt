# coding=utf-8
from oslo_config import cfg


api_service_opts = [
    cfg.BoolOpt('debug', default=False, help='DEBUG'),
    cfg.StrOpt('sync_type', default='normal', choices=['normal', 'json'], help='DEFAULT[HOST]'),
    cfg.URIOpt('hostname', default='http://127.0.0.1:80', help='DEFAULT[HOST]'),
    cfg.StrOpt('job_start_path', default='/api/start-job/', help='DEFAULT[PORT]'),
    cfg.StrOpt('school_domain_path', default='/api/school-info/', help='DEFAULT[PORT]'),
    cfg.StrOpt('school_info_path', default='/api/school-info/', help='DEFAULT[PORT]'),
    cfg.StrOpt('json_path', default='/api/school-info/', help='DEFAULT[PORT]'),
    cfg.StrOpt('school_id', default='', help='DEFAULT[HOST]'),
    cfg.StrOpt('class_path', default='/api/class/', help='DEFAULT[PORT]'),
    cfg.StrOpt('teacher_path', default='/api/teacher/', help='DEFAULT[PORT]'),
    cfg.StrOpt('lesson_teacher_path', default='/api/lesson-teacher/', help='DEFAULT[PORT]'),
    cfg.StrOpt('school_openapi_path', default='/api/query/', help='DEFAULT[PORT]'),
    cfg.StrOpt('teachers_key', default='teachers', help='DEFAULT[PORT]'),
    cfg.StrOpt('json_teacher_key', default='teachers', help='DEFAULT[PORT]'),
    cfg.StrOpt('lesson_teachers_key', default='lesson_teachers', help='DEFAULT[PORT]'),
    cfg.DictOpt('grade_name_map', default={
        u'小学-1': u'一',
        u'小学-2': u'二',
        u'小学-3': u'三',
        u'小学-4': u'四',
        u'小学-5': u'五',
        u'小学-6': u'六',
        u'初中-1': u'初一',
        u'初中-2': u'初二',
        u'初中-3': u'初三',
        u'高中-1': u'高一',
        u'高中-2': u'高二',
        u'高中-3': u'高三'
    }),
    cfg.DictOpt('json_key_map', default={
        # 班级
        "class_id": "class_id",
        "grade_name": "grade_name",
        "class_name": "class_name",
        # 教师
        "teacher_id": "teacher_id",
        "teacher_name": "teacher_name",
        "teacher_sex": "teacher_sex",
        "teacher_edu_background": "teacher_edu_background",
        "teacher_birthday": "teacher_birthday",
        "teacher_title": "teacher_title",
        "teacher_mobile": "teacher_mobile",
        "teacher_qq": "teacher_qq",
        "teacher_remark": "teacher_remark",
        "teacher_register_at": "teacher_register_at",
        # 授课教师
        # "teacher_id": "teacher_id",
        # "class_id": "class_id",
        # "teacher_name": "teacher_name",
        # "class_name": "class_name",
        "lesson_name": "lesson_name",
        "schedule_time": "schedule_time",
        # 作息时间
        "sequence": "sequence",
        "start_time": "start_time",
        "end_time": "end_timeme",
        # 课表
        "lesson_period": "lesson_period",
        "weekday": "weekdayay"
    }, help='DEFAULT[PORT]'),
]


api_group = cfg.OptGroup(name='sync_api', title='Options for the sync-api service')


ALL_OPTS = (api_service_opts)


def register_opts(conf):
    conf.register_group(api_group)
    conf.register_opts(ALL_OPTS, api_group)


def list_opts():
    return {
        api_group: ALL_OPTS
    }
