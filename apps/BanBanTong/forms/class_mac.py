# coding=utf-8
import logging
import os
from django import forms
from django.conf import settings
from django.forms.models import formset_factory
from django.utils.dateparse import parse_date
from BanBanTong.db import models
from BanBanTong.utils import str_util
import xlrd

from activation.decorator import get_none_activate


logger = logging.getLogger(__name__)


class BatchClassForm(forms.Form):
    grade_1 = forms.IntegerField(label=u'一年级', initial=0, required=False)
    grade_2 = forms.IntegerField(label=u'二年级', initial=0, required=False)
    grade_3 = forms.IntegerField(label=u'三年级', initial=0, required=False)
    grade_4 = forms.IntegerField(label=u'四年级', initial=0, required=False)
    grade_5 = forms.IntegerField(label=u'五年级', initial=0, required=False)
    grade_6 = forms.IntegerField(label=u'六年级', initial=0, required=False)
    grade_7 = forms.IntegerField(label=u'七年级', initial=0, required=False)
    grade_8 = forms.IntegerField(label=u'八年级', initial=0, required=False)
    grade_9 = forms.IntegerField(label=u'九年级', initial=0, required=False)
    grade_10 = forms.IntegerField(label=u'十年级', initial=0, required=False)
    grade_11 = forms.IntegerField(label=u'十一年级', initial=0, required=False)
    grade_12 = forms.IntegerField(label=u'十二年级', initial=0, required=False)

    def __init__(self, *args, **kwargs):
        super(BatchClassForm, self).__init__(*args, **kwargs)
        terms = models.Term.get_current_term_list()
        self.term = terms[0]
        self.activate_number = get_none_activate()

    def clean(self):
        '''
            仅在无任何班级的情况下才可能使用批量添加功能
        '''
        cleaned_data = super(BatchClassForm, self).clean()

        if models.Class.objects.filter(grade__term=self.term).exclude(grade__number=13).exists():
            raise forms.ValidationError(u'已存在班级数据，不能批量添加.')

        return cleaned_data

    def save(self):

        ret = []
        # 初始化十二个年级的班级数据
        for grade_name in [u'一', u'二', u'三', u'四', u'五', u'六', u'七', u'八', u'九', u'十', u'十一', u'十二']:
            grade_number = str_util.grade_name_to_number(grade_name)
            class_number = self.cleaned_data['grade_%s' % grade_number]
            if class_number:
                # 创建年级
                custom_grade_name = settings.CONF.server.grade_map.get(grade_name) or settings.CONF.server.grade_map.get(str(grade_name)) or grade_name
                logger.debug('custom_grade_name:%s', custom_grade_name)
                g, c = models.Grade.objects.get_or_create(name=custom_grade_name,
                                                          number=grade_number,
                                                          term=self.term)
                # 创建班级
                for number in range(1, class_number + 1):
                    if self.activate_number:
                        obj = models.Class.objects.create(
                            name=str(number),
                            number=number,
                            grade=g
                        )
                        ret.append(obj)

                        self.activate_number -= 1

        return ret


