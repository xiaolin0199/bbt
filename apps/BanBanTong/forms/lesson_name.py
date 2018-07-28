# coding=utf-8
import logging
import os
from django import forms
from django.db import IntegrityError
from django.forms.models import formset_factory
from BanBanTong.db import models
import xlrd


logger = logging.getLogger(__name__)


class LessonNameForm(forms.ModelForm):

    def save(self, commit=True):
        name = self.cleaned_data['name']
        try:
            obj = models.LessonName.objects.get(name=name, deleted=True)
            obj.deleted = False
            obj.save()
        except:
            school = models.Group.objects.get(group_type='school')
            obj = models.LessonName.objects.create(school=school, name=name)
        return obj

    class Meta:
        model = models.LessonName
        exclude = ['uuid', 'school', 'deleted']


LessonNameFormSet = formset_factory(LessonNameForm)


class LessonNameUploadForm(forms.Form):
    excel = forms.FileField()
    _valid_extensions = ['.xls', '.xlsx']
    head = [u'学校开课课程']

    def __init__(self, *args, **kwargs):
        super(LessonNameUploadForm, self).__init__(*args, **kwargs)
        self.fields['excel'].error_messages = {
            'required': '请上传学校开课课程管理的xls文件！'
        }

    def clean(self):
        cleaned_data = super(LessonNameUploadForm, self).clean()
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
                    logger.info('LessonName import excel head not match!')
                    self._errors['excel'] = u'所导入的文件与该信息表格模板格式不相符！'
                    del cleaned_data['excel']
                else:
                    self.sheet = sheet

        return cleaned_data

    def save(self, commit=True):
        ret = []
        for l in parse_xls(self.sheet):
            form = LessonNameForm(l)
            if form.is_valid():
                try:
                    obj = form.save()
                    ret.append(obj)
                except IntegrityError:
                    logger.info('LessonName excel: duplicate %s', str(l))
                    continue
            else:
                logger.info('LessonName excel: invalid %s', str(l))
                logger.info(str(form.errors))
        return ret


class LessonNameUploadVerifyForm(forms.Form):
    excel = forms.FileField()
    _valid_extensions = ['.xls', '.xlsx']
    head = [u'学校开课课程']

    def __init__(self, *args, **kwargs):
        super(LessonNameUploadVerifyForm, self).__init__(*args, **kwargs)
        self.fields['excel'].error_messages = {
            'required': '请上传学校开课课程管理的xls文件！'
        }

    def clean(self):
        cleaned_data = super(LessonNameUploadVerifyForm, self).clean()
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

        return cleaned_data

    def save(self, commit=True):
        ret = []
        if len(self.sheet.row_values(0)) < len(self.head):
            ret.append({'row': 1, 'error': '所导入的文件与该信息表格模板格式不一致！'})
            return ret
        elif cmp(self.head, self.sheet.row_values(0)[:len(self.head)]) != 0:
            ret.append({'row': 1, 'error': '所导入的文件与该信息表格模板格式不相符！'})
            return ret
        for l in parse_xls(self.sheet):
            form = LessonNameForm(l)
            if not form.is_valid():
                ret.append({'row': l['row'], 'error': str(form.errors)})
        return ret


def parse_xls(sheet):
    ret = []
    for i in xrange(1, sheet.nrows):
        try:
            row = sheet.row_values(i)
            if len(row) < 1:
                continue
            lesson_name = {
                'row': i + 1,
                'name': row[0].strip()
            }
            ret.append(lesson_name)
        except:
            logger.exception('')
            logger.info('LessonName excel: exception %s', str(i + 1), str(row))
    return ret
