#!/usr/bin/env python
# coding=utf-8
import csv
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
        预先生成导出文件：统计分析->班班通授课次数统计
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

    def teaching_time_query(self, cache_key):
        '''根据查询条件进行过滤。分为两种情况：
        1. 按学年学期查询，过滤出对应的LessonTeacher，实际授课记录也从LessonTeacher计算。
        2. 按自然日期查询，首先找出该自然日期对应的Term->LessonTeacher，总计划授课次数从
        LessonTeacher计算，实际授课次数从该自然日期范围内的TeacherLoginLog计算。
        '''
        school_year = self.term.school_year
        term_type = self.term.term_type

        # LessonTeacher: 街道乡镇，学校，年级，班级，计划授课次数
        # 实际授课次数从LessonTeacher或TeacherLoginLog计算
        q = models.LessonTeacher.objects.filter(teacher__deleted=False)
        if school_year:
            # 按学年学期查询
            q = q.filter(class_uuid__grade__term__school_year=school_year)
        if term_type:
            q = q.filter(class_uuid__grade__term__term_type=term_type)
            term = models.Term.objects.filter(school_year=school_year,
                                              term_type=term_type)
            if term.exists():
                term = term[0]

        if cache_key == 'teaching-time-by-lessonteacher':  # 按老师课程的计划总数用原G表中的schedule_time
            total_schedule = q.aggregate(total=Sum('schedule_time'))['total']
        else:
            #按已排课的班级来计算, classes表示从G表查询之后的排课班级UUID集合
            classes = q.values_list('class_uuid', flat=True).distinct()
            total_schedule = models.Class.objects.filter(uuid__in=classes).aggregate(total=Sum('grade__term__schedule_time'))['total']
        if total_schedule is None:
            total_schedule = 0
        total_finish = q.aggregate(total=Sum('finished_time'))['total']
        if total_finish is None:
            total_finish = 0

        return q, total_schedule, total_finish

    def _export(self, cache_key, query_fields, excel_header, dict_keys, format_func):
        start_date = None
        end_date = None
        school_year = self.term.school_year
        term_type = self.term.term_type

        q, total_schedule, total_finish = self.teaching_time_query(cache_key)
        q = q.values(*query_fields)
        q = q.annotate(group_finished=Sum('finished_time'))
        if format_func == format_record.teaching_time:
            q = format_func(q, start_date, end_date)
        else:
            q = format_func(q, start_date, end_date,
                            school_year, term_type)

        try:
            export_type = constants.BANBANTONG_DEFAULT_EXPORT_TYPE.upper()
            if export_type not in ['XLS', 'CSV']:
                export_type = 'XLS'
        except:
            export_type = 'XLS'
        filename = '%s-%s-%s.%s' % (school_year, term_type, cache_key,
                                    export_type.lower())
        tmp_file = os.path.join(constants.CACHE_TMP_ROOT, 'export', filename)

        if export_type == 'XLS':
            xls = xlwt.Workbook(encoding='utf8')
            sheet = xls.add_sheet(u'班班通授课次数统计')
            for i in range(len(excel_header)):
                sheet.write(0, i, excel_header[i])
            row = 1
            for record in q:
                for i in range(len(dict_keys)):
                    sheet.write(row, i, record[dict_keys[i]])
                try:
                    percent = record['finished_time'] * 100.0 / record['schedule_time']
                except:
                    percent = 0.0
                percent = '%0.2f%%' % percent
                sheet.write(row, len(dict_keys), percent)
                row += 1
            # sheet.write(row, len(dict_keys) - 3, '合计')
            # sheet.write(row, len(dict_keys) - 2, total_finish)
            # sheet.write(row, len(dict_keys) - 1, total_schedule)

            # 2014-12-25
            sheet.write(row, dict_keys.index('finished_time') - 1, '合计')
            sheet.write(row, dict_keys.index('finished_time'), total_finish)
            sheet.write(row, dict_keys.index('schedule_time'), total_schedule)

            try:
                total_percent = total_finish * 100.0 / total_schedule
            except:
                total_percent = 0.0
            total_percent = '%0.2f%%' % total_percent
            sheet.write(row, len(dict_keys), total_percent)
            xls.save(tmp_file)
        elif export_type == 'CSV':
            with open(filename, 'wb') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(excel_header)
                for record in q:
                    row_data = []
                    for i in range(len(dict_keys)):
                        row_data.append(unicode(record[dict_keys[i]]).encode('utf-8', 'ignore'))
                    try:
                        percent = record['finished_time'] * 100.0 / record['schedule_time']
                    except:
                        percent = 0.0
                    percent = '%0.2f%%' % percent
                    row_data.append(percent)
                    writer.writerow(row_data)
                try:
                    total_percent = total_finish * 100.0 / total_schedule
                except:
                    total_percent = 0.0
                total_percent = '%0.2f%%' % total_percent
                # 最后一行
                last_row = [''] * len(excel_header)
                last_row[-1] = total_percent
                last_row[-2] = total_schedule
                last_row[-3] = total_finish
                last_row[-4] = u'合计'.encode('utf-8', 'ignore')
                writer.writerow(last_row)

    def by_class_export(self):
        cache_key = 'teaching-time-by-class'
        query_fields = ('class_uuid__grade__term__school__parent__name',
                        'class_uuid__grade__term__school__name',
                        'class_uuid__grade__name',
                        'class_uuid__name',
                        'class_uuid__grade__term__schedule_time')
        excel_header = ['街道乡镇', '学校', '年级', '班级',
                        '实际授课总数', '计划达标授课总数（学期）', '授课达标占比（%）']
        dict_keys = ('town_name', 'school_name', 'grade_name', 'class_name',
                     'finished_time', 'schedule_time')
        ret = self._export(cache_key, query_fields, excel_header, dict_keys,
                           format_record.teaching_time)
        return ret

    def by_country_export(self):
        cache_key = 'teaching-time-by-country'
        fields = ('class_uuid__grade__term__school__parent__parent__name',
                  'class_uuid__grade__term__schedule_time')
        excel_header = ['区县市', '班级总数', '班级平均授课数',
                        '实际授课总数', '计划达标授课数/班级', '计划达标授课总数（学期）', '授课达标占比（%）']
        dict_keys = ('country_name', 'class_total', 'class_average',
                     'finished_time', 'class_schedule_time', 'schedule_time')
        ret = self._export(cache_key, fields, excel_header, dict_keys,
                           format_record.teaching_time_class_total)
        return ret

    def by_grade_export(self):
        cache_key = 'teaching-time-by-grade'
        query_fields = ('class_uuid__grade__term__school__parent__name',
                        'class_uuid__grade__term__school__name',
                        'class_uuid__grade__name',
                        'class_uuid__grade__term__schedule_time')
        excel_header = ['街道乡镇', '学校', '年级', '班级总数', '班级平均授课数',
                        '实际授课总数', '计划达标授课数/班级', '计划达标授课总数（学期）', '授课达标占比（%）']
        dict_keys = ('town_name', 'school_name', 'grade_name', 'class_total',
                     'class_average',
                     'finished_time', 'class_schedule_time', 'schedule_time')
        ret = self._export(cache_key, query_fields, excel_header, dict_keys,
                           format_record.teaching_time_class_total)
        return ret

    def by_lessonteacher_export(self):
        cache_key = 'teaching-time-by-lessonteacher'
        query_fields = ('class_uuid__grade__term__school__parent__name',  # 乡镇town
                        'class_uuid__grade__term__school__name',
                        'class_uuid__grade__name',
                        'class_uuid__name',
                        'teacher__name',
                        'lesson_name__name',
                        'schedule_time')
        excel_header = ['街道乡镇', '学校', '年级', '班级', '教师', '课程',
                        '实际授课总数', '计划达标授课总数（学期）', '授课达标占比（%）']
        dict_keys = ('town_name', 'school_name', 'grade_name', 'class_name',
                     'teacher_name', 'lesson_name',
                     'finished_time', 'schedule_time')
        ret = self._export(cache_key, query_fields, excel_header, dict_keys,
                           format_record.teaching_time)
        return ret

    def by_school_export(self):
        cache_key = 'teaching-time-by-school'
        fields = (
            #'class_uuid__grade__term__school__parent__parent__name',
            'class_uuid__grade__term__school__parent__name',
            'class_uuid__grade__term__school__name',
            'class_uuid__grade__term__schedule_time')
        excel_header = [
            #'区县市',
            '街道乡镇', '学校', '班级总数', '班级平均授课数',
            '实际授课总数', '计划达标授课数/班级', '计划达标授课总数（学期）', '授课达标占比（%）']
        dict_keys = (
            #'country_name',
            'town_name', 'school_name', 'class_total',
            'class_average',
            'finished_time', 'class_schedule_time', 'schedule_time')
        ret = self._export(cache_key, fields, excel_header, dict_keys,
                           format_record.teaching_time_class_total)
        return ret

    def by_town_export(self):
        cache_key = 'teaching-time-by-town'
        query_fields = (
            #'class_uuid__grade__term__school__parent__parent__name',
            'class_uuid__grade__term__school__parent__name',
            'class_uuid__grade__term__schedule_time')
        excel_header = [
            #'区县市',
            '街道乡镇', '班级总数', '班级平均授课数',
            '实际授课总数', '计划达标授课数/班级', '计划达标授课总数（学期）', '授课达标占比（%）']
        dict_keys = (
            #'country_name',
            'town_name', 'class_total', 'class_average',
            'finished_time', 'class_schedule_time', 'schedule_time')
        ret = self._export(cache_key, query_fields, excel_header, dict_keys,
                           format_record.teaching_time_class_total)
        return ret
