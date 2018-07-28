#!/usr/bin/env python
# coding=utf-8
'''新增删除资产类型'''
import json
import os
import uuid
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db.models import Sum
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import format_record
from BanBanTong.utils import model_list_to_dict
import xlwt


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('asset_log')
def aggregate(request, *args, **kwargs):
    if request.method == 'GET':
        country_name = request.GET.get('country_name')
        town_name = request.GET.get('town_name')
        school_name = request.GET.get('school_name')
        cache.set('asset_type_list', json.dumps(request.GET))
        q = models.AssetType.objects.filter(deleted=False)
        if country_name:
            q = q.filter(school__parent__parent__name=country_name)
        if town_name:
            q = q.filter(school__parent__name=town_name)
        if school_name:
            q = q.filter(school__name=school_name)
        q = q.order_by().values('name', 'icon', 'unit_name').distinct()
        records = format_record.asset_type_total_in_use(q, request.GET)
        return create_success_dict(data={'records': records})


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('asset_log')
def export(request, *args, **kwargs):
    if models.Setting.getvalue('server_type') != 'school':
        c = cache.get('asset_type_list')
        if not c:
            return create_failure_dict(msg='查询超时无法导出，请重新查询！')
        cond = json.loads(c)
        country_name = cond.get('country_name')
        town_name = cond.get('town_name')
        school_name = cond.get('school_name')
    # now = datetime.date.today()
    #title = '%04d%02d%02d' % (now.year, now.month, now.day)
    title = u'资产统计'
    q = models.AssetType.objects.filter(deleted=False)
    if models.Setting.getvalue('server_type') != 'school':
        if country_name:
            q = q.filter(school__parent__parent__name=country_name)
        if town_name:
            q = q.filter(school__parent__name=town_name)
        if school_name:
            q = q.filter(school__name=school_name)
    q = q.values('uuid', 'name', 'unit_name', 'school')
    xls = xlwt.Workbook(encoding='utf8')
    sheet = xls.add_sheet(title)
    header = ['区县市', '街道乡镇', '学校', '资产设备名称',
              '单位', '数量', '批次数']
    for i in range(len(header)):
        sheet.write(0, i, header[i])
    row = 1
    for record in q:
        if record['school'] is not None:
            school = models.Group.objects.get(uuid=record['school'])
            sheet.write(row, 0, school.get_country_name())
            sheet.write(row, 1, school.get_town_name())
            sheet.write(row, 2, school.name)
        else:
            sheet.write(row, 0, u'')
            sheet.write(row, 1, u'')
            sheet.write(row, 2, u'')
        sheet.write(row, 3, record['name'])
        sheet.write(row, 4, record['unit_name'])
        a = models.Asset.objects.filter(asset_type__uuid=record['uuid'],
                                        status='在用')
        total = a.aggregate(sum=Sum('number'))['sum']
        if total is None:
            total = 0
        sheet.write(row, 5, total)
        sheet.write(row, 6, a.count())
        row += 1
    cached_id = str(uuid.uuid1())
    tmp_file = os.path.join(constants.CACHE_TMP_ROOT, cached_id)
    xls.save(tmp_file)
    filename = '%s.xls' % title
    return create_success_dict(url=reverse('base:xls_download',
                                           kwargs={'cached_id': cached_id,
                                                   'name': filename}))


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('asset_log')
def get_assettype_for_repair(request, *args, **kwargs):
    q = models.AssetType.objects.filter(asset__isnull=False)
    q = q.filter(asset__status='在用').distinct()
    q = q.values('uuid', 'name')
    return create_success_dict(data={'records': model_list_to_dict(q)})


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('asset_log')
def list_current(request, *args, **kwargs):
    if request.method == 'GET':
        q = models.AssetType.objects.filter(deleted=False)
        distinct = request.GET.get('distinct')
        if distinct and models.Setting.getvalue('server_type') != 'school':
            # 前端县级下拉列表专用
            q = q.order_by().values('name').distinct()
            return create_success_dict(data={'records': model_list_to_dict(q)})
        if models.Setting.getvalue('server_type') == 'school':
            q = q.values('uuid', 'name', 'icon', 'unit_name')
            cond = None
        else:
            town_name = request.GET.get('town_name')
            school_name = request.GET.get('school_name')
            cond = {'town_name': town_name, 'school_name': school_name}
            cache.set('asset_type_list', json.dumps(cond))
            if town_name:
                q = q.filter(school__parent__name=town_name)
            if school_name:
                q = q.filter(school__name=school_name)
            q = q.order_by().values('name', 'icon', 'unit_name').distinct()
        records = format_record.asset_type_total_in_use(q, cond)
        return create_success_dict(data={'records': records})
