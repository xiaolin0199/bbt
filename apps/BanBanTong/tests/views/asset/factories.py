#coding=utf-8

#import factory
from BanBanTong.tests import factory

from BanBanTong.db import models

#####################################################
#
class ProvinceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Group
        django_get_or_create = ('name',)

    #name = factory.Sequence(lambda n: u'测试省%s' % n)
    name = u'测试省'
    group_type = u'province'
    parent = None

class CityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Group
        django_get_or_create = ('name',)

    #name = factory.Sequence(lambda n: u'测试地市%s' % n)
    name = u'测试地市'
    group_type = u'city'
    parent = factory.SubFactory(ProvinceFactory)

class CountryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Group
        django_get_or_create = ('name',)

    #name = factory.Sequence(lambda n: u'测试区县%s' % n)
    name = u'测试区县'
    group_type = u'country'
    parent = factory.SubFactory(CityFactory)

class TownFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Group
        django_get_or_create = ('name',)

    #name = factory.Sequence(lambda n: u'测试街道%s' % n)
    name = u'测试街道'
    group_type = u'town'
    parent = factory.SubFactory(CountryFactory)

class SchoolFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Group
        django_get_or_create = ('name',)

    #name = factory.Sequence(lambda n: u'测试学校%s' % n)
    name = u'测试学校'
    group_type = u'school'
    parent = factory.SubFactory(TownFactory)

#
###############################################################

class AssetTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.AssetType

    name = factory.Sequence(lambda n: u'电脑%d' % n)

    @factory.sequence
    def icon(n):
        return u'pc%d' % n

class AssetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Asset

    asset_type = factory.SubFactory(AssetTypeFactory)
    school = factory.SubFactory(SchoolFactory)
    number = factory.Sequence(lambda n: u'%d' %n)
    device_model = factory.LazyAttribute(lambda v: u'HP%s' % v.number)
    asset_from = factory.Iterator(models.ASSET_FROM, getter=lambda c:c[0])
    reported_by = u'admin'

