# coding=utf-8
from django import forms

from BanBanTong.db import models


class ResourceForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ResourceForm, self).__init__(*args, **kwargs)
        self.fields['resource_from'].error_messages = {
            'required': '请输入资源来源！'
        }
        self.fields['resource_type'].error_messages = {
            'required': '请输入资源类型！'
        }

    class Meta:
        model = models.Resource
        exclude = ['uuid']


class ResourceFromForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ResourceFromForm, self).__init__(*args, **kwargs)
        self.fields['value'].error_messages = {
            'required': '请输入资源来源！'
        }

    def clean_value(self):
        value = self.cleaned_data['value'].strip()
        froms = models.ResourceFrom.objects.filter(value=value)
        if froms.count() > 0:
            raise forms.ValidationError(u'已存在该资源来源')

        return value

    def save(self):
        # 只提供添加功能，不编辑
        country = models.Group.objects.get(group_type='country')
        obj = models.ResourceFrom(country=country,
                                  value=self.cleaned_data['value'])
        remark = self.cleaned_data['remark']
        if remark:
            obj.remark = remark
        obj.save()
        return obj

    class Meta:
        model = models.ResourceFrom
        exclude = ['uuid', 'country']


class ResourceTypeForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ResourceTypeForm, self).__init__(*args, **kwargs)
        self.fields['value'].error_messages = {
            'required': '请输入资源类型！'
        }

    def clean_value(self):
        value = self.cleaned_data['value'].strip()
        types = models.ResourceType.objects.filter(value=value)
        if types.count() > 0:
            raise forms.ValidationError(u'已存在该资源类型')

        return value

    def save(self):
        # 只提供添加功能，不编辑
        country = models.Group.objects.get(group_type='country')
        obj = models.ResourceType(country=country,
                                  value=self.cleaned_data['value'])
        remark = self.cleaned_data['remark']
        if remark:
            obj.remark = remark
        obj.save()
        return obj

    class Meta:
        model = models.ResourceType
        exclude = ['uuid', 'country']
