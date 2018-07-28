#!/usr/bin/env python
# coding=utf-8
from django.core.cache import cache
from BanBanTong.db import models
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict


def set(request):
    pk = request.POST.get('id')
    try:
        node = models.Node.objects.get(id=pk)
    except:
        return create_failure_dict(msg='错误的id')
    key = 'resync-%d-%s' % (node.id, node.communicate_key)
    cache.set(key, 'True')
    return create_success_dict()
