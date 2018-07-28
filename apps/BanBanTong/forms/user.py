# coding=utf-8
from django import forms
from django.conf import settings
from django.forms.models import formset_factory
from BanBanTong.db import models


class UserPermittedGroupForm(forms.ModelForm):

    class Meta:
        model = models.UserPermittedGroup
        exclude = ['uuid', 'user']


UserPermittedGroupFormSet = formset_factory(UserPermittedGroupForm)


class UserForm(forms.ModelForm):
    password_confirmation = forms.CharField(max_length=128,
                                            widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['username'].error_messages = {
            'required': '请输入用户名！'
        }
        self.fields['role'].error_messages = {
            'invalid_choice': '选择的角色是无效的！',
        }
        self.fields['password'].error_messages = {
            'required': '请输入密码！'
        }
        self.fields['password_confirmation'].error_messages = {
            'required': '请输入确认密码！'
        }

        self.fields['password'].widget = forms.PasswordInput()

        if not self.instance._state.adding:
            self.fields['password'].required = False
            self.fields['password_confirmation'].required = False
        else:
            self.fields['password'].required = True
            self.fields['password_confirmation'].required = True
        self.fields['level'].required = False

    def clean(self):
        cleaned_data = super(UserForm, self).clean()

        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        password_confirmation = cleaned_data.get('password_confirmation')

        username_existing = False

        if self.instance._state.adding:
            if models.User.objects.filter(username=username).exclude(username='oseasy').exists():
                username_existing = True
            elif username == 'oseasy':
                err = self.error_class(['用户名不能为系统保留字段'])
                self._errors['username'] = err
                if cleaned_data.has_key('username'):
                    del cleaned_data['username']
        else:
            q = models.User.objects.filter(username=username).exclude(username='oseasy')
            q = q.exclude(uuid=self.instance.uuid)
            if q.exists():
                username_existing = True
            else:
                if self.instance.username in settings.ADMIN_USERS and username != self.instance.username:
                    if self.instance.username == 'admin':
                        err = self.error_class(['超级管理员的用户名不能修改！'])
                        self._errors['username'] = err
                        if cleaned_data.has_key('username'):
                            del cleaned_data['username']
                    elif self.instance.username == 'oseasy':
                        err = self.error_class(['用户名为系统保留字段'])
                        self._errors['username'] = err
                        if cleaned_data.has_key('username'):
                            del cleaned_data['username']

        if username_existing:
            self._errors['username'] = self.error_class(['用户名已存在！'])
            del cleaned_data['username']

        elif password and password_confirmation:
            if password != password_confirmation:
                err = self.error_class(['确认密码与密码不匹配！'])
                self._errors['password_confirmation'] = err
                del cleaned_data['password']
                del cleaned_data['password_confirmation']
        else:
            del cleaned_data['password']
            del cleaned_data['password_confirmation']
        cleaned_data['level'] = models.Setting.getvalue('server_type')
        return cleaned_data

    class Meta:
        model = models.User
        exclude = ['uuid', 'created_at', 'permitted_groups']


class ProfileForm(forms.ModelForm):
    password_confirmation = forms.CharField(max_length=255,
                                            widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['password'].error_messages = {
            'required': '请输入密码！'
        }
        self.fields['password_confirmation'].error_messages = {
            'required': '请输入确认密码！'
        }

        self.fields['password'].widget = forms.PasswordInput()

        if not self.instance._state.adding:
            self.fields['password'].required = False
            self.fields['password_confirmation'].required = False

        else:
            self.fields['password'].required = True
            self.fields['password_confirmation'].required = True

    def clean(self):
        cleaned_data = super(ProfileForm, self).clean()

        password = cleaned_data.get('password')
        password_confirmation = cleaned_data.get('password_confirmation')

        if password and password_confirmation:
            if password != password_confirmation:
                err = self.error_class(['确认密码与密码不匹配！'])
                self._errors['password_confirmation'] = err
                del cleaned_data['password']
                del cleaned_data['password_confirmation']

        else:
            del cleaned_data['password']
            del cleaned_data['password_confirmation']

        return cleaned_data

    class Meta:
        model = models.User
        exclude = ['uuid', 'created_at', 'last_login_at', 'last_login_ip',
                   'permitted_groups', 'role', 'username', 'level', 'status']
