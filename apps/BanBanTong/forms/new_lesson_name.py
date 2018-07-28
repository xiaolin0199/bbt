# coding=utf-8
import logging
import os
from django import forms
from django.db import IntegrityError
from django.forms.models import formset_factory
from BanBanTong.db import models
import xlrd


logger = logging.getLogger(__name__)


class NewLessonNameForm(forms.ModelForm):

    def save(self, obj=None, commit=True):
        name = self.cleaned_data['name']
        if obj:
            #obj = models.NewLessonName.objects.get(name=name, deleted=True)
            #obj.deleted = False
            # obj.save()
            obj.name = name
            obj.save()
        else:
            try:
                obj = models.NewLessonName.objects.get(name=name)
                obj.deleted = False
                obj.save()
                #
                models.NewLessonNameType.objects.filter(newlessonname=obj).delete()
            except Exception:
                country = models.Group.objects.get(group_type='country')
                obj = models.NewLessonName.objects.create(country=country, name=name)

        return obj

    class Meta:
        model = models.NewLessonName
        #exclude = ['uuid', 'school', 'deleted']
        exclude = ['uuid', 'deleted', 'lesson_type', 'country']


NewLessonNameFormSet = formset_factory(NewLessonNameForm)


class NewLessonNameUploadForm(forms.Form):
    excel = forms.FileField()
    _valid_extensions = ['.xls', '.xlsx']
    head = [u'学校开课课程']

    def __init__(self, *args, **kwargs):
        super(NewLessonNameUploadForm, self).__init__(*args, **kwargs)
        self.fields['excel'].error_messages = {
            'required': '请上传学校开课课程管理的xls文件！'
        }

    def clean(self):
        cleaned_data = super(NewLessonNameUploadForm, self).clean()
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
                    logger.debug('NewLessonName import excel head not match!')
                    self._errors['excel'] = u'所导入的文件与该信息表格模板格式不相符！'
                    del cleaned_data['excel']
                else:
                    self.sheet = sheet

        return cleaned_data

    def save(self, commit=True):
        ret = []
        for l in parse_xls(self.sheet):
            form = NewLessonNameForm(l)
            if form.is_valid():
                try:
                    obj = form.save()
                    ret.append(obj)
                except IntegrityError:
                    logger.info('NewLessonName excel: duplicate %s', str(l))
                    continue
            else:
                logger.info('NewLessonName excel: invalid %s', str(l))
                logger.info(str(form.errors))
        return ret


class NewLessonNameUploadVerifyForm(forms.Form):
    excel = forms.FileField()
    _valid_extensions = ['.xls', '.xlsx']
    head = [u'学校开课课程']

    def __init__(self, *args, **kwargs):
        super(NewLessonNameUploadVerifyForm, self).__init__(*args, **kwargs)
        self.fields['excel'].error_messages = {
            'required': '请上传学校开课课程管理的xls文件！'
        }

    def clean(self):
        cleaned_data = super(NewLessonNameUploadVerifyForm, self).clean()
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
            form = NewLessonNameForm(l)
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
            logger.info('NewLessonName excel: exception %s', str(i + 1), str(row))
    return ret
