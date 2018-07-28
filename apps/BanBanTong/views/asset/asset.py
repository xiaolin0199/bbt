#!/usr/bin/env python
# coding=utf-8
'''资产申报'''
import json
import logging
import os
import traceback
import uuid
import django.db
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db.models import Sum
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.forms.asset import AssetForm
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import get_page_info
from BanBanTong.utils import model_list_to_dict
from BanBanTong.utils import model_to_dict
import xlwt


logger = logging.getLogger(__name__)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('asset_log')
def add(request, *args, **kwargs):
    if request.method == 'POST':
        record = AssetForm(request.POST)
        if record.is_valid():
            asset = record.save(commit=False)
            asset.school = models.Group.objects.get(group_type='school')
            asset.reported_by = request.current_user.username
            try:
                asset.save()
            except django.db.DataError, e:
                # print dir(e)
                if 'Out of range value' in str(e):
                    return create_failure_dict(msg=u'申报数目过大', debug=str(e))
                return create_failure_dict(msg=str(e), debug=str(e))
            except StandardError, e:
                # print type(e), dir(e)
                # print e.args
                # print e.message
                return create_failure_dict(msg='StandardError', debug=str(e))

            # 插入一条申报记录
            log = models.AssetLog()
            town = asset.school.parent
            town_name = town.name
            if town.group_type != 'town':
                town = None
                town_name = ''
            log.town = town
            try:
                country_name = town.parent.name
            except:
                country_name = ''
            log.country_name = country_name
            log.town_name = town_name
            log.school = asset.school
            log.school_name = asset.school.name
            log.log_type = '新增'
            log.asset_type = asset.asset_type
            log.asset_from = asset.asset_from
            log.device_model = asset.device_model
            log.number = asset.number
            log.reported_by = asset.reported_by
            log.remark = asset.remark
            log.save()

            return create_success_dict(msg='成功申报资产！',
                                       data=model_to_dict(asset))
        return create_failure_dict(msg='申报资产失败！', errors=record.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('asset_log')
def aggregate(request, *args, **kwargs):
    if request.method == 'GET':
        cache.set('asset_list', json.dumps(request.GET))
        q, title = list_query(request.GET)
        page_info = get_page_info(request)
        #paginator = Paginator(q, page_info['page_size'])
        paginator = Paginator(q, 15)
        records = list(paginator.page(page_info['page_num']).object_list)
        return create_success_dict(data={
            'page': page_info['page_num'],
            'page_count': paginator.num_pages,
            'page_size': 15,
            'record_count': paginator.count,
            'records': records,
        })
        # return create_success_dict(data={'records': model_list_to_dict(q)})


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('asset_log')
def delete(request, *args, **kwargs):
    if request.method == 'POST':
        asset_uuid = request.POST['uuid']
        number = request.POST['number']
        try:
            a = models.Asset.objects.get(uuid=asset_uuid)
            number = int(number)
            if number > a.number:
                return create_failure_dict(msg='停用数量超过批次数量！')
            else:
                # 查找关联的停用记录
                if not models.Asset.objects.filter(related_asset=a).exists():
                    r = models.Asset.objects.create(related_asset=a,
                                                    asset_type=a.asset_type,
                                                    school=a.school,
                                                    device_model=a.device_model,
                                                    number=number,
                                                    asset_from=a.asset_from,
                                                    reported_by=a.reported_by,
                                                    reported_at=a.reported_at,
                                                    status=u'停用',
                                                    remark=a.remark)
                else:
                    r = models.Asset.objects.get(related_asset=a)
                    r.number += number
                    r.save()
                a.number -= number
                if a.number == 0:
                    a.delete()
                else:
                    a.save()
                # 插入一条申报记录
                log = models.AssetLog()
                try:
                    town = models.Group.objects.get(group_type='town')
                    town_name = town.name
                except:
                    town = None
                    town_name = ''
                try:
                    country_name = town.parent.name
                except:
                    country_name = ''
                school = models.Group.objects.get(group_type='school')
                log.country_name = country_name
                log.town = town
                log.town_name = town_name
                log.school = school
                log.school_name = school.name
                log.log_type = '停用'
                log.asset_from = r.asset_from
                log.asset_type = r.asset_type
                log.device_model = r.device_model
                log.number = number
                log.reported_by = r.reported_by
                log.remark = r.remark
                log.save()
                return create_success_dict(msg='停用申报成功！')
        except:
            traceback.print_exc()
            return create_failure_dict(msg='错误的批次！')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('asset_log')
def export(request, *args, **kwargs):
    c = cache.get('asset_list')
    if not c:
        return create_failure_dict(msg='查询超时无法导出，请重新查询！')
    cond = json.loads(c)
    q, title = list_query(cond)
    xls = xlwt.Workbook(encoding='utf8')
    sheet = xls.add_sheet(title)
    header = ['街道乡镇', '学校', '申报时间', '资产状态', '资产类型',
              '设备型号', '数量', '设备来源', '申报用户', '备注']
    for i in range(len(header)):
        sheet.write(0, i, header[i])
    row = 1
    for record in q:
        sheet.write(row, 0, record['asset_type__school__parent__name'])
        sheet.write(row, 1, record['asset_type__school__name'])
        sheet.write(row, 2, record['reported_at'])
        sheet.write(row, 3, record['status'])
        sheet.write(row, 4, record['asset_type__name'])
        sheet.write(row, 5, record['device_model'])
        sheet.write(row, 6, record['number'])
        sheet.write(row, 7, record['asset_from'])
        sheet.write(row, 8, record['reported_by'])
        sheet.write(row, 9, record['remark'])
        row += 1
    cached_id = str(uuid.uuid1())
    tmp_file = os.path.join(constants.CACHE_TMP_ROOT, cached_id)
    xls.save(tmp_file)
    filename = u'%s.xls' % title
    return create_success_dict(url=reverse('base:xls_download',
                                           kwargs={'cached_id': cached_id,
                                                   'name': filename}))


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('asset_log')
def get_devicemodel_by_assettype(request, *args, **kwargs):
    uu = request.GET.get('uuid')
    try:
        q = models.Asset.objects.filter(asset_type__uuid=uu)
        q = q.values('device_model').distinct()
        return create_success_dict(data={'records': model_list_to_dict(q)})
    except:
        logger.exception('')


def list_query(cond):
    try:
        name = cond.get('name')
        asset_type_uuid = cond.get('asset_type_uuid')
        country_name = cond.get('country_name')
        town_name = cond.get('town_name')
        school_name = cond.get('school_name')
        status = cond.get('status')
        year = cond.get('year')
        reported_by = cond.get('reported_by')
        device_model = cond.get('device_model')
        remark = cond.get('remark')

        title = u'资产批次'
        q = models.Asset.objects.all()
        if name:
            q = q.filter(asset_type__name=name)
        if asset_type_uuid:
            asset_type = models.AssetType.objects.get(uuid=asset_type_uuid)
            q = q.filter(asset_type=asset_type)
        if country_name:
            q = q.filter(school__parent__parent__name=country_name)
        if town_name:
            q = q.filter(school__parent__name=town_name)
        if school_name:
            q = q.filter(school__name=school_name)
        if status:
            q = q.filter(status=status)
        if year:
            q = q.filter(reported_at__year=int(year))
            #title = year
        if reported_by:
            q = q.filter(reported_by__contains=reported_by)
        if device_model:
            q = q.filter(device_model__contains=device_model)
        if remark:
            q = q.filter(remark__contains=remark)
        q = q.values('uuid',
                     'asset_type__school__parent__parent__name',
                     'asset_type__school__parent__name',
                     'asset_type__school__name',
                     'asset_type__name', 'device_model',
                     'asset_from',
                     'reported_by', 'reported_at', 'status',
                     'remark')
        q = q.annotate(number=Sum('number'))
        q = q.order_by('-status', '-reported_at')
        return q, title
    except:
        logger.exception('')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('asset_log')
def list_current(request, *args, **kwargs):
    if request.method == 'GET':
        cache.set('asset_list', json.dumps(request.GET))
        q, title = list_query(request.GET)
        page_info = get_page_info(request)
        #paginator = Paginator(q, page_info['page_size'])
        paginator = Paginator(q, 15)
        records = list(paginator.page(page_info['page_num']).object_list)
        return create_success_dict(data={
            'page': page_info['page_num'],
            'page_count': paginator.num_pages,
            'page_size': 15,
            'record_count': paginator.count,
            'records': records,
        })
