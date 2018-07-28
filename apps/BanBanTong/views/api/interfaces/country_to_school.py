# coding=utf-8
import base64
import bz2
import logging
from django.core import serializers
from BanBanTong.db import models
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict


logger = logging.getLogger(__name__)


def get(request):
    if request.method == 'POST':
        if models.Setting.getvalue('server_type') != 'country':
            return create_failure_dict(msg='错误的服务器级别')
        key = request.POST.get('key')
        max_created_at = request.POST.get('max_created_at')
        try:
            models.Node.objects.get(communicate_key=key)
        except:
            return create_failure_dict(msg='错误的key')
        q = models.CountryToSchoolSyncLog.objects.filter(created_at__gt=max_created_at)
        q = q.order_by('created_at')
        l = [serializers.serialize('json', [i, ]) for i in q]
        data = base64.b64encode(bz2.compress('\n'.join(l)))
        return create_success_dict(data=data)
