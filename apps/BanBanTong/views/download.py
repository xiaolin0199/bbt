# coding=utf-8
from django.conf import settings
import os
from django.http import HttpResponse
from BanBanTong import constants
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import file_utils


@decorator.file_response
def download(request, *args, **kwargs):
    name = kwargs.get('name')
    while str(name).startswith('/'):
        name = name[1:]
    if name:
        if name == 'client.zip':
            # 重新打包客户端，把最新的服务器IP打进去
            file_utils.package_client_file()
        f = os.path.join(settings.PUBLIC_ROOT, name)
        if not os.path.exists(f):
            return HttpResponse(status=404)
        return create_success_dict(path=f, name=name)


@decorator.file_response
def xls_download(request, *args, **kwargs):
    cached_id = kwargs.get('cached_id')
    while str(cached_id).startswith('/'):
        cached_id = cached_id[1:]
    if cached_id:
        tmp_file = os.path.join(constants.CACHE_TMP_ROOT, cached_id)
        if os.path.exists(tmp_file):
            name = kwargs.get('name', '%s.xls' % cached_id)
            return create_success_dict(path=tmp_file, name=name)
        return HttpResponse(status=404)
