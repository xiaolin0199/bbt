# coding=utf-8
import logging
from BanBanTong.db import models
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import model_list_to_dict


logger = logging.getLogger(__name__)


def get_node_id(request):
    '''
        返回校服务器的NODE ID
    '''
    if request.method == 'POST':
        if models.Setting.getvalue('server_type') == 'school':
            return
        key = request.POST.get('key')
        try:
            node = models.Node.objects.get(communicate_key=key)
            return create_success_dict(data={'node_id': node.id})
        except:
            logger.exception('')
            return create_failure_dict(data={'node_id': None})


def check_data(request):
    if request.method == 'POST':
        if models.Setting.getvalue('server_type') == 'school':
            return
        key = request.POST.get('key')
        try:
            node = models.Node.objects.get(communicate_key=key)
            if node.last_upload_id > 0:
                return create_success_dict(data={'has_records': True})
            else:
                return create_success_dict(data={'has_records': False})
        except:
            logger.exception('')
            return create_failure_dict()


def get_group(request):
    types = ('province', 'city', 'country')
    q = models.Group.objects.filter(group_type__in=types)
    q = q.values()
    key = request.GET.get('key')
    try:
        school_name = models.Node.objects.get(communicate_key=key).name
    except:
        return create_failure_dict(msg='错误的key')
    try:
        school = models.Group.objects.get(name=school_name,
                                          group_type='school')
        town_name = school.parent.name
    except:
        town_name = ''
    return create_success_dict(data={'school_name': school_name,
                                     'town_name': town_name,
                                     'records': model_list_to_dict(q)})


def verify(request):
    if models.Setting.getvalue('server_type') == 'school':
        return
    if request.method == 'POST':
        key = request.POST.get('key')
        try:
            models.Node.objects.get(communicate_key=key)
            return create_success_dict()
        except Exception as e:
            logger.exception('')
            return create_failure_dict(debug=str(e))
