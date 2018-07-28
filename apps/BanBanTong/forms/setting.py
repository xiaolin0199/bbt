# coding=utf-8
import hashlib
import uuid
from django import forms
from django.conf import settings
from BanBanTong.db import models


class ServerInfoForm(forms.Form):
    '''安装新服务器的第一步：服务器类型和地区'''
    host = forms.CharField(max_length=100, required=False)
    port = forms.IntegerField(required=False)
    server_type = forms.ChoiceField(choices=models.GROUP_TYPES)
    school_name = forms.CharField(max_length=100, required=False)
    province = forms.CharField(max_length=100)
    city = forms.CharField(max_length=100)
    country = forms.CharField(max_length=100, required=False)
    town = forms.CharField(max_length=100, required=False)
    install_step = forms.IntegerField()

    def save(self):
        if self.cleaned_data['host']:
            obj, c = models.Setting.objects.get_or_create(name='host')
            obj.value = self.cleaned_data['host']
            obj.save()
            models.Setting.objects.filter(name='host_new').delete()
            models.Setting.objects.create(name='host_new',
                                          value=self.cleaned_data['host'])
        if self.cleaned_data['port']:
            obj, c = models.Setting.objects.get_or_create(name='port')
            obj.value = self.cleaned_data['port']
            obj.save()
        server_type = self.cleaned_data['server_type']
        models.Setting.objects.create(name='server_type',
                                      value=server_type)
        models.Setting.objects.create(name='install_step',
                                      value=self.cleaned_data['install_step'])
        province_name = self.cleaned_data['province']
        models.Setting.objects.create(name='province',
                                      value=province_name)
        s = province_name
        uu = str(uuid.uuid5(uuid.NAMESPACE_DNS, s.encode('utf8'))).upper()
        province = models.Group.objects.create(uuid=uu,
                                               name=province_name,
                                               group_type='province')
        city_name = self.cleaned_data['city']
        models.Setting.objects.create(name='city', value=city_name)
        s = u'%s.%s' % (province_name, city_name)
        uu = str(uuid.uuid5(uuid.NAMESPACE_DNS, s.encode('utf8'))).upper()
        city = models.Group.objects.create(uuid=uu,
                                           name=city_name,
                                           group_type='city',
                                           parent=province)
        school = None
        if server_type == 'school':
            school_name = self.cleaned_data['school_name']
            if school_name:
                models.Setting.objects.create(name='school',
                                              value=school_name)
                school = models.Group(name=school_name,
                                      group_type='school', parent=city)

        country_name = self.cleaned_data['country']
        if country_name:
            models.Setting.objects.create(name='country',
                                          value=country_name)
            s = u'%s.%s' % (s, country_name)
            uu = str(uuid.uuid5(uuid.NAMESPACE_DNS, s.encode('utf8'))).upper()
            country = models.Group.objects.create(uuid=uu,
                                                  name=country_name,
                                                  group_type='country',
                                                  parent=city)
            if server_type == 'school':
                school.parent = country

            town_name = self.cleaned_data['town']
            if town_name:
                models.Setting.objects.create(name='town',
                                              value=town_name)
                s = u'%s.%s' % (s, town_name)
                uu = str(uuid.uuid5(uuid.NAMESPACE_DNS, s.encode('utf8')))
                uu = uu.upper()
                town = models.Group.objects.create(uuid=uu,
                                                   name=town_name,
                                                   group_type='town',
                                                   parent=country)
                if server_type == 'school':
                    school.parent = town
        if server_type == 'school':
            school.save()

        models.User.objects.all().delete()
        for username in settings.ADMIN_USERS:
            passhash = hashlib.sha1(username).hexdigest()
            if username == 'oseasy':
                passhash = hashlib.sha1('0512').hexdigest()

            models.User.objects.create(username=username,
                                       password=passhash,
                                       sex='',
                                       status='active',
                                       level=server_type,
                                       remark=u'系统管理员')


class StepForm(forms.Form):
    install_step = forms.IntegerField()

    def save(self):
        install_step = self.cleaned_data['install_step']
        obj, c = models.Setting.objects.get_or_create(name='install_step')
        obj.value = install_step
        obj.save()
        if obj.value == -1:  # 把服务器标记为安装完成
            i, c = models.Setting.objects.get_or_create(name='installed')
            i.value = True
            i.save()
