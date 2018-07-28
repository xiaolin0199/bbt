#coding=utf-8

from django.test import TestCase
from django.test import Client

from BanBanTong.db import models
from factories import AssetFactory , AssetTypeFactory
from factories import TownFactory , SchoolFactory

import json
import hashlib

class AssetTestCase(TestCase):
    def setUp(self):

        self.a = AssetFactory(number=30)
        #登陆
        username = 'admin'
        password = hashlib.sha1('admin'.encode('utf8')).hexdigest()
        user = models.User.objects.get_or_create(username=username,password=password)

        self.client.post('/login/',{'username':'admin','password':'admin'})

    def test_asset_add(self):
        add_url = '/asset/add/'
        asset_type = AssetTypeFactory()
        post_data = {
            'asset_type': asset_type.uuid,
            'device_model': u'HP10',
            'number': 10,
            'asset_from': u'校自主采购',
            'remark': u'DDD'
        }

        #asset需要Group表里预先有school及town信息
        school = SchoolFactory()
        town = TownFactory(parent=school)

        #执行操作
        response = self.client.post(add_url, post_data)
 
        #检测 
        data = json.loads(response.content)
        self.assertEqual(data.get('status'), u'success')

        #每创建一条asset纪录时，会同步创建一条assetlog纪录，检测一下
        log = models.AssetLog.objects.latest('reported_by')
        #log = models.AssetLog.objects.get(town=town, school=school, asset_type=asset_type, device_model=u'HP10', number=10)
        self.assertEqual(log.town, town)
        self.assertEqual(log.school, school)
        self.assertEqual(log.asset_type, asset_type)
        self.assertEqual(log.device_model, u'HP10')
        self.assertEqual(log.number, 10)



    def test_asset_delete(self):
        delete_url = '/asset/delete/'
        post_data = {
            'uuid': self.a.uuid,
            'number': 10
        }
        #有足够的可供停用资产
        response = self.client.post(delete_url, post_data)

        data = json.loads(response.content)
        self.assertEqual(data.get('status'), u'success')

        #原30个,已停用10个，再停用30将不会成功
        post_data = {
            'uuid': self.a.uuid,
            'number': 30
        }

        response = self.client.post(delete_url, post_data)

        data = json.loads(response.content)
        self.assertEqual(data.get('status'), u'failure')
        self.assertEqual(data.get('msg'), u'停用数量超过批次数量！')




    def tearDown(self):
        #退出登陆
        self.client.post('/logout/')

