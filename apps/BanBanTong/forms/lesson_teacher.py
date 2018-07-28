# coding=utf-8
import logging
import os
import traceback
from django import forms
from BanBanTong.db import models
from BanBanTong.db.models import Class
from BanBanTong.db.models import Grade
from BanBanTong.db.models import LessonName
from BanBanTong.db.models import LessonTeacher
from BanBanTong.db.models import Teacher
from BanBanTong.db.models import Term
import xlrd
from BanBanTong.utils.datetimeutil import excel_cell_to_date
from BanBanTong.utils.datetimeutil import excel_float_to_date
from django.conf import settings
DEBUG = settings.DEBUG
del settings

logger = logging.getLogger(__name__)


class LessonTeacherForm(forms.ModelForm):
    grade_name = forms.CharField(max_length=20)
    class_name = forms.CharField(max_length=20)
    lesson_name = forms.CharField(max_length=20)
    teacher_name = forms.CharField(max_length=100, required=False)
    birthday = forms.DateField(required=False)

    def __init__(self, *args, **kwargs):
        super(LessonTeacherForm, self).__init__(*args, **kwargs)
        if not self.instance._state.adding:
            self.fields['grade_name'].required = False
            self.fields['class_name'].required = False
            self.fields['lesson_name'].required = False
            self.fields['teacher'].required = False

        if 'excel' in args:
            self.fields['teacher'].required = False
            self.fields['teacher_name'].required = True
            self.fields['birthday'].required = True
            self.from_excel = True
        else:
            self.from_excel = False

    def clean(self):
        cleaned_data = super(LessonTeacherForm, self).clean()
        if not self.instance._state.adding:
            cleaned_data['teacher'] = self.instance.teacher

            schedule_time = cleaned_data['schedule_time']
            if schedule_time >= 0:
                count = self.instance.teacherloginlog_set.count()
                if schedule_time < count:
                    # 如果是从excel导入的话,那么会判断分配课时和实际授课的大小
                    if self.from_excel:
                        cleaned_data['schedule_time'] = count
                    else:
                        msg = u'分配课时数小于实际上课数目(%s)' % count
                        self._errors['schedule_time'] = msg
                        del cleaned_data['schedule_time']
            return cleaned_data
        grade_name = cleaned_data['grade_name'].strip().replace(' ', '')
        class_name = cleaned_data['class_name'].strip().replace(' ', '')
        lesson_name = cleaned_data['lesson_name'].strip().replace(' ', '')
        teacher_name = cleaned_data['teacher_name'].strip().replace(' ', '')
        birthday = str(cleaned_data['birthday']).strip().replace(' ', '')
        schedule_time = cleaned_data['schedule_time']
        if grade_name and class_name:
            try:
                terms = Term.get_current_term_list()
                term = terms[0]
            except:
                if 'class_name' not in self._errors:
                    self._errors['class_name'] = '系统尚未配置当前学期！'
                else:
                    self._errors['class_name'].append('系统尚未配置当前学期！')
                del cleaned_data['class_name']
            try:
                self.class_uuid = Class.objects.get(grade__term=term,
                                                    grade__name=grade_name,
                                                    name=class_name)
            except:
                if DEBUG:
                    traceback.print_exc()
                self.class_uuid = None
                if 'class_name' not in self._errors:
                    self._errors['class_name'] = '错误的班级！'
                else:
                    self._errors['class_name'].append('错误的班级！')
                del cleaned_data['grade_name']
                del cleaned_data['class_name']
        if lesson_name:
            try:
                self.lesson_uuid = LessonName.objects.get(name=lesson_name,
                                                          deleted=False)
            except:
                self.lesson_uuid = None
                self._errors['lesson_name'] = '错误的课程名称！'
                del cleaned_data['lesson_name']
        if teacher_name and birthday:
            names = [
                teacher_name,
                '%s(%s)' % (teacher_name, cleaned_data['birthday'].strftime('%y%m%d'))
            ]
            try:
                teacher = Teacher.objects.get(
                    name__in=names,
                    birthday=birthday,
                    deleted=False,
                )
                cleaned_data['teacher'] = teacher
            except:
                self._errors['teacher_name'] = '找不到对应的教师！'
                self._errors['birthday'] = '找不到对应的教师！'
                self._errors['teacher'] = '找不到对应的教师！'
                del cleaned_data['teacher_name']
                del cleaned_data['birthday']
                del cleaned_data['teacher']
        if 'teacher' in cleaned_data and cleaned_data['teacher'] and \
                self.class_uuid and self.lesson_uuid and not self.from_excel:
            if self.instance._state.adding:
                q = LessonTeacher.objects.filter(class_uuid=self.class_uuid,
                                                 lesson_name=self.lesson_uuid)
                q = q.filter(teacher=cleaned_data['teacher'])
                if q.exists():
                    msg = '已有相同的年级班级-课程-教师姓名，无法重复添加！'
                    self._errors['teacher'] = msg
                    del cleaned_data['teacher']

        return cleaned_data

    def save(self, commit=True):
        schedule_time = self.cleaned_data['schedule_time']
        if self.instance._state.adding:
            teacher = self.cleaned_data['teacher']
            try:
                obj, is_new = LessonTeacher.objects.get_or_create(
                    class_uuid=self.class_uuid,
                    teacher=teacher,
                    lesson_name=self.lesson_uuid,
                    defaults={
                        'schedule_time': schedule_time
                    }
                )
                if not is_new and obj.schedule_time != schedule_time:
                    obj.schedule_time = schedule_time
                    obj.save()
                return obj
            except:
                logger.exception('')

        else:
            self.instance.schedule_time = schedule_time
            self.instance.save()
            return self.instance

    class Meta:
        model = LessonTeacher
        exclude = ['uuid', 'class_uuid', 'lesson_name', 'finished_time', 'login_time']


