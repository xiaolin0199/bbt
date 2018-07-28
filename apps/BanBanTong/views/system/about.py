# coding=utf-8
import ConfigParser
import logging
import platform
from BanBanTong.db import models
from BanBanTong import constants
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator


logger = logging.getLogger(__name__)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_about')
def about(request, *args, **kwargs):
    system = platform.system()
    path = constants.BANBANTONG_VERSION_FILE
    config_file = ConfigParser.RawConfigParser()
    config_file.read(path)
    major = config_file.get('Version', 'Version number')
    minor = config_file.get('Version', 'svn')
    version = '%s %s.%s' % (system, major, minor)
    return create_success_dict(data={
        'version': version,
    })


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_activation')
def activation(request, *args, **kwargs):
    # 校 (学校名称/分配终端数)
    # 县 (产品名称/授权状态/授权终端数量/授权年限)
    server_type = models.Setting.getvalue('server_type')
    data = {'server_type': server_type}

    if server_type == 'school':
        # school_name = models.Group.objects.get(group_type='school').name
        pass

    elif server_type == 'country':
        pass

    return create_success_dict(data=data)
