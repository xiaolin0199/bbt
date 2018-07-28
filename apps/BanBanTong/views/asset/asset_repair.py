#!/usr/bin/env python
# coding=utf-8
'''资产管理>资产维修管理'''
import datetime
import json
import os
import traceback
import uuid
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.utils.dateparse import parse_date
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.forms.asset import AssetRepairForm
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import get_page_info
from BanBanTong.utils import model_to_dict
import xlwt


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('asset_repair')
def add(request, *args, **kwargs):
    """资产报修"""
    # TODO 2015-03-23
    # 表单添加字段
    # 所属位置（常规教室（年级，班级，其他（文本框手动输入））

    if models.Setting.getvalue('server_type') != 'school':
        return
    if request.method == 'POST':
        try:
            record = AssetRepairForm(request.POST)
            if record.is_valid():
                a = record.save(commit=False)
                a.reported_by = request.current_user.username
                school = models.Group.objects.get(group_type='school')
                a.school = school
                a.school_name = school.name
                town, town_name = school.get_town()
                a.town = town
                a.town_name = town_name
                a.country_name = school.get_country_name()
                a.save(force_insert=True)
                data = model_to_dict(a)
                data['asset_type__name'] = data['asset_type']['name']
                return create_success_dict(msg='资产报修成功！',
                                           data=data)
            return create_failure_dict(msg='资产报修失败！',
                                       errors=record.errors)
        except:
            traceback.print_exc()


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('asset_repair')
def export(request, *args, **kwargs):
    c = cache.get('asset_repair_list')
    if not c:
        return create_failure_dict(msg='查询超时无法导出，请重新查询！')
    cond = json.loads(c)
    title, q = list_query(cond)
    xls = xlwt.Workbook(encoding='utf8')
    sheet = xls.add_sheet(title)
    header = ['区县市', '街道乡镇', '学校', '报修时间', '资产类型',
              '设备型号', '年级', '班级', '申报用户', '备注']
    for i in range(len(header)):
        sheet.write(0, i, header[i])
    row = 1
    for record in q:
        sheet.write(row, 0, record['country_name'])
        sheet.write(row, 1, record['town_name'])
        sheet.write(row, 2, record['school_name'])
        sheet.write(row, 3, str(record['reported_at']))
        sheet.write(row, 4, record['asset_type__name'])
        sheet.write(row, 5, record['device_model'])
        sheet.write(row, 6, record['grade_name'])
        sheet.write(row, 7, record['class_name'])
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
@decorator.authorized_privilege('asset_repair')
def list_current(request, *args, **kwargs):
    """资产管理>资产维修管理"""
    # TODO 2015-03-23
    # 添加字段
    # 所属位置
    # 修改API文档
    if request.method == 'GET':
        page_info = get_page_info(request)
        cache.set('asset_repair_list', json.dumps(request.GET))
        title, q = list_query(request.GET)
        paginator = Paginator(q, page_info['page_size'])
        records = list(paginator.page(page_info['page_num']).object_list)
        return create_success_dict(data={
            'page': page_info['page_num'],
            'page_count': paginator.num_pages,
            'page_size': page_info['page_size'],
            'record_count': paginator.count,
            'records': records,
        })


def list_query(cond):
    start_date = cond.get('start_date')
    end_date = cond.get('end_date')
    grade_name = cond.get('grade_name')
    class_name = cond.get('class_name')
    reported_by = cond.get('reported_by')
    asset_type = cond.get('asset_type')
    device_model = cond.get('device_model')
    remark = cond.get('remark')
    country_name = cond.get('country_name')
    town_name = cond.get('town_name')
    school_name = cond.get('school_name')
    q = models.AssetRepairLog.objects.all()
    title = u'资产维修管理'
    if start_date and end_date:
        s = parse_date(start_date)
        e = parse_date(end_date) + datetime.timedelta(days=1)
        q = q.filter(reported_at__range=(s, e))
        # title = '%s-%s' % (start_date.replace('-', ''),
        #                   end_date.replace('-', ''))
    if grade_name:
        q = q.filter(grade_name=grade_name)
    if class_name:
        q = q.filter(class_name=class_name)
    if reported_by:
        q = q.filter(reported_by__contains=reported_by)
    if asset_type:
        q = q.filter(asset_type__name=asset_type)
    if device_model:
        q = q.filter(device_model__contains=device_model)
    if remark:
        q = q.filter(remark__contains=remark)
    if country_name:
        q = q.filter(country_name=country_name)
    if town_name:
        q = q.filter(town_name=town_name)
    if school_name:
        q = q.filter(school_name=school_name)
    q = q.values('uuid', 'reported_at', 'reported_by',
                 'asset_type__name', 'device_model',
                 'country_name',
                 'town_name',
                 'school_name',
                 'grade_name',
                 'class_name', 'remark').order_by('-reported_at')
    return title, q
