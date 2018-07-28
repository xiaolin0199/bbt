# coding=utf-8
import os
import traceback
import logging
from django import forms
from django.forms.models import formset_factory
from BanBanTong.db import models
import xlrd
from BanBanTong.utils.datetimeutil import excel_float_to_date

logger = logging.getLogger(__name__)


class TermForm(forms.ModelForm):

    def clean_school_year(self):
        # 2014-2015
        data = self.cleaned_data['school_year']
        if len(data) != 9:
            raise forms.ValidationError(u'学年字符串长度错误(%(len)d)！',
                                        params={'len': len(data)})
        if data[4] != '-':
            raise forms.ValidationError(u'学年字符串分隔符错误(%(sep)s)！',
                                        params={'sep': data[4]})
        start_year = data[:4]
        end_year = data[5:]
        try:
            start_year = int(start_year)
        except:
            raise forms.ValidationError(u'开始学年不能转成数值(%(value)s)！',
                                        params={'value': start_year})
        try:
            end_year = int(end_year)
        except:
            raise forms.ValidationError(u'结束学年不能转成数值(%(value)s)！',
                                        params={'value': end_year})
        if end_year - start_year != 1:
            raise forms.ValidationError(u'开始学年(%(s)d)与结束学年(%(e)d)相差超过一年！',
                                        params={'s': start_year, 'e': end_year})
        q = models.Term.objects.filter(school_year=data).exclude(deleted=True)
        if self.instance._state.adding:
            if q.count() >= 2:
                raise forms.ValidationError(u'学年(%(val)s)已有两个学期！',
                                            params={'val': data})
        return data

    def clean_start_date(self):
        data = self.cleaned_data['start_date']
        # 开始时间不能在其他学期范围内
        if not self.instance._state.adding:
            return data
        q = models.Term.objects.filter(start_date__lte=data,
                                       end_date__gte=data)
        q = q.exclude(deleted=True)
        if q.exists():
            raise forms.ValidationError(u'开始时间(%(v)s)在其他学期时间范围内！',
                                        params={'v': str(data)})
        return data

    def clean_end_date(self):
        data = self.cleaned_data['end_date']
        # 结束时间不能在其他学期范围内
        q = models.Term.objects.filter(start_date__lte=data,
                                       end_date__gte=data)
        q = q.exclude(deleted=True)
        if not self.instance._state.adding:
            q = q.exclude(uuid=self.instance.uuid)
        if q.exists():
            raise forms.ValidationError(u'结束时间(%(v)s)在其他学期时间范围内！',
                                        params={'v': str(data)})
        return data

    def clean(self):
        cleaned_data = super(TermForm, self).clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        school_year = cleaned_data.get('school_year')
        term_type = cleaned_data.get('term_type')

        if start_date and end_date:
            if start_date >= end_date:
                raise forms.ValidationError(u'学期开始时间(%(s)s)必须早于结束时间(%(e)s)！',
                                            params={'s': str(start_date),
                                                    'e': str(end_date)})
            q = models.Term.objects.filter(start_date__gte=start_date,
                                           end_date__lte=end_date)
            q = q.exclude(deleted=True)
            if not self.instance._state.adding:
                q = q.exclude(uuid=self.instance.uuid)
            if q.exists():
                raise forms.ValidationError(u'学期时段包含了其它学期！')
        if not self.instance._state.adding:
            del cleaned_data['school_year']
            del cleaned_data['term_type']
            del cleaned_data['start_date']
            return cleaned_data
        if school_year and term_type:
            q = models.Term.objects.filter(school_year=school_year,
                                           term_type=term_type)
            q = q.exclude(deleted=True)
            if q.exists():
                raise forms.ValidationError(u'学年(%(y)s)学期(%(t)s)已存在！',
                                            params={'y': school_year,
                                                    't': term_type})

        return cleaned_data

    class Meta:
        model = models.Term
        exclude = ['uuid', 'school']


TermFormSet = formset_factory(TermForm)


class TermUploadForm(forms.Form):
    excel = forms.FileField()
    _valid_extensions = ['.xls', '.xlsx']
    _fields = ['start_year', 'end_year',
               'autumn_term_start_date', 'autumn_term_end_date',
               'spring_term_start_date', 'spring_term_end_date']
    head = [u'开始学年', u'结束学年', u'秋季学期开始时间', u'秋季学期结束时间',
            u'春季学期开始时间', u'春季学期结束时间']

    def __init__(self, *args, **kwargs):
        super(TermUploadForm, self).__init__(*args, **kwargs)
        self.fields['excel'].error_messages = {
            'required': '请上传学年学期的xls文件！'
        }

    def clean(self):
        cleaned_data = super(TermUploadForm, self).clean()
        excel = cleaned_data.get('excel')
        if excel:
            ext = os.path.splitext(excel.name)[1]
            if ext not in self._valid_extensions:
                err = self.error_class([u'您上传的文档类型错误，请重新上传！'])
                self._errors['excel'] = err
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
                    self.sheet = sheet
        return cleaned_data

    def save(self, commit=True):
        ret = []
        school = models.Group.objects.get(group_type='school')
        for l in parse_xls(self.sheet):
            form = TermForm(l)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.school = school
                obj.save()
                ret.append(obj)
            else:
                logger.debug('Term excel: invalid=%s, err=%s', l, form.errors)
        return ret

    def verify(self):
        ret = []
        for l in parse_xls(self.sheet):
            form = TermForm(l)
            if not form.is_valid():
                ret.append({'row': l['row'], 'error': form.errors.as_text()})
        return ret


def parse_xls(sheet):
    ret = []
    for i in xrange(1, sheet.nrows):
        try:
            term = []
            row = sheet.row_values(i)
            if len(row) < 4:
                continue
            if not isinstance(row[0], int):
                if row[0] == '':
                    continue
                row[0] = int(row[0])
            if not isinstance(row[1], int):
                row[1] = int(row[1])
            if not isinstance(row[2], int):
                if row[2]:
                    row[2] = int(row[2])
            if not isinstance(row[3], int):
                if row[3]:
                    row[3] = int(row[3])
            if not isinstance(row[4], int):
                if row[4]:
                    row[4] = int(row[4])
            if not isinstance(row[5], int):
                if row[5]:
                    row[5] = int(row[5])
            if row[2] and row[3]:
                term.append({
                    'row': i + 1,
                    'school_year': '%d-%d' % (row[0], row[1]),
                    'term_type': u'秋季学期',
                    'start_date': excel_float_to_date(row[2]),
                    'end_date': excel_float_to_date(row[3])
                })
            if row[4] and row[5]:
                term.append({
                    'row': i + 1,
                    'school_year': '%d-%d' % (row[0], row[1]),
                    'term_type': u'春季学期',
                    'start_date': excel_float_to_date(row[4]),
                    'end_date': excel_float_to_date(row[5])
                })
            ret.extend(term)
        except:
            traceback.print_exc()
    return ret
