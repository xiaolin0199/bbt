# coding=utf-8
from django import forms
from django.db.models import Q
from django.forms.models import formset_factory

from BanBanTong.db import models


class RolePrivilegesForm(forms.ModelForm):

    class Meta:
        model = models.RolePrivilege
        exclude = ['uuid', 'role']


class RoleForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(RoleForm, self).__init__(*args, **kwargs)
        self.fields['name'].error_messages = {
            'required': u'请输入角色名！'
        }

    def clean(self):
        cleaned_data = super(RoleForm, self).clean()

        name = cleaned_data.get('name')

        # 判断角色名是否重复
        if name:
            existing = False
            if self.instance._state.adding:
                if models.Role.objects.filter(name=name).count() > 0:
                    existing = True
            else:
                if models.Role.objects.filter(~Q(uuid=self.instance.uuid),
                                              name=name).count() > 0:
                    existing = True
            if existing:
                self._errors['name'] = self.error_class([u'角色名已存在！'])

        return cleaned_data

    class Meta:
        model = models.Role
        exclude = ['uuid']


RolePrivilegesFormSet = formset_factory(RolePrivilegesForm)
