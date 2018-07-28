# coding=utf-8
from django import forms
from BanBanTong.db import models


class AssetForm(forms.ModelForm):

    def clean(self):
        cleaned_data = super(AssetForm, self).clean()
        return cleaned_data

    class Meta:
        model = models.Asset
        exclude = ['uuid', 'school', 'status', 'reported_by']


class AssetRepairForm(forms.ModelForm):

    class Meta:
        model = models.AssetRepairLog
        exclude = ['uuid', 'reported_by', 'reported_at', 'school']
