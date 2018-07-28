#!/usr/bin/env python
# coding=utf-8
'''资产管理->申报记录查询'''
import datetime
import json
import os
import traceback
import uuid
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.utils.dateparse import parse_date
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.db import utils as db_utils
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import get_page_info
from BanBanTong.utils import model_list_to_dict
import xlwt


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('asset_report_log')
def export(request, *args, **kwargs):
    c = cache.get('asset_log')
    if not c:
        return create_failure_dict(msg='查询超时无法导出，请重新查询！')
    cond = json.loads(c)
    q, title = list_query(cond)
    xls = xlwt.Workbook(encoding='utf-8')
    sheet = xls.add_sheet(title)
    header = ['区县市', '街道乡镇', '学校', '申报时间', '申报类型',
              '资产类型', '设备型号', '数量', '资产来源',
              '申报用户', '备注']
    for i in range(len(header)):
        sheet.write(0, i, header[i].decode('utf-8'))
    row = 1
    for record in q:
        sheet.write(row, 0, record['country_name'])
        sheet.write(row, 1, record['town_name'])
        sheet.write(row, 2, record['school_name'])
        sheet.write(row, 3, str(record['reported_at']))
        sheet.write(row, 4, record['log_type'])
        sheet.write(row, 5, record['asset_type__name'])
        sheet.write(row, 6, record['device_model'])
        sheet.write(row, 7, record['number'])
        sheet.write(row, 8, record['asset_from'])
        sheet.write(row, 9, record['reported_by'])
        sheet.write(row, 10, record['remark'])
        row += 1
    cached_id = str(uuid.uuid1())
    tmp_file = os.path.join(constants.CACHE_TMP_ROOT, cached_id)
    xls.save(tmp_file)
    filename = u'%s.xls' % title
    return create_success_dict(url=reverse('base:xls_download',
                                           kwargs={'cached_id': cached_id,
                                                   'name': filename}))


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('asset_report_log')
def list_current(request, *args, **kwargs):
    if request.method == 'GET':
        try:
            page_info = get_page_info(request)
            cache.set('asset_log', json.dumps(request.GET))
            q, title = list_query(request.GET)
            page_data = db_utils.pagination(q, **page_info)
            ret = create_success_dict(data={
                'page': page_data['page_num'],
                'page_size': page_data['page_size'],
                'record_count': page_data['record_count'],
                'page_count': page_data['page_count'],
                'records': model_list_to_dict(page_data['records'])
            })
            return ret
        except StandardError:
            traceback.print_exc()


def list_query(cond):
    try:
        start_date = cond.get('start_date')
        end_date = cond.get('end_date')
        log_type = cond.get('log_type')
        asset_type = cond.get('asset_type')
        asset_from = cond.get('asset_from')
        device_model = cond.get('device_model')
        remark = cond.get('remark')
        reported_by = cond.get('reported_by')
        country_name = cond.get('country_name')
        town_name = cond.get('town_name')
        school_name = cond.get('school_name')
        q = models.AssetLog.objects.all()
        title = u'资产申报记录查询'
        if start_date and end_date:
            s = parse_date(start_date)
            e = parse_date(end_date)
            s = datetime.datetime.combine(s, datetime.time.min)
            e = datetime.datetime.combine(e, datetime.time.max)
            q = q.filter(reported_at__range=(s, e))
            # title = '%s-%s' % (start_date.replace('-', ''),
            #                   end_date.replace('-', ''))
        if log_type:
            q = q.filter(log_type=log_type)
        if asset_type:
            q = q.filter(asset_type__name=asset_type)
        if asset_from:
            q = q.filter(asset_from=asset_from)
        if device_model:
            q = q.filter(device_model__contains=device_model)
        if remark:
            q = q.filter(remark__contains=remark)
        if reported_by:
            q = q.filter(reported_by__contains=reported_by)
        if country_name:
            q = q.filter(country_name=country_name)
        if town_name:
            q = q.filter(town_name=town_name)
        if school_name:
            q = q.filter(school_name=school_name)
        q = q.values('country_name', 'town_name', 'school_name',
                     'reported_at', 'log_type', 'asset_type__name',
                     'device_model', 'number', 'reported_by',
                     'asset_from',
                     'remark').order_by('-reported_at')
        return q, title
    except:
        traceback.print_exc()
