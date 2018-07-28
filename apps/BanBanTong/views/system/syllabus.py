#!/usr/bin/env python
# coding=utf-8
import requests
import traceback

from django.core.cache import cache
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import format_record
from BanBanTong.utils import model_list_to_dict
from BanBanTong.utils import model_to_dict


def content_list(request):
    pk = request.GET.get('id')
    q = models.SyllabusGradeLessonContent.objects.filter(syllabus_grade_lesson=pk)
    q = q.values().order_by('seq', 'subseq')
    q = format_record.syllabus_content_list(q)
    return create_success_dict(data={'records': model_list_to_dict(q)})


def grade_set(request):
    term_uuid = request.GET.get('term_uuid', '')
    try:
        t = models.NewTerm.objects.get(uuid=term_uuid)
    except:
        return create_failure_dict(msg='错误的学年学期')

    records = models.SyllabusGrade.objects.filter(school_year=t.school_year, term_type=t.term_type).values('grade_name', 'in_use')

    return create_success_dict(data={'records': model_list_to_dict(records)})


def grade_enable(request):
    if request.method == 'POST':
        if not cache.get('sudo'):
            return create_failure_dict(msg='请输入正确的超级管理员admin密码！')
        grade_name = request.POST.get('grade_name', '')
        term_uuid = request.POST.get('term_uuid', '')
        try:
            t = models.NewTerm.objects.get(uuid=term_uuid)
        except:
            return create_failure_dict(msg='错误的学年学期')

        try:
            obj = models.SyllabusGrade.objects.get(school_year=t.school_year, term_type=t.term_type, grade_name=grade_name)
        except:
            return create_failure_dict(msg='错误的年级')
        if obj.in_use:
            return create_failure_dict(msg='该年级大纲已启用')
        obj.in_use = True
        obj.save()
        return create_success_dict(msg='启用成功')


def grade_list(request):
    uu = request.GET.get('uuid')
    try:
        t = models.NewTerm.objects.get(uuid=uu)
    except:
        return create_failure_dict(msg='错误的uuid')
    q = models.SyllabusGrade.objects.filter(school_year=t.school_year,
                                            term_type=t.term_type)
    q = q.values('id', 'grade_name', 'in_use')
    return create_success_dict(data={'records': model_list_to_dict(q)})


def lesson_enable(request):
    if request.method == 'POST':
        if not cache.get('sudo'):
            return create_failure_dict(msg='请输入正确的超级管理员admin密码！')

        lesson_name = request.POST.get('lesson_name', '')
        grade_name = request.POST.get('grade_name', '')
        publish = request.POST.get('publish', '')
        bookversion = request.POST.get('bookversion', '')
        term_uuid = request.POST.get('term_uuid', '')
        try:
            t = models.NewTerm.objects.get(uuid=term_uuid)
        except:
            return create_failure_dict(msg='错误的学年学期')

        try:
            obj = models.SyllabusGradeLesson.objects.get(syllabus_grade__school_year=t.school_year, syllabus_grade__term_type=t.term_type,
                                                         syllabus_grade__grade_name=grade_name, lesson_name=lesson_name, publish=publish, bookversion=bookversion)
        except:
            return create_failure_dict(msg='错误的课程')

        if obj.in_use:
            return create_failure_dict(msg='该课程已启用')

        obj.in_use = True
        obj.save()

        return create_success_dict(msg='启用成功')


def lesson_list(request):
    #pk = request.GET.get('id')
    grade_name = request.GET.get('grade_name', '')
    term_uuid = request.GET.get('term_uuid', '')
    try:
        t = models.NewTerm.objects.get(uuid=term_uuid)
    except:
        return create_failure_dict(msg='错误的学年学期')

    # 保存syllabusgrade
    try:
        obj, c = models.SyllabusGrade.objects.get_or_create(school_year=t.school_year, term_type=t.term_type, grade_name=grade_name, defaults={'in_use': False})
    except:
        return create_failure_dict(msg='错误的班级信息')

    q = models.SyllabusGradeLesson.objects.filter(syllabus_grade=obj)
    q = q.values()

    return create_success_dict(data={'records': model_list_to_dict(q),
                                     'host': 'http://oebbt-cover.qiniudn.com',
                                     'RESOURCE_PLATFORM_HOST': constants.RESOURCE_PLATFORM_HOST})


