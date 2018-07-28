#!/usr/bin/env python
# coding=utf-8
import datetime
import logging
import os
from django.db.models import Sum
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.utils import format_record
import xlwt


class Task(object):
    '''
        预先生成导出文件：统计分析->班班通授课时长统计
    '''
    run_period = 60 * 60 * 3
    logger = logging.getLogger(__name__)

    def __init__(self):
        if models.Setting.getvalue('server_type') != 'country':
            return
        try:
            self.term = self.get_current_term()
            if not self.term:
                return
            self.by_class_export()
            self.by_grade_export()
            self.by_lessonteacher_export()
            self.by_school_export()
            self.by_teacher_export()
            self.by_town_export()
        except:
            self.logger.exception('')

    def get_current_term(self):
        today = datetime.date.today()
        q = models.NewTerm.objects.filter(start_date__lte=today, end_date__gte=today)
        if q.count() == 0:
            q = models.NewTerm.objects.filter(start_date__gte=today)
        try:
            return q[0]
        except:
            return

    def _new_query(self):
        school_year = self.term.school_year
        term_type = self.term.term_type

        q = models.LessonTeacher.objects.filter(teacher__deleted=False)
        l = models.TeacherLoginTimeCache.objects.all()
        if school_year:
            # 按学年学期查询
            q = q.filter(class_uuid__grade__term__school_year=school_year)
            l = l.filter(class_uuid__grade__term__school_year=school_year)
        if term_type:
            q = q.filter(class_uuid__grade__term__term_type=term_type)
            l = l.filter(class_uuid__grade__term__term_type=term_type)
            term = models.Term.objects.filter(school_year=school_year,
                                              term_type=term_type)
            if term.exists():
                term = term[0]

        # 总授课时长
        total_time_used = q.aggregate(total=Sum('login_time'))['total']
        if total_time_used is None:
            total_time_used = 0
        return q, total_time_used

    def _new_export(self, cache_key, fields, excel_header, dict_keys):
        q, total_time_used = self._new_query()
        q = q.values(*fields)
        q = q.annotate(lesson_count=Sum('finished_time'), total_time_used=Sum('login_time'))

        xls = xlwt.Workbook(encoding='utf8')
        title = u'班班通授课时长统计'
        sheet = xls.add_sheet(title)
        for i in range(len(excel_header)):
            sheet.write(0, i, excel_header[i])
        row = 1
        l = format_record.new_time_used(q, cache_key, None, None,
                                        self.term.school_year,
                                        self.term. term_type)
        for record in l:
            for i in range(len(dict_keys) - 1):
                sheet.write(row, i, record[dict_keys[i]])
            try:
                avg = u'%s分钟' % (record['total_time_used'] / record['lesson_count'] / 60)
            except:
                avg = u'0分钟'

            sheet.write(row, len(dict_keys) - 1, avg)
            sheet.write(row, len(dict_keys), u'%s分钟' % (record[dict_keys[len(dict_keys) - 1]] / 60))
            row += 1
        sheet.write(row, len(dict_keys) - 1, '合计')
        sheet.write(row, len(dict_keys), total_time_used / 60)

        filename = '%s-%s-%s.xls' % (self.term.school_year,
                                     self.term.term_type, cache_key)
        tmp_file = os.path.join(constants.CACHE_TMP_ROOT, 'export', filename)
        xls.save(tmp_file)

    def by_grade_export(self):
        cache_key = 'time-used-by-grade'
        fields = ('class_uuid__grade__term__school__parent__name',  # 乡镇towm
                  'class_uuid__grade__term__school__name',
                  'class_uuid__grade__name',)
        excel_header = ['街道乡镇', '学校', '年级', '班级总数',
                        '授课节次总数', '平均时长/节次', '总授课时长']
        dict_keys = ('town_name', 'school_name', 'grade_name',
                     'class_count', 'lesson_count', 'total_time_used')
        ret = self._new_export(cache_key, fields, excel_header, dict_keys)
        return ret

    def by_class_export(self):
        cache_key = 'time-used-by-class'
        fields = ('class_uuid__grade__term__school__parent__name',  # 乡镇towm
                  'class_uuid__grade__term__school__name',
                  'class_uuid__grade__name',
                  'class_uuid__name',)
        excel_header = ['街道乡镇', '学校', '年级', '班级',
                        '授课节次总数', '平均时长/节次', '总授课时长']
        dict_keys = ('town_name', 'school_name', 'grade_name', 'class_name',
                     'lesson_count', 'total_time_used')
        ret = self._new_export(cache_key, fields, excel_header, dict_keys)
        return ret

    def by_teacher_export(self):
        cache_key = 'time-used-by-teacher'
        fields = ('class_uuid__grade__term__school__parent__name',  # 乡镇towm
                  'class_uuid__grade__term__school__name',
                  'teacher__name',)
        excel_header = ['街道乡镇', '学校', '老师',
                        '授课节次总数', '平均时长/节次', '总授课时长']
        dict_keys = ('town_name', 'school_name', 'teacher_name',
                     'lesson_count', 'total_time_used')
        ret = self._new_export(cache_key, fields, excel_header, dict_keys)
        return ret

    def by_lessonteacher_export(self):
        cache_key = 'time-used-by-lessonteacher'
        fields = ('class_uuid__grade__term__school__parent__name',  # 乡镇towm
                  'class_uuid__grade__term__school__name',
                  'class_uuid__grade__name',
                  'class_uuid__name',
                  'lesson_name__name',
                  'teacher__name',)
        excel_header = ['街道乡镇', '学校', '年级', '班级', '教师', '课程',
                        '授课节次总数', '平均时长/节次', '总授课时长']
        dict_keys = ('town_name', 'school_name', 'grade_name', 'class_name', 'teacher_name',
                     'lesson_name', 'lesson_count', 'total_time_used')
        ret = self._new_export(cache_key, fields, excel_header, dict_keys)
        return ret

    def by_school_export(self):
        cache_key = 'time-used-by-school'
        fields = ('class_uuid__grade__term__school__parent__name',  # 乡镇towm
                  'class_uuid__grade__term__school__name',)
        excel_header = ['街道乡镇', '学校', '班级总数',
                        '授课节次总数', '平均时长/节次', '总授课时长']
        dict_keys = ('town_name', 'school_name', 'class_count',
                     'lesson_count', 'total_time_used')
        ret = self._new_export(cache_key, fields, excel_header, dict_keys)
        return ret

    def by_town_export(self):
        cache_key = 'time-used-by-town'
        fields = ('class_uuid__grade__term__school__parent__name',)
        excel_header = ['街道乡镇', '班级总数', '授课节次总数',
                        '平均时长/节次', '总授课时长']
        dict_keys = ('town_name', 'class_count', 'lesson_count',
                     'total_time_used')
        ret = self._new_export(cache_key, fields, excel_header, dict_keys)
        return ret
