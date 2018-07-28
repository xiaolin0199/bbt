# coding=utf-8
import logging
import os
import traceback
from django import forms
from django.conf import settings
from django.db.models import Q
from BanBanTong.db import models
import xlrd
from BanBanTong.utils.datetimeutil import excel_float_to_date

DEBUG = settings.DEBUG
logger = logging.getLogger(__name__)


class TeacherForm(forms.ModelForm):
    password_confirmation = forms.CharField(max_length=255, widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        super(TeacherForm, self).__init__(*args, **kwargs)
        self.fields['password'].widget = forms.PasswordInput()
        self.fields['name'].error_messages['required'] = u'请输入教师姓名！'
        if 'sequence' in self.fields:
            self.fields['sequence'].required = False
        self.fields['sex'].error_messages = {
            'required': u'请输入教师性别！',
            'invalid_choice': u'性别填写错误！'
        }
        self.fields['birthday'].error_messages = {
            'required': u'请输入教师出生年月！',
            'invalid': u'出生年月输入有误！'
        }
        self.fields['edu_background'].error_messages = {
            'required': u'请输入教师学历！'
        }
        self.fields['password'].required = False
        self.fields['password_confirmation'].required = False
        self.school = models.Group.objects.get(group_type='school')

    def clean_name(self):
        data = self.cleaned_data['name'].strip()
        data = data.replace(' ', '')
        if not data:
            raise forms.ValidationError(u'教师姓名不能为空')
        return data

    def clean_sex(self):
        data = self.cleaned_data['sex'].strip()
        data = data.replace(' ', '')
        if not data:
            raise forms.ValidationError(u'性别不能为空')
        return data

    def clean_edu_background(self):
        data = self.cleaned_data['edu_background'].strip()
        data = data.replace(' ', '')
        if not data:
            raise forms.ValidationError(u'教师学历不能为空')
        return data

    def clean_title(self):
        data = self.cleaned_data['title'].strip()
        data = data.replace(' ', '')
        return data

    def clean_mobile(self):
        data = self.cleaned_data['mobile'].strip()
        data = data.replace(' ', '')
        return data

    def clean_qq(self):
        data = self.cleaned_data['qq'].strip()
        data = data.replace(' ', '')
        return data

    def clean_remark(self):
        data = self.cleaned_data['remark'].strip()
        data = data.replace(' ', '')
        return data

    def clean(self):
        cleaned_data = super(TeacherForm, self).clean()
        name = cleaned_data.get('name')
        password = cleaned_data.get('password')
        password_confirmation = cleaned_data.get('password_confirmation')
        birthday = cleaned_data.get('birthday')

        names = [name, '%s(%s)' % (name, birthday.strftime('%y%m%d'))]
        objs = models.Teacher.objects.filter(
            name__in=names,
            # birthday=birthday,
            school=self.school
        )
        if objs.exists():
            for o in objs:
                if o.birthday == birthday and self.instance._state.adding:
                    o.deleted = False
                    o.save()
                    self._errors['name'] = u'教师(%s)已存在' % name

            else:
                if self.instance._state.adding:
                    name = '%s(%s)' % (name, birthday.strftime('%y%m%d'))
                    cleaned_data['name'] = name

        existing = False
        different_password = False

        if self.instance._state.adding:
            if password and password_confirmation:
                if password == password_confirmation:
                    if name:
                        if models.Teacher.objects.filter(
                                # password=password,
                                deleted=False,
                                name=name).exists():
                            existing = True
                else:
                    different_password = True
            else:
                if birthday:
                    password = birthday.strftime('%m%d')
                    cleaned_data['password'] = password
                    cleaned_data['password_confirmation'] = password
        else:
            if password and password_confirmation:
                if password == password_confirmation:
                    if name:
                        if models.Teacher.objects.filter(~Q(uuid=self.instance.uuid),
                                                         # password=password,
                                                         name=name).exists():
                            existing = True
                else:
                    different_password = True
            else:
                if name:
                    if models.Teacher.objects.filter(~Q(uuid=self.instance.uuid),
                                                     # password=self.instance.password,
                                                     name=name).exists():
                        existing = True
            if not birthday:
                birthday = self.instance.birthday
                cleaned_data['birthday'] = birthday

            if not password and birthday:
                cleaned_data['password'] = birthday.strftime('%m%d')

        if different_password:
            err = self.error_class([u'密码与确认密码不匹配！'])
            self._errors['password_confirmation'] = err

        if existing:
            self._errors['name'] = self.error_class([u'该教师信息已存在'])

        return cleaned_data

    class Meta:
        model = models.Teacher
        exclude = ['uuid', 'register_at', 'deleted', 'school']


class TeacherUploadForm(forms.Form):
    _valid_extensions = ['.xls', '.xlsx']
    excel = forms.FileField()
    head = [u'ID', u'姓名', u'性别', u'学历', u'出生年月',
            u'教师职称', u'注册时间', u'移动电话', u'QQ', u'备注']

    def __init__(self, *args, **kwargs):
        super(TeacherUploadForm, self).__init__(*args, **kwargs)
        self.fields['excel'].error_messages = {
            'required': u'请上传教职人员基础信息的xls文件！'
        }

    def clean(self):
        cleaned_data = super(TeacherUploadForm, self).clean()
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
                    self._errors['excel'] = u'所导入的文件与该信息表格模板格式不相符！'
                    del cleaned_data['excel']
                else:
                    self.sheet = sheet
        return cleaned_data

    def save(self, commit=True):
        ret = []
        school = models.Group.objects.get(group_type='school')
        objs, errors = parse_xls(self.sheet)

        for t in objs:
            try:
                instance = models.Teacher.objects.get(name=t['name'],
                                                      birthday=t['birthday'])
                instance.deleted = False
                instance.save()
                form = TeacherForm(t, instance=instance)
            except:
                form = TeacherForm(t)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.school = school
                obj.deleted = False
                obj.save()
                ret.append(obj)
            else:
                logger.debug('Teacher excel: invalid %s, err=%s', str(t), form.errors)
        return ret


class TeacherUploadVerifyForm(forms.Form):
    _valid_extensions = ['.xls', '.xlsx']
    excel = forms.FileField()
    head = [u'ID', u'姓名', u'性别', u'学历', u'出生年月',
            u'教师职称', u'注册时间', u'移动电话', u'QQ', u'备注']

    def __init__(self, *args, **kwargs):
        super(TeacherUploadVerifyForm, self).__init__(*args, **kwargs)
        self.fields['excel'].error_messages = {
            'required': '请上传教职人员基础信息的xls文件！'
        }

    def clean(self):
        cleaned_data = super(TeacherUploadVerifyForm, self).clean()
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
        objs, errors = parse_xls(self.sheet)
        for t in objs:
            try:
                instance = models.Teacher.objects.get(name=t['name'],
                                                      birthday=t['birthday'])
                form = TeacherForm(t, instance=instance)
            except:
                form = TeacherForm(t)
            ret.extend(errors)
            if not form.is_valid():
                ret.append({'row': t['row'], 'error': str(form.errors)})
        return ret


def parse_xls(sheet):
    objs = []
    errors = []
    for i in xrange(1, sheet.nrows):
        try:
            row = sheet.row_values(i)
            if len(row) < 10:
                logger.debug('Teacher xls: skip %s', str(i + 1))
                errors.append({'row': i + 1, 'error': u'单元格少于10个'})
                continue
            if isinstance(row[4], (str, unicode)):
                birthday = float(str(row[4]).strip().replace(' ', ''))
            else:
                birthday = row[4]
            if not isinstance(birthday, float):
                logger.debug('Teacher excel: birthday not float %s', str(i + 1))
                continue
            if isinstance(row[7], float):
                mobile = str(int(row[7]))
            else:
                mobile = row[7]
            if isinstance(row[8], float):
                qq = str(int(row[8]))
            else:
                qq = row[8]
            teacher = {
                'row': i + 1,
                'name': row[1].strip().replace(' ', ''),
                'sex': 'male' if row[2].strip() == u'男' else 'female',
                'edu_background': row[3].strip(),
                'birthday': excel_float_to_date(birthday),
                'title': row[5].strip(),
                'mobile': mobile,
                'qq': qq,
                'remark': row[9].strip(),
                'password': '',
                'password_confirmation': '',
            }
            birthday = teacher['birthday']
            teacher['password'] = '%02d%02d' % (birthday.month, birthday.day)
            teacher['password'] = str(teacher['password'])
            teacher['password_confirmation'] = teacher['password']
            objs.append(teacher)
        except:
            if DEBUG:
                traceback.print_exc()
            logger.exception('')
    ##
    # d = {}
    # for i, v in enumerate(objs):
    #     if not d.has_key(v['name']):
    #         d[v['name']] = [i]
    #     else:
    #         d[v['name']].append(i)
    #
    # for k in d:
    #     if len(d[k]) > 1:
    #         for i in d[k]:
    #             objs[i]['name'] = '%s(%s)' % (objs[i]['name'],
    #             objs[i]['birthday'].strftime('%m%d'))
    #
    return objs, errors
