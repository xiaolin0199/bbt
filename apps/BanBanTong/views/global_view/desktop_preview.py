#!/usr/bin/env python
# coding=utf-8
import datetime
from BanBanTong.db import models
from BanBanTong.utils import decorator
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import format_record
from BanBanTong.utils import paginatoooor
from django.conf import settings
DEBUG = settings.DEBUG
del settings


def _get_globalpreviews(uuid, only_computerclass=False):
    now = datetime.datetime.now()
    dt = now - datetime.timedelta(minutes=14)
    q = models.DesktopGlobalPreview.objects.filter(pic__created_at__gt=dt)
    if not models.Grade.is_computerclass(uuid):
        try:
            school = models.Group.objects.get(uuid=uuid)
            q = q.filter(pic__school=school)
            try:
                term = models.Term.get_current_term_list(school)[0]
            except:
                return (False, '当前时间不在任何学期内')
            q = q.filter(pic__grade__term=term)
        except:
            try:
                grade = models.Grade.objects.get(uuid=uuid)
                q = q.filter(pic__grade=grade)
            except:
                return (False, '错误的UUID')

        if only_computerclass:
            lst = models.DesktopGlobalPreviewTag.get_lst()
            q = q.filter(uuid__in=lst)
    else:
        d = models.DesktopGlobalPreviewTag.get_lst()
        q = q.filter(uuid__in=d)

    q = q.order_by('pic__grade_number', 'pic__class_number')
    q = q.values('pic__grade__name', 'pic__class_uuid__name',
                 'pic__lesson_name', 'pic__teacher_name',
                 'pic__lesson_period_sequence',
                 'pic__host', 'pic__url', 'uuid')
    records = format_record.global_desktop_preview(q)
    return (True, records)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('global_desktop_preview')
def realtime(request, *args, **kwargs):
    """实时概况>班班通桌面预览"""
    node = request.GET.get('uuid', None)
    if not node:
        return create_failure_dict(msg='未获取到获取节点信息')

    only_computerclass = False
    is_ok, records = _get_globalpreviews(node, only_computerclass)
    if is_ok:
        return paginatoooor(request, records)

    return create_failure_dict(msg=records,
                               data={'page_count': 1, 'page': 1,
                                     'page_size': 4, 'record_count': 0,
                                     'records': []})


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('global_desktop_preview')
def computerclass_realtime(request, *args, **kwargs):
    """实时概况>电脑教室桌面预览"""
    node = request.GET.get('uuid', None)
    if not node:
        return create_failure_dict(msg='未获取到获取节点信息')

    only_computerclass = True
    is_ok, records = _get_globalpreviews(node, only_computerclass)
    if is_ok:
        return paginatoooor(request, records)

    return create_failure_dict(msg=records)
