# coding=utf-8
"""
    banbantong 缓存timeout统一设定
"""

ONLINE_CACHE_KEY_PREFIX = 'class-teacher-online'
TOTALS_CACHE_KEY_PREFIX = 'class-teacher-totals'


CACHES = {
    'a': {
        'asset_list': 'null',
        'asset_log': 'null',
        'asset_repair_list': 'null',
        'asset_type_list': 'null',

    },
    'c': {
        'classes': 'null',
        'class-all': None,
        'class_noreport_heartbeat_ip': 90,
        # 'class-[class_uuid]-teacherlogintime': 90,
        'class-': 90,
        'cloud-service-clean-date': 60 * 60 * 24,
        # computerclass-teacher-%s-active-time
        'computerclass-teacher-': 90,
    },
    'g': {
        'grade-all': None,
        'grade_class_lesson_teacher': 60 * 45,
        'group-all': None,
        # 'group-[user_uuid]': 'null',
        'group-': 'null',
    },
    'l': {
        # 'lessonschedule-[class_uuid]-[weekday]': 60*60*24,
        'lessonschedule-': 60 * 60 * 24,
    },
    'p': {
        # 'permitted-groups-[user_uuid]': 'null',
        'permitted-groups-': 'null',
    },
    'r': {
        # 'resource_from_for_[mac]': 60*45,
        'resource_from_for_': 60 * 45,
        # 'resource-analysis-for-node-[node_uuid]': 60*10,
        'resource-analysis-for-node-': 60 * 10,
        # 'resource-from-by-[country/town/school/lesson/teacher]': 'null',
        'resource-from-by-': 'null',
        # 'resource-from-by-[country/town/school/class/lesson/teacher]': 'null',
        'resource-from-by-': 'null',
        # 'resource_types_for_[mac]': 60*45,
        'resource_types_for_': 60 * 45,
        'restore-status': 'null',
        # 'resync-[node_id]-[communicate_key]': 'null',
        'resync-': 'null',
    },
    's': {
        'simplecache_resource': None,
        'sudo': 'null',
        # 'simplecache_lesson_teacher_[class_uuid]': 'null',
        'simplecache_lesson_teacher_': 'null',
    },
    't': {
        # 'teacher-uuids-for-node-[node_uuid]': 60*60,
        'teacher-uuids-for-node-': 60 * 60,
        # 'teacher-absent-by-[country/town/school/grade/class/lesson/lessongrade]': 'null',
        'teacher-absent-by-': 'null',
        # 'teacher-active-by-[country/town/school/grade/lesson/lessongrade]': 'null',
        'teacher-active-by-': 'null',
        # 'teaching-analysis-lesson-count-[school_year]-[term_type]-[town_name]-[school_name]-[grade_name]-[class_name]': 60*60*4,
        'teaching-analysis-lesson-count-': 60 * 60 * 4,
        # 'teaching-analysis-total-time-[school_year]-[term_type]-[town_name]-[school_name]-[grade_name]-[class_name]': 60*60*4,
        'teaching-analysis-total-time-': 60 * 60 * 4,
        # 'teacher-[teacher-uuid]-active-time': 90,
        'teacher-': 90,
    }
}


def _get_cache_timeout(cache_key, timeout=None):
    if not isinstance(cache_key, str):
        try:
            # cache_key 中只比对字母,所以之类简单的转换一下就OK了
            cache_key = str(cache_key)
        except:
            pass

    d = CACHES.get(cache_key[0], [])
    for k in d:
        if k in cache_key:
            if d[k] == 'null':
                return None
            return d[k]
    if timeout == 'null':
        return None

    return timeout

get_timeout = _get_cache_timeout


if __name__ == '__main__':
    keys = []
    for i in CACHES:
        for k in CACHES[i]:
            t = _get_cache_timeout(k)
            keys.append(k)
    keys.extend([
        '12312',
        'dasgqgh',
        11,
        u'asdfasf',
        u'fadsfaz张三',
        'fadsfaz张三',

    ])

    for k in keys:
        print _get_cache_timeout(k)
