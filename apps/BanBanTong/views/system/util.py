#!/usr/bin/env python
# coding=utf-8
import hashlib
from django.core.cache import cache
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils.crc32 import getunsined_crc32


@decorator.authorized_user_with_redirect
def sudo(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        if hashlib.sha1(password).hexdigest() == request.current_user.password:
            cache.set('sudo', 'success')
            return create_success_dict()
        cache.delete('sudo')
        return create_failure_dict()


@decorator.authorized_user_with_redirect
def get_unlock_key(request, seed):
    if seed == 'unlock':
        key = getunsined_crc32(seed, 4)
    elif seed == 'uninstall':
        key = getunsined_crc32(seed, 6)
    else:
        return create_failure_dict(msg=u'错误的密钥类型')
    return create_success_dict(data={'key': key})
