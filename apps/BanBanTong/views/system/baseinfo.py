#!/usr/bin/env python
# coding=utf-8
from BanBanTong.utils import decorator
import BanBanTong.views.system.lesson_name
import BanBanTong.views.system.resource
import BanBanTong.views.system.term


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_baseinfo')
def term(request):
    return BanBanTong.views.system.term.list_current(request)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_baseinfo')
def lesson_name(request):
    return BanBanTong.views.system.lesson_name.list_current(request)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_baseinfo')
def resource_from(request):
    return BanBanTong.views.system.resource.resource_from(request)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_baseinfo')
def resource_type(request):
    return BanBanTong.views.system.resource.resource_type(request)