class ClassForm(forms.ModelForm):
    grade_name = forms.CharField(max_length=10)
    grade_number = forms.IntegerField(required=False)
    class_number = forms.IntegerField(required=False)
    name = forms.CharField(max_length=10)
    teacher_name = forms.CharField(max_length=20, required=False)
    birthday = forms.CharField(max_length=20, required=False)
    teacher_uuid = forms.CharField(max_length=40, required=False)

    def save(self):
        terms = models.Term.get_current_term_list()
        term = terms[0]

        grade_name = self.cleaned_data['grade_name']
        name = self.cleaned_data['name']
        teacher_name = self.cleaned_data['teacher_name']
        teacher_uuid = self.cleaned_data['teacher_uuid']
        birthday = self.cleaned_data['birthday']
        grade_number = self.cleaned_data.get('grade_number')
        class_number = self.cleaned_data.get('class_number')
        if not isinstance(grade_number, int):
            grade_number = str_util.grade_name_to_number(grade_name)
        grade_name_map = {k.decode('utf8'): v.decode('utf8') for k, v in settings.CONF.server.grade_map.items()}
        custom_grade_name = grade_name_map.get(grade_name) or grade_name
        g, c = models.Grade.objects.get_or_create(name=custom_grade_name, number=grade_number, term=term)
        if teacher_uuid:
            teachers = models.Teacher.objects.filter(uuid=teacher_uuid, deleted=False)
        else:
            if teacher_name:
                teachers = models.Teacher.objects.filter(name=teacher_name, deleted=False)
            else:
                teachers = None
        try:
            if birthday:
                teachers = teachers.filter(birthday=parse_date(birthday))
        except:
            logger.exception('')

        if teachers:
            teacher = teachers[0]
        else:
            teacher = None

        auto_number = False
        if not isinstance(class_number, int):
            auto_number = True
            class_number = str_util.class_name_to_number(name)
        if self.instance._state.adding:
            lst = g.class_set.values_list('number', flat=True)
            lst = list(set(range(1, max(lst and lst or [1]) + 2)) - set(lst))
            if not class_number in lst and auto_number:
                class_number = lst[0]
        else:
            class_number = self.instance.number

        if self.instance._state.adding:
            obj = models.Class.objects.create(name=name, number=class_number, grade=g, teacher=teacher)
        else:
            obj = self.instance
            obj.teacher = teacher
            obj.save()

        return obj

    class Meta:
        model = models.Class
        exclude = ['uuid', 'grade', 'last_active_time', 'teacher', 'number']


ClassFormSet = formset_factory(ClassForm)


class ClassUploadForm(forms.Form):
    excel = forms.FileField()
    _valid_extensions = ['.xls', '.xlsx']
    _fields = ['grade', 'class']
    head = [u'年级', u'班级']

    def __init__(self, *args, **kwargs):
        super(ClassUploadForm, self).__init__(*args, **kwargs)
        self.fields['excel'].error_messages = {
            'required': '请上传学校年级班级的xls文件！'
        }

    def clean(self):
        cleaned_data = super(ClassUploadForm, self).clean()
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
                elif cmp(self.head, sheet.row_values(0)[:len(self.head)]) != 0:
                    logger.info('Class import excel head not match!')
                    self._errors['excel'] = u'所导入的文件与该信息表格模板格式不相符！'
                else:
                    self.sheet = sheet
        return cleaned_data

    def save(self, commit=True):
        ret = []
        for l in parse_xls(self.sheet):
            form = ClassForm(l)
            if form.is_valid():
                try:
                    obj = form.save()
                    ret.append(obj)
                except:
                    logger.exception('')
                    logger.info('GradeClass excel: exception %s', str(l))
                    continue
            else:
                logger.info('GradeClass excel: invalid %s', str(l))
                logger.info(str(form.errors))
        return ret

    def verify(self):
        ret = []
        for l in parse_xls(self.sheet):
            form = ClassForm(l)
            if not form.is_valid():
                ret.append({'row': l['row'], 'error': form.errors.as_text()})
        return ret


def parse_xls(sheet):
    ret = []
    for i in xrange(1, sheet.nrows):
        try:
            row = sheet.row_values(i)
            if len(row) < 2:
                continue
            grade_name = row[0]
            if isinstance(grade_name, float):
                grade_name = str(int(row[0]))
            class_name = row[1]
            if isinstance(class_name, float):
                class_name = str(int(row[1]))
            grade_class = {
                'row': i + 1,
                'grade_name': grade_name,
                'name': class_name
            }
            ret.append(grade_class)
        except:
            logger.exception('')
            logger.info('GradeClass excel: skip %s %s', str(i + 1), str(row))
            continue
    return ret
