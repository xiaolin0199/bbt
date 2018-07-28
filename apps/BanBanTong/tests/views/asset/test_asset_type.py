#coding=utf-8

from django.test import TestCase
from django.test import Client

from BanBanTong.db import models
from factories import AssetTypeFactory

import json
import hashlib

class AssetTypeTestCase(TestCase):
    def setUp(self):
        #重置序列号从几开始
        #AssetTypeFactory.reset_sequence(1)

        #__sequence可以指定序列号
        #1
        AssetTypeFactory(cannot_delete=True,__sequence=10)
        #2
        AssetTypeFactory(__sequence=20)

        
        #登陆
        username = 'admin'
        password = hashlib.sha1('admin'.encode('utf8')).hexdigest()
        user = models.User.objects.get_or_create(username=username,password=password)

        self.client.post('/login/',{'username':'admin','password':'admin'})


    def test_asset_type_model(self):
        a = models.AssetType.objects.get(name=u'电脑10')
        b = models.AssetType.objects.get(name=u'电脑20')

        self.assertEqual(a.test_speak(), u'pc10')
        self.assertEqual(b.test_speak(), u'pc20')

        self.assertEqual(a.cannot_delete, True)
        self.assertEqual(b.cannot_delete, False)

    def test_asset_type_list_current(self):
        response = self.client.get('/asset/asset-type/')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        #状态是否为success
        self.assertEqual(data.get('status'), u'success')
        #是否二条纪录
        self.assertEqual(len(data.get('data').get('records')),2)

    def tearDown(self):
        #退出登陆
        self.client.post('/logout/')

