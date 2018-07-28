#!/usr/bin/env python
# coding=utf-8
from django.test import TestCase
from BanBanTong.db import models
from BanBanTong.utils import cloud_service


class CloudServiceTest(TestCase):

    def test_wrong_server_type(self):
        models.Setting(name='server_type', value='province').save(force_insert=True)
        models.Setting(name='country', value=u'武昌区').save(force_insert=True)
        self.assertEqual(cloud_service.generate_bucket_name(), '')

    def test_result(self):
        models.Setting(name='server_type', value='school').save(force_insert=True)
        models.Setting(name='country', value=u'武昌区').save(force_insert=True)
        models.GroupTB(group_id=420106, name=u'武昌区', parent_id=420100).save(force_insert=True)
        obj = models.GroupTB.objects.get(name=models.Setting.getvalue('country'))
        self.assertEqual(cloud_service.generate_bucket_name(),
                         'oebbt-' + str(obj.group_id))