class LessonTeacherUploadForm(forms.Form):
    excel = forms.FileField()
    _valid_extensions = ['.xls', '.xlsx']
    _fields = ['teacher_name', 'birthday', 'grade_name', 'class_name',
               'lesson_name', 'schedule_time']
    head = [u'姓名', u'生日', u'授课年级', u'授课班级',
            u'授课课程', u'计划课时']

    def __init__(self, *args, **kwargs):
        super(LessonTeacherUploadForm, self).__init__(*args, **kwargs)
        self.fields['excel'].error_messages = {
            'required': '请上传班级课程授课老师的xls文件！'
        }

    def clean(self):
        cleaned_data = super(LessonTeacherUploadForm, self).clean()
        excel = cleaned_data.get('excel')
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
                    self._errors['excel'] = u'所导入的文件与该信息表格模板格式不一致！'
                    del cleaned_data['excel']
                elif cmp(self.head, sheet.row_values(0)[:len(self.head)]) != 0:
                    self._errors['excel'] = u'所导入的文件与该信息表格模板格式不相符！'
                    del cleaned_data['excel']
                else:
                    try:
                        current_term = models.Term.get_current_term_list()[0]
                    except Exception:
                        current_term = None

                    if not current_term:
                        self._errors['excel'] = u'学年学期已结束,不能导入,请添加新的学期'
                        del cleaned_data['excel']
                    else:
                        if current_term.allow_import_lesson():
                            self.sheet = sheet
                            self.datemode = xls.datemode
                        else:
                            self._errors['excel'] = u'该学年学期已过期,不能导入'
                            del cleaned_data['excel']
        return cleaned_data

    def save(self, commit=True):
        ret = []
        # 先对表中的不符规范的数据进行清理
        LessonTeacher.clean_bad_items()
        for item in parse_xls(self.sheet, self.datemode):
            form = LessonTeacherForm(item, 'excel')
            if form.is_valid():
                try:
                    obj = form.save()
                    obj.calculate_finished_time()
                    ret.append(obj)
                except:
                    logger.debug(str(item))
                    logger.exception('')
            else:
                logger.debug('LessonTeacher excel: invalid %s', str(item))
                logger.debug(str(form.errors))
                continue
        return ret


def parse_xls(sheet, datemode):
    ret = []
    for i in xrange(1, sheet.nrows):
        try:
            row = sheet.row_values(i)
            if len(row) < 6:
                continue
            if isinstance(row[1], (str, unicode)):
                birthday = float(str(row[1]).strip().replace(' ', ''))
            else:
                birthday = row[1]
            if not isinstance(birthday, float):
                logger.info('LessonTeacher excel: birthday not float %s', str(i + 1))
                continue
            grade_name = row[2]
            if isinstance(row[2], float):
                grade_name = str(int(row[2]))
            class_name = row[3]
            if isinstance(row[3], float):
                class_name = str(int(row[3]))
            lesson_teacher = {
                'row': i + 1,
                'grade_name': grade_name,
                'class_name': class_name,
                'teacher_name': row[0],
                'birthday': excel_float_to_date(birthday, datemode),
                'lesson_name': row[4].strip(),
                'schedule_time': int(row[5])
            }
            ret.append(lesson_teacher)
        except:
            logger.debug('LessonTeacher excel: exception %s %s', str(i + 1), str(row))
            logger.exception('')
            continue
    return ret


