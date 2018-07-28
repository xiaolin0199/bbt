# coding=utf-8
from django.conf.urls import url
import asset_repair
import asset_log
import asset_type
import asset


urlpatterns = [
    # 资产管理->资产统计与申报
    url(r'^asset-type/?$', asset_type.list_current),
    url(r'^asset-type/aggregate/?$', asset_type.aggregate),
    url(r'^asset-type/export/?$', asset_type.export),
    url(r'^add/?$', asset.add),
    url(r'^delete/?$', asset.delete),
    url(r'^export/?$', asset.export),
    url(r'^$', asset.list_current),
    url(r'^aggregate/?$', asset.aggregate),
    # 资产管理>申报记录查询
    url(r'^asset-log/export/?$', asset_log.export),
    url(r'^asset-log/?$', asset_log.list_current),
    # 资产管理>资产维修管理
    url(r'^asset-repair/add/?$', asset_repair.add),
    url(r'^asset-repair/export/?$', asset_repair.export),
    url(r'^asset-repair/?$', asset_repair.list_current),
    url(r'^get-devicemodel-by-assettype/?$', asset.get_devicemodel_by_assettype),
    url(r'^asset-type/get-assettype-for-repair/?$', asset_type.get_assettype_for_repair),
]
