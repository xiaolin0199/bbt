# coding=utf-8
import logging
from django import forms
from django.forms.models import formset_factory
from BanBanTong.db import models

logger = logging.getLogger(__name__)


class ClassForm(forms.ModelForm):
    error_messages = {
        'field_type_error': u'数据输入不合法',
        'can_not_rename': u'该电脑教室已存在终端使用时长数据,不可修改名称',
    }

    def __init__(self, *args, **kwargs):
        super(ClassForm, self).__init__(*args, **kwargs)
        if not self.instance._state.adding:
            self._term = self.instance.grade.term
        else:
            self._term = models.Term.get_current_term_list()[0]
        self._grade, is_new = models.Grade.objects.get_or_create(
            name=u'电脑教室',
            term=self._term,
            number=13
        )

    def clean_name(self):
        name = self.cleaned_data["name"]
        if self.instance._state.adding:
            cls = self._grade.class_set
        else:
            cls = self._grade.class_set.exclude(pk=self.instance.pk)

        try:
            cls.get(name=name)
            self._errors['name'] = u'电脑教室(%s)已经存在' % name
            del self.cleaned_data['name']
        except models.Class.DoesNotExist:
            if name and len(name) > 20:
                self._errors['name'] = u'教室名称(%s)超出最大字符限制' % name
                try:
                    del self.cleaned_data['name']
                except:
                    pass

            if not self.instance._state.adding and self.instance.name != name:
                # 以下几种情况下可以修改电脑教室的名称
                # 1 机器时长功能尚未引入
                # 2 本学年学期未产生目标电脑教室的机器时长数据
                from machine_time_used import models as m
                objs = m.MachineTimeUsed.objects.filter(
                    term_school_year=self._term.school_year,
                    term_type=self._term.term_type,
                    grade_name=self.instance.grade.name,
                    class_name=self.instance.name
                )
                if objs.exists():
                    raise forms.ValidationError(
                        self.error_messages['can_not_rename'],
                        code='can_not_rename',
                    )

            return name
        except Exception as e:
            self._errors['name'] = u'服务器错误(%s)' % e
            try:
                del self.cleaned_data['name']
            except:
                pass

    def save(self, commit=True):
        obj = super(ClassForm, self).save(commit=False)
        name = self.cleaned_data['name']
        if self.instance._state.adding:
            lst = self._grade.class_set.values_list('number', flat=True)
            lst = set(range(1, max(lst and lst or [1]) + 2)) - set(lst)
            number = list(lst)[0]
            obj.number = number
        obj.name = name
        obj.grade = self._grade
        if commit:
            obj.save()
        return obj

    class Meta:
        model = models.Class
        fields = ['name', ]


class ComputerClassForm(forms.ModelForm):
    error_messages = {
        'duplicate_classname': u'已存在同名教室.',
        'value_range_error': u'客户端数量应该在0到300之间.',
        'server_error': u'服务器错误,如果是第一次出现,请尝试重启服务,\n \
                          如果反复出现,请联系管理员解决该问题.',
        'field_type_error': u'数据输入不合法',
        'lesson_does_not_exist': u'课程不存在',
    }
    client_number = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        self._cls = kwargs.get('cls')
        self._cc = kwargs.get('cc')
        self._request = kwargs.get('request')
        _term = models.Term.get_current_term_list()[0]
        self.term = _term
        self.grade, is_new = models.Grade.objects.get_or_create(
            name=u'电脑教室',
            term=_term,
            number=13
        )
        if self._cls:
            del kwargs['cls']
        if self._cc:
            del kwargs['cc']
        if self._request:
            del kwargs['request']
        if self._cc:
            kwargs['instance'] = self._cc
        super(ComputerClassForm, self).__init__(*args, **kwargs)
        if 'instance' in kwargs:
            del kwargs['instance']
        if self._cls:
            kwargs['instance'] = self._cls
        self.cls = ClassForm(*args, **kwargs)

    def clean_lesson_range(self):
        if not self._request:
            self.lesson_range = models.LessonName.objects.none()
            return
        lesson_range = self._request.POST.getlist('lesson_range', [])
        lesson_instance = []
        for pk in lesson_range:
            try:
                obj = models.LessonName.objects.get(pk=pk, deleted=False)
                lesson_instance.append(obj)
            except models.LessonName.DoesNotExist:
                raise forms.ValidationError(
                    self.error_messages['lesson_does_not_exist'],
                    code='lesson_does_not_exist',
                )
            except Exception:
                raise forms.ValidationError(
                    self.error_messages['server_error'],
                    code='server_error'
                )
        self.lesson_range = lesson_instance

    def clean_client_number(self):
        client_number = self.cleaned_data["client_number"]
        try:
            client_number = int(client_number)
        except:
            raise forms.ValidationError(
                self.error_messages['field_type_error'],
                code='field_type_error',
            )

        if 0 <= client_number <= 300:
            return client_number
        else:
            raise forms.ValidationError(
                self.error_messages['value_range_error'],
                code='value_range_error',
            )

    def clean(self):
        cleaned_data = super(ComputerClassForm, self).clean()
        self.clean_lesson_range()
        return cleaned_data

    @property
    def errors(self):
        if self._errors is None:
            self.full_clean()
        if not self.cls.is_valid():
            if not self._errors:
                self._errors = {}
            self.cls.full_clean()
            self._errors.update(self.cls._errors)
        return self._errors

    def is_valid(self):
        flag = super(ComputerClassForm, self).is_valid()
        return self.cls.is_valid() and flag

    def save(self, commit=True):
        cls = self.cls.save()
        obj = super(ComputerClassForm, self).save(commit=False)
        obj.class_bind_to = cls
        obj.client_number = self.cleaned_data['client_number']
        if commit:
            obj.save()
            obj.computerclasslessonrange_set.all().delete()
            for u in self.lesson_range:
                models.ComputerClassLessonRange.objects.create(
                    computerclass=obj,
                    lessonname=u
                )
        return obj

    class Meta:
        model = models.ComputerClass
        fields = ['client_number', ]

ComputerClassFormSet = formset_factory(ComputerClassForm)
