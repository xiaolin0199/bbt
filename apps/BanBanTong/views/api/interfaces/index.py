# coding=utf-8
import datetime
import traceback

from BanBanTong.db import models
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import simplecache


# 获取资源来源
def get_resourcefrom(request):
    data = {}
    rf = models.ResourceFrom.objects.values('value')
    data['resource_from'] = map(lambda o: {
        'key': o['value'],
        'text': o['value'],
    }, rf)

    return create_success_dict(data=data)

# 获取资源类型


def get_resourcetypes(request):
    data = {}
    rt = models.ResourceType.objects.values('value')
    data['resource_type'] = map(lambda o: {
        'key': o['value'],
        'text': o['value'],
    }, rt)

    return create_success_dict(data=data)


#
def server_settings(request, *args, **kwargs):
    if models.Setting.getvalue('server_type') != 'school':
        return create_failure_dict()
    if request.method == 'GET':
        mac = request.GET.get('mac')
        try:
            t = models.Term.get_current_term_list()[0]
            c = models.Class.objects.get(
                classmacv2__mac=mac,
                grade__term=t
            )
        except:
            traceback.print_exc()
            return create_failure_dict()

        data = {
            'status': False,
            'resource_from': [],  # 资源来源
            'resource_types': [],  # 资源类型
            'all_teachers': [],  # 班级c的所有授课教师
            'teacher': [],  # 班级c当前节次的所有授课教师
            'lesson': [],  # 班级c当前节次所有课程
            'info': {},  # 当前节次默认上课信息
        }

        # resource_from
        q = models.ResourceFrom.objects.values('value')
        for i in q:
            data['resource_from'].append({
                'key': i['value'],
                'text': i['value']
            })

        # resource_types
        q = models.ResourceType.objects.values('value')
        for i in q:
            data['resource_types'].append({
                'key': i['value'],
                'text': i['value']
            })

        # all_teachers
        q = simplecache.LessonTeacher.get_teachers_lessons(c)
        teachers = {}
        for i in q:
            if i['teacher__uuid'] not in teachers:
                teachers[i['teacher__uuid']] = {
                    'key': i['teacher__uuid'],
                    'text': i['teacher__name'],
                    'lessons': []
                }

            teachers[i['teacher__uuid']]['lessons'].append({
                'key': i['lesson_name__name'],
                'text': i['lesson_name__name']
            })
        for i in teachers:
            data['all_teachers'].append(teachers[i])

        # teacher/lesson
        # V4.3.0修改过后,有课表的时候,这里就会显示一个默认的课程
        is_current, ls = simplecache.LessonSchedule.get_current(c)
        if ls:
            try:
                lt = models.LessonTeacher.objects.filter(
                    class_uuid=c,
                    lesson_name__name=ls['lesson_name__name']
                )
                t = [{
                    'key': i.teacher.uuid,
                    'text': i.teacher.name
                } for i in lt]
                data['teacher'] = t
                data['lesson'] = [{
                    'key': ls['lesson_name__name'],
                    'text': ls['lesson_name__name']
                }]
            except:
                pass

        now = datetime.datetime.now()
        s = datetime.datetime.combine(now.date(), datetime.time.min)
        e = datetime.datetime.combine(now.date(), datetime.time.max)
        q = models.TeacherLoginLog.objects.filter(
            created_at__range=(s, e),
            lesson_period_start_time__lte=now.time(),
            lesson_period_end_time__gte=now.time(),
            class_uuid=c,
        )
        if q.exists():
            data['status'] = True
            lesson = models.LessonName.objects.get(name=q[0].lesson_name)
            data['info'] = {
                'teacher_key': q[0].teacher.uuid,
                'password': q[0].teacher.password,
                'lesson_key': lesson.uuid,
                'resource_from': q[0].resource_from,
                'resource_types': q[0].resource_type,
                'server_time': now,
                'time': q[0].lesson_period_end_time
            }
        return create_success_dict(data=data)