class LessonTeacherUploadVerifyForm(forms.Form):
    excel = forms.FileField()
    _valid_extensions = ['.xls', '.xlsx']
    head = [u'姓名', u'生日', u'授课年级', u'授课班级',
            u'授课课程', u'计划课时']

    def __init__(self, *args, **kwargs):
        super(LessonTeacherUploadVerifyForm, self).__init__(*args, **kwargs)
        self.fields['excel'].error_messages = {
            'required': '请上传班级课程授课老师的xls文件！'
        }

    def clean(self):
        cleaned_data = super(LessonTeacherUploadVerifyForm, self).clean()
        excel = cleaned_data.get('excel')
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
                self.sheet = sheet
                self.datemode = xls.datemode
        return cleaned_data

    def save(self):
        ret = []
        if len(self.sheet.row_values(0)) < len(self.head):
            ret.append({'row': 1, 'error': '所导入的文件与该信息表格模板格式不一致！'})
            return ret
        if cmp(self.head, self.sheet.row_values(0)[:len(self.head)]) != 0:
            ret.append({'row': 1, 'error': '所导入的文件与该信息表格模板格式不相符！'})
            return ret
        ret = verify_xls(self.sheet, self.datemode)
        return ret


def verify_xls(sheet, datemode):
    ret = []
    for i in xrange(1, sheet.nrows):
        row = sheet.row_values(i)
        if len(row) < 6:
            ret.append({'row': i + 1, 'error': u'不足6列，跳过'})
            continue
        if not isinstance(row[0], (str, unicode)):
            ret.append({'row': i + 1, 'error': u'姓名格式错误！'})
            continue
        if row[0] == u'':
            ret.append({'row': i + 1, 'error': u'姓名不能为空！'})
            continue
        if isinstance(row[1], (str, unicode)):
            try:
                birthday = float(row[1])
            except:
                ret.append({'row': i + 1, 'error': u'生日格式错误！'})
                continue
        else:
            birthday = row[1]
        birthday = excel_cell_to_date(birthday)
        if birthday is None:
            ret.append({'row': i + 1, 'error': u'生日有错误！'})
            continue
        if not Teacher.objects.filter(name=row[0], birthday=birthday).exists():
            ret.append({'row': i + 1, 'error': u'姓名生日对应的教师不存在！'})
            continue
        grade_name = row[2]
        if isinstance(row[2], float):
            grade_name = str(int(row[2]))
        if not isinstance(grade_name, (str, unicode)):
            ret.append({'row': i + 1, 'error': u'年级格式错误！'})
            continue
        if grade_name == u'':
            ret.append({'row': i + 1, 'error': u'年级不能为空！'})
            continue
        if not Grade.objects.filter(name=grade_name).exists():
            ret.append({'row': i + 1, 'error': u'年级不存在！'})
            continue
        class_name = row[3]
        if isinstance(row[3], float):
            class_name = str(int(row[3]))
        if not isinstance(class_name, (str, unicode)):
            ret.append({'row': i + 1, 'error': u'班级格式错误！'})
            continue
        if class_name == u'':
            ret.append({'row': i + 1, 'error': u'班级不能为空！'})
            continue
        if not Class.objects.filter(name=class_name).exists():
            ret.append({'row': i + 1, 'error': u'班级不存在！'})
            continue
        if not isinstance(row[4], (str, unicode)):
            ret.append({'row': i + 1, 'error': u'课程格式错误！'})
            continue
        if row[4] == u'':
            ret.append({'row': i + 1, 'error': u'课程不能为空！'})
            continue
        if not LessonName.objects.filter(name=row[4]).exists():
            ret.append({'row': i + 1, 'error': u'课程不存在！'})
            continue
        if not isinstance(row[5], float):
            try:
                schedule_time = int(row[5])
            except:
                ret.append({'row': i + 1, 'error': u'计划课时格式错误！'})
                continue
        else:
            schedule_time = int(row[5])
        if schedule_time <= 0:
            ret.append({'row': i + 1, 'error': u'计划课时(%d,%s)小于等于零，请确认！' % (schedule_time, row[5])})
            continue
    return ret
