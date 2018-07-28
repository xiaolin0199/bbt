# coding=utf-8
import base64
import bz2
import logging
import os
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import str_util
from BanBanTong.views.system.node import _backup_data
from BanBanTong.views.system.node import _backup_group
from BanBanTong.views.system.node import _backup_setting


logger = logging.getLogger(__name__)


def restore(request):
    if request.method == 'POST':
        logger.debug("restore start")
        if models.Setting.getvalue('server_type') == 'school':
            return
        key = request.POST.get('key')
        try:
            node = models.Node.objects.get(communicate_key=key)
        except:
            logger.debug('错误的communicate_key: %s', key)
            return create_failure_dict(msg='错误的key')
        try:
            f = open(os.path.join(constants.CACHE_TMP_ROOT,
                                  str(node.id) + '.node'))
        except:
            logger.debug('没有.node文件')
            return create_failure_dict(msg='上级服务器没有数据')
        uuids = [line.strip('\r\n') for line in f]
        f.close()
        data = ''
        count = 0
        logger.debug('restore --- backing up group')
        s, i = _backup_group(uuids)
        data += s
        count += i
        logger.debug('restore --- backing up data')
        s, i = _backup_data(uuids)
        data += s
        count += i
        logger.debug('restore --- backing up setting')
        data_setting = _backup_setting(node)
        logger.debug('restore --- data generated')
        # 修改密钥
        new_key = str_util.generate_node_key()
        old_key = node.communicate_key
        # print 'will update communicate_key4:', node.communicate_key, '->', new_key
        node.communicate_key = new_key
        data += data_setting.replace(old_key, new_key)
        node.last_upload_id = 0
        node.save()
        data = data.replace(old_key, new_key)
        data = bz2.compress(data)
        data = base64.b64encode(data)
        logger.debug('restore --- going to send data')
        syllabus = models.CountryToSchoolSyncLog.pack_all_data()
        return create_success_dict(data=data, syllabus=syllabus)


def restore_test(request):
    if request.method == 'POST':
        if models.Setting.getvalue('server_type') == 'school':
            return
        key = request.POST.get('key')
        if models.Node.objects.filter(communicate_key=key).exists():
            return create_success_dict()
        else:
            return create_failure_dict(msg='错误的key')
