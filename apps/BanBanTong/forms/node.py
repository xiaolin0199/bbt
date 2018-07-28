# coding=utf-8
from django import forms
from django.forms.models import formset_factory
from BanBanTong.db import models
from activation.decorator import get_none_activate


class NodeForm(forms.ModelForm):
    name = forms.CharField(max_length=20, required=True)
    communicate_key = forms.CharField(max_length=16, required=True)
    activation_number = forms.IntegerField(required=False)
    remark = forms.CharField(max_length=180, required=False)

    def __init__(self, *args, **kwargs):
        super(NodeForm, self).__init__(*args, **kwargs)
        if not self.instance._state.adding:
            self.fields['name'].required = False
            self.fields['communicate_key'].required = False
            self.fields['activation_number'].required = True
            self.fields['remark'].required = False

    def clean_name(self):
        '''
            校验学校不能同名
        '''
        node_name = self.cleaned_data.get('name')
        if self.instance._state.adding:
            if models.Node.objects.all().filter(name=node_name).exists():
                raise forms.ValidationError(u'学校名称已存在.')
        return node_name

    def clean_activation_number(self):
        '''
            校验activation_number的合法性,这个很复杂
            前提: 欲分配数量需要 > 0 (至少为1) , 同时欲分配的数量必须 >= 实际使用的数量
            1. 当可分配 <= 0:
                1.1 欲分配数量比原先的大， False
                1.2 欲分配数量比原先的小， True
            2. 当可分配 > 0:
                2.1 欲分配数量比原先的大
                    2.1.1 欲分配数量与原分配数量的差额 > 可分配, False
                    2.1.2 欲分配数量与原分配数量的差额 <= 可分配, True
        '''
        # 原分配
        old_number = self.instance.activation_number
        # 实际使用 (该node学校已使用的授权点，即该学校已存在多个少班级)
        real_use_number = self.instance.get_use_number()
        # 欲分配
        activation_number = self.cleaned_data.get('activation_number', 0)
        # 可分配
        none_number = get_none_activate()

        if activation_number is None:
            activation_number = 0

        # 欲分配不合法
        if activation_number <= 0:
            raise forms.ValidationError(u'欲分配授权终端数量需为正整数')

        # 欲分配的数量不得小于实际已使用的数量
        if activation_number < real_use_number:
            raise forms.ValidationError(u'欲分配授权终端数量不得小于实际已使用的数量')

        # 已无可分配的数量
        if none_number <= 0:
            # 欲分配 > 原分配
            if activation_number > old_number:
                raise forms.ValidationError(u'可分配授权终端数量不足，请更新授权')
        # 还有可分配的数量
        else:
            # 欲分配 - 原分配 > 可分配
            if activation_number - old_number > none_number:
                raise forms.ValidationError(u'可分配授权终端数量不足，请更新授权')

        return activation_number

    def save(self, commit=True):
        if 'activation_number' in self.cleaned_data and self.cleaned_data['activation_number'] is None:
            self.cleaned_data['activation_number'] = 0
            self.instance.activation_number = 0

        if self.instance._state.adding:
            super(NodeForm, self).save(commit)
            return self.instance
        else:
            remark = self.cleaned_data['remark']
            activation_number = self.cleaned_data['activation_number']

            self.instance.activation_number = activation_number
            self.instance.remark = remark
            self.instance.save()
            return self.instance

    class Meta:
        model = models.Node
        fields = ['name', 'communicate_key', 'activation_number', 'remark']

NodeFormSet = formset_factory(NodeForm)
