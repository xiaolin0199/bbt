#!/usr/bin/env python
# coding=utf-8
import base64
import logging
import os
import shutil
import uuid
from django.conf import settings
from django.core.cache import cache
from django.http.response import HttpResponse
from django.template import loader
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import model_list_to_dict


logger = logging.getLogger(__name__)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('maintain')
def auth(request, *args, **kwargs):
    return create_success_dict()


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('maintain')
def index(request, *args, **kwargs):
    template = loader.get_template('maintain.html')
    return HttpResponse(template.render({}))


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('maintain')
def info(request, *args, **kwargs):
    d = {}
    # 缓存使用状况
    d['classes_last_active_time'] = cache.get('classes_last_active_time')
    d['classes'] = cache.get('classes')
    # 数据库状态
    q = models.Setting.objects.all()
    d['setting'] = model_list_to_dict(q)
    if models.Setting.getvalue('server_type') == 'school':
        q = models.Group.objects.all()
        d['group'] = model_list_to_dict(q)
    q = models.SyncLog.objects.count()
    d['synclog_count'] = q
    return create_success_dict(data=d)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('maintain')
def log(request, *args, **kwargs):
    log_type = request.GET.get('log_type')
    if not log_type:
        return
    if log_type == '1':
        filename = 'debug.log'
    elif log_type == '2':
        filename = 'errors.log'
    elif log_type == '3':
        filename = 'settings.log'
    try:
        f = open(os.path.join(constants.LOG_PATH, filename))
        if log_type == '3':
            content = f.read()
            lines = base64.b64decode(content)
        else:
            lines = f.readlines()
        f.close()
        return create_success_dict(data={'lines': lines})
    except:
        logger.exception('')
        return create_failure_dict()


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('maintain')
def log_download(request, *args, **kwargs):
    cached_id = str(uuid.uuid1())
    tmp_file = os.path.join(settings.PUBLIC_ROOT, cached_id)
    log_dir = constants.LOG_PATH
    ret = shutil.make_archive(tmp_file, 'bztar', log_dir)
    return create_success_dict(url='/download/%s' % os.path.basename(ret))
