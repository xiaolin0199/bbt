# coding=utf-8
import hashlib
import datetime

from django import forms
from BanBanTong.db import models
from BanBanTong.utils import get_ip


class UserLoginForm(forms.Form):
    username = forms.CharField(max_length=255,
                               error_messages={'required': u'请输入用户名！'})
    password = forms.CharField(max_length=255,
                               widget=forms.PasswordInput,
                               error_messages={'required': u'请输入密码！'})

    def set_request(self, request):
        self._request = request

    def clean(self):
        cleaned_data = super(UserLoginForm, self).clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            err = self.error_class([u'用户名或密码错误！'])
            try:
                user = models.User.objects.get(username=username)
                passbyte = password.encode('utf8')
                if user.password != hashlib.sha1(passbyte).hexdigest():
                    self._errors['password'] = err
                    del cleaned_data['password']
                elif user.status == 'suspended':
                    self._errors['username'] = self.error_class([u'该账户已禁用！'])
                    del cleaned_data['password']
                else:
                    self._logged_user = user
            except:
                self._errors['username'] = err
                del cleaned_data['username']

        return cleaned_data

    def save(self):
        self._logged_user.last_login_at = datetime.datetime.now()
        self._logged_user.last_login_ip = get_ip(self._request)
        self._logged_user.save()
        return self._logged_user
