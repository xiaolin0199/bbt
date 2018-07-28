# coding=utf-8
import logging
import os
from django import forms
from BanBanTong.db import models
import xlrd
from django.conf import settings
DEBUG = settings.DEBUG
del settings

logger = logging.getLogger(__name__)


class LessonScheduleForm(forms.ModelForm):
    lesson_period_sequence = forms.IntegerField()
    lesson_name = forms.CharField(max_length=20)

    def __init__(self, *args, **kwargs):
        super(LessonScheduleForm, self).__init__(*args, **kwargs)
        term = models.Term.get_current_term_list()
        if len(term) > 0:
            self.term = term[0]
        else:
            self.term = None
        if 'verify' in args:
            self.fields['class_uuid'].required = False

    def clean_lesson_name(self):
        data = self.cleaned_data['lesson_name']
        q = models.LessonName.objects.filter(school=self.term.school,
                                             name=data, deleted=False)
        if not q.exists():
            raise forms.ValidationError(u'课程(%(name)s)不存在！',
                                        params={'name': data})
        return data

    def clean_lesson_period_sequence(self):
        data = self.cleaned_data['lesson_period_sequence']
        q = models.LessonPeriod.objects.filter(term=self.term, sequence=data)
        if not q.exists():
            raise forms.ValidationError(u'节次(%(seq)d)不存在！',
                                        params={'seq': data})
        return data

    def save(self):
        class_uuid = self.cleaned_data['class_uuid']
        seq = self.cleaned_data['lesson_period_sequence']
        weekday = self.cleaned_data['weekday']
        lesson_name = self.cleaned_data['lesson_name']

        term = class_uuid.grade.term
        school = class_uuid.grade.term.school
        lesson_period = models.LessonPeriod.objects.get(term=term,
                                                        sequence=seq)
        lesson_name_obj = models.LessonName.objects.get(school=school,
                                                        name=lesson_name,
                                                        deleted=False)
        l = models.LessonSchedule.objects.create(class_uuid=class_uuid,
                                                 lesson_period=lesson_period,
                                                 weekday=weekday,
                                                 lesson_name=lesson_name_obj)
        return l

    class Meta:
        model = models.LessonSchedule
        exclude = ['uuid', 'lesson_period', 'lesson_name']


class LessonScheduleUploadForm(forms.Form):
    school_year = forms.CharField(max_length=20, required=False)
    term_type = forms.CharField(max_length=20, required=False)
    grade_name = forms.CharField(max_length=20)
    class_name = forms.CharField(max_length=20)
    excel = forms.FileField()
    _valid_extensions = ['.xls', '.xlsx']
    _fields = ['sequence', 'week1', 'week2', 'week3',
               'week4', 'week5', 'week6', 'week7']
    head = [u'节次', u'周一', u'周二', u'周三', u'周四',
            u'周五', u'周六', u'周日']

    def __init__(self, *args, **kwargs):
        super(LessonScheduleUploadForm, self).__init__(*args, **kwargs)
        self.fields['excel'].error_messages = {
            'required': '请上传班级课程表的xls文件！'
        }
        if 'verify' in args:
            self.fields['grade_name'].required = False
            self.fields['class_name'].required = False

    def clean(self):
        cleaned_data = super(LessonScheduleUploadForm, self).clean()
        excel = cleaned_data.get('excel')
        school_year = cleaned_data.get('school_year')
        term_type = cleaned_data.get('term_type')
        # grade_name = cleaned_data.get('grade_name')
        # class_name = cleaned_data.get('class_name')
        if excel:
            ext = os.path.splitext(excel.name)[1]
            if ext not in self._valid_extensions:
                self._errors['excel'] = '您上传的文档类型错误，请重新上传！'
                del cleaned_data['excel']
            else:
                data = ''
                for chunk in excel.chunks():
                    data += chunk
                xls = xlrd.open_workbook(file_contents=data)
                sheet = xls.sheet_by_index(0)
                if len(sheet.row_values(0)) < len(self.head):
                    self._errors['excel'] = '所导入的文件与该信息表格模板格式不一致！'
                    del cleaned_data['excel']
                elif cmp(self.head, sheet.row_values(0)[:len(self.head)]) != 0:
                    self._errors['excel'] = '所导入的文件与该信息表格模板格式不相符！'
                    del cleaned_data['excel']
                else:
                    if not school_year and not term_type:
                        self.sheet = sheet
                    else:
                        # 某学校.某学年.某学期 是否还可以导入课程信息
                        try:
                            term_obj = models.Term.objects.get(school_year=school_year, term_type=term_type)
                        except:
                            term_obj = None

                        if term_obj:
                            if not term_obj.allow_import_lesson():
                                self._errors['excel'] = '该学年学期已过期,不能导入课程'
                                del cleaned_data['excel']
                            else:
                                self.sheet = sheet
                        else:
                            self._errors['excel'] = '学年学期%s(%s)设置有误' % (school_year, term_type)
                            del cleaned_data['excel']

        return cleaned_data

    def save(self, commit=True):
        grade_name = self.cleaned_data['grade_name']
        class_name = self.cleaned_data['class_name']
        # 删除原数据进行全新导入
        q = models.LessonSchedule.objects.all()
        q = q.filter(class_uuid__name=class_name,
                     class_uuid__grade__name=grade_name)

        try:
            cls = q[0].class_uuid
            please = models.Statistic.objects.get(key=cls.pk)
        except models.Statistic.DoesNotExist:
            please = models.Statistic.create_one_item(cls.grade.term, cls)
        except:
            please = None
        q.delete()
        ret = []
        if please:
            please.leave_me_alone('lesson')

        for l in parse_xls(self.sheet, grade_name, class_name):
            form = LessonScheduleForm(l)
            if form.is_valid():
                obj = form.save()
                ret.append(obj)
            else:
                logger.info('LessonSchedule excel: invalid %s', str(l))
                continue
        return ret

    def verify(self):
        ret = []
        for l in parse_xls(self.sheet, '', '', verify=True):
            form = LessonScheduleForm(l, 'verify')
            if not form.is_valid():
                ret.append({'row': l['row'], 'error': form.errors.as_text()})
        return ret


def parse_xls(sheet, grade_name, class_name, verify=False):
    ret = []
    if not verify:
        terms = models.Term.get_current_term_list()
        q = models.Class.objects.filter(name=class_name,
                                        grade__name=grade_name,
                                        grade__term__in=terms)
        if not q.exists():
            return ret
        c = q[0]
    for i in xrange(1, sheet.nrows):
        try:
            row = sheet.row_values(i)
            if len(row) < 1:
                continue
            if row[0] == '':
                continue
            if not isinstance(row[0], int):
                sequence = int(row[0])
            else:
                sequence = row[0]
            for j in range(1, 8):
                if row[j] == '':
                    continue
                lesson_name = row[j]
                weekday = models.WEEK_KEYS[j - 1][0]
                lesson_schedule = {
                    'row': i + 1,
                    'column': j + 1,
                    'lesson_period_sequence': sequence,
                    'weekday': weekday,
                    'lesson_name': lesson_name
                }
                if not verify:
                    lesson_schedule['class_uuid'] = c.uuid
                ret.append(lesson_schedule)
        except Exception:
            logger.info('LessonSchedule excel: exception %s %s', str(i + 1), str(row))
            logger.exception('')
    return ret
