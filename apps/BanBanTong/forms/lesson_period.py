# coding=utf-8
import logging
import os
from django import forms
from django.forms.models import formset_factory
from BanBanTong.db import models
import xlrd
from BanBanTong.utils.datetimeutil import excel_cell_to_time


logger = logging.getLogger(__name__)


class LessonPeriodForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(LessonPeriodForm, self).__init__(*args, **kwargs)
        term = models.Term.get_current_term_list()
        if len(term) != 0:
            term = term[0]
        else:
            term = None
        self.term = term

    def clean_sequence(self):
        data = self.cleaned_data['sequence']
        if self.instance._state.adding:
            if models.LessonPeriod.objects.filter(sequence=data,
                                                  term=self.term).exists():
                raise forms.ValidationError(u'序号(%(seq)d)重复！',
                                            params={'seq': data})
        return data

    def clean_start_time(self):
        # 开始时间不能落于其他节次的时间段内
        data = self.cleaned_data['start_time']
        q = models.LessonPeriod.objects.filter(term=self.term,
                                               start_time__lte=data,
                                               end_time__gte=data)
        if not self.instance._state.adding:
            q = q.exclude(uuid=self.instance.uuid)
        if q.exists():
            raise forms.ValidationError(u'开始时间(%(start)s)与已有时段重叠！',
                                        params={'start': str(data)})
        return data

    def clean_end_time(self):
        # 结束时间不能落于其他节次的时间段内
        data = self.cleaned_data['end_time']
        q = models.LessonPeriod.objects.filter(term=self.term,
                                               start_time__lte=data,
                                               end_time__gte=data)
        if not self.instance._state.adding:
            q = q.exclude(uuid=self.instance.uuid)
        if q.exists():
            raise forms.ValidationError(u'结束时间(%(end)s)与已有时段重叠！',
                                        params={'end': str(data)})
        return data

    def clean(self):
        cleaned_data = super(LessonPeriodForm, self).clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if str(start_time) and str(end_time) and start_time is not None and end_time is not None:
            # 00:00:00 and 00:00:00 为False
            if start_time >= end_time:
                raise forms.ValidationError(u'开始时间(%(start)s)必须早于结束时间(%(end)s)！',
                                            params={'start': str(start_time),
                                                    'end': str(end_time)})
            q = models.LessonPeriod.objects.all()

            # if self.instance._state.adding: create: True  edit: False
            if self.instance.pk:
                q = q.exclude(pk=self.instance.pk)

            a = q.filter(term=self.term,
                         start_time__lte=start_time,
                         end_time__gte=end_time)

            if a.exists():
                raise forms.ValidationError(u'作息时间在其它作息时段内！')

            a = q.filter(term=self.term,
                         start_time__gte=start_time,
                         end_time__lte=end_time)

            if a.exists():
                raise forms.ValidationError(u'作息时间包含了其它作息时段！')

        return cleaned_data

    class Meta:
        model = models.LessonPeriod
        exclude = ['uuid', 'term']


LessonPeriodFormSet = formset_factory(LessonPeriodForm)


class LessonPeriodUploadForm(forms.Form):
    excel = forms.FileField()
    _valid_extensions = ['.xls', '.xlsx']
    _fields = ['sequence', 'start_time', 'end_time']
    head = [u'节次', u'开始时间', u'结束时间']

    def __init__(self, *args, **kwargs):
        super(LessonPeriodUploadForm, self).__init__(*args, **kwargs)
        self.fields['excel'].error_messages = {
            'required': u'请上传学校作息时间的xls文件！'
        }

    def clean(self):
        cleaned_data = super(LessonPeriodUploadForm, self).clean()
        excel = cleaned_data.get('excel')
        if excel:
            ext = os.path.splitext(excel.name)[1]
            if ext not in self._valid_extensions:
                self._errors['excel'] = u'您上传的文档类型错误，请重新上传！'
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
                    logger.info('LessonPeriod import excel head not match!')
                    self._errors['excel'] = u'所导入的文件与该信息表格模板格式不相符！'
                    del cleaned_data['excel']
                else:
                    self.sheet = sheet
                    self.datemode = xls.datemode
        return cleaned_data

    def save(self, commit=True):
        ret = []
        try:
            term = models.Term.get_current_term_list()[0]
        except:
            return ret
        for l in parse_xls(self.sheet, self.datemode):
            f = LessonPeriodForm(l)
            if f.is_valid():
                obj = f.save(commit=False)
                obj.term = term
                obj.save()
                ret.append(obj)
            else:
                logger.info('LessonPeriod excel: invalid %s', str(l))
                logger.info(str(f.errors))
        return ret

    def verify(self):
        ret = []
        for l in parse_xls(self.sheet, self.datemode):
            form = LessonPeriodForm(l)
            if not form.is_valid():
                ret.append({'row': l['row'], 'error': form.errors.as_text()})
        return ret


def parse_xls(sheet, datemode):
    ret = []
    for i in xrange(1, sheet.nrows):
        try:
            row = sheet.row_values(i)
            if len(row) < 3:
                logger.info('LessonPeriod excel: skip short row %s', i + 1)
                continue
            start_time = excel_cell_to_time(row[1], datemode)
            end_time = excel_cell_to_time(row[2], datemode)
            lesson_period = {
                'row': i + 1,
                'sequence': int(row[0]),
                'start_time': start_time,
                'end_time': end_time,
            }
            ret.append(lesson_period)
        except:
            logger.exception('')
            logger.info('LessonPeriod excel: skip %s %s', str(i + 1), str(row))
            continue
    return ret