def lesson_del(request):
    if request.method == 'POST':
        if not cache.get('sudo'):
            return create_failure_dict(msg='请输入正确的超级管理员admin密码！')

        id = request.POST.get('id', '')
        try:
            lesson = models.SyllabusGradeLesson.objects.get(id=id)
        except Exception:
            return create_failure_dict(msg='错误的课程信息')

        # if lesson.syllabus_grade.in_use:
        #    return create_failure_dict(msg='已启用的年级不能删除课程')

        # 处理该课程下的大纲
        contents = lesson.syllabusgradelessoncontent_set.all()
        for content in contents:
            # 大纲对应的登录记录
            content.teacherloginloglessoncontent_set.all().delete()
            # 大纲本身
            content.delete()

        # 处理课程
        lesson.delete()

        return create_success_dict(msg='课程删除成功')


def courseware_list(request):
    pk = request.GET.get('id')
    teacherloginlog_uuids = models.TeacherLoginLogLessonContent.objects.filter(lessoncontent=pk).values_list('teacherloginlog', flat=True)
    q = models.TeacherLoginLogCourseWare.objects.filter(teacherloginlog__in=teacherloginlog_uuids)
    q = q.values('courseware__title', 'courseware__qiniu_url').distinct()

    return create_success_dict(data={'records': model_list_to_dict(q)})


def remote_get(request):
    '''
        远程获取大纲内容
        1.保存 syllabusgradelesson内容;
        2.保存 syllabusgradelessoncontent内容;
    '''
    term_uuid = request.POST.get('term_uuid', u'')
    publish = request.POST.get('publish', u'')
    grade_name = request.POST.get('syllabus_grade', u'')
    lesson_name = request.POST.get('lesson_name', u'')
    bookversion = request.POST.get('date', u'')
    #remark = request.POST.get('remark', u'')
    #cover_pic = request.POST.get('cover_pic', u'')
    #version_pic = request.POST.get('version_pic', u'')

    # 1. 保存 syllabusgrade 内容 , 已存在的年级直接读取
    try:
        t = models.NewTerm.objects.get(uuid=term_uuid)
    except:
        return create_failure_dict(msg='错误的学年学期')

    grade = models.SyllabusGrade.objects.get(school_year=t.school_year, term_type=t.term_type, grade_name=grade_name)

    # 2. 保存 syllabusgradelessoncontent内容
    year, month, number = bookversion.split('-')
    # 调用远程接口来获取大纲内容并保存
    url = '%s/view/api/syllabus/list-by-bookversion/' % (constants.RESOURCE_PLATFORM_HOST)

    data = {
        'lessonname': lesson_name,
        #'volume': u'上册' if t.term_type == u'秋季学期' else u'下册',
        'school_year': t.school_year,
        'term_type': t.term_type,
        'grade_name': grade_name,
        'publish': publish,
        'year': year,
        'month': month,
        'number': number
    }
    try:
        ret = requests.get(url, params=data, timeout=120)
        ret = ret.json()
        data = ret.get('data', None)

        if data:
            remark = data.get('remark', '')
            cover_pic = data.get('cover_pic', '')
            version_pic = data.get('version_pic', '')
            volume = data.get('volume', '')
            records = data.get('records', [])

            # 2.1 保存 syllabusgradelesson 内容 , 已存在的课程直接读取
            lesson, c = models.SyllabusGradeLesson.objects.get_or_create(syllabus_grade=grade, lesson_name=lesson_name, publish=publish, bookversion=bookversion, defaults={
                                                                         'remark': remark, 'picture_host': cover_pic, 'picture_url': version_pic, 'edition': publish})

            if not c:
                return create_failure_dict(msg='不能添加重复课程')

            if lesson.in_use:
                return create_failure_dict(msg='已启用的课程不能拉取教材大纲数据')

            # 根据资源平台传递过来的大纲册来回写班班通该字段
            if volume:
                lesson.volume = volume
                lesson.save()

            # 先删除原来的
            lesson.syllabusgradelessoncontent_set.all().delete()

            # 先处理一下拉取过来的大纲数据，它们有父子关系
            parent_dict = {}
            for record in records:
                id = record['id']
                title = record['title']
                seq = record['seq']
                subseq = record['subseq']
                parent = record['parent']
                # 保存父
                if not parent:
                    obj = models.SyllabusGradeLessonContent.objects.create(syllabus_grade_lesson=lesson, title=title, seq=seq, subseq=subseq)
                    parent_dict[id] = obj

            for record in records:
                title = record['title']
                seq = record['seq']
                subseq = record['subseq']
                parent = record['parent']
                # 保存子
                if parent:
                    parent = parent_dict[parent]
                    models.SyllabusGradeLessonContent.objects.create(syllabus_grade_lesson=lesson, title=title, parent=parent, seq=seq, subseq=subseq)

            return create_success_dict(data={'records': model_to_dict(lesson)})

        return create_failure_dict(msg='无合适课程教学大纲拉取')
    except Exception:
        traceback.print_exc()
        return create_failure_dict(msg='课程教学大纲拉取失败')
