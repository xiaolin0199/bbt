# coding=utf-8
import logging

from BanBanTong.db import models
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import model_list_to_dict


logger = logging.getLogger(__name__)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_sync_server')
def add(request, *args, **kwargs):
    if request.method == 'POST':
        host = request.POST.get('host')
        port = request.POST.get('port')
        key = request.POST.get('key')
        # show_download_btn = request.POST.get('show_download_btn', False)
        # 根据 host port key 取得该校级服务器在上级服务器中的node_id
        node_id = models.Setting.get_node_id_from_top(host, port, key)
        if node_id:
            obj, c = models.Setting.objects.get_or_create(name='sync_node_id')
            obj.value = node_id
            obj.save()
        else:
            logger.exception('')
            return create_failure_dict(msg='获取本服务器在上级服务的NODE ID失败')

        obj, c = models.Setting.objects.get_or_create(name='sync_server_host')
        obj.value = host
        obj.save()
        obj, c = models.Setting.objects.get_or_create(name='sync_server_port')
        obj.value = port
        obj.save()
        obj, c = models.Setting.objects.get_or_create(name='sync_server_key')
        obj.value = key
        obj.save()

        # 删除token，使得服务器在同步时重新login，上级重新生成<id>.node文件
        models.Setting.objects.filter(name='sync_server_token').delete()
        return create_success_dict(msg='上级服务器设置成功！')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_sync_server')
def list_current(request, *args, **kwargs):
    if request.method == 'GET':
        names = [
            'sync_server_host',
            'sync_server_port',
            'sync_server_key']
        q = models.Setting.objects.filter(name__in=names).values()
        return create_success_dict(data=model_list_to_dict(q))


def get_settinginfo(request):
    field_name = request.GET.get('field', None)
    if not field_name:
        return create_failure_dict()
    try:
        o = models.Setting.objects.get(name=field_name)
        return create_success_dict(data={field_name: o.value})
    except models.Setting.DoesNotExist:
        return create_failure_dict()
    except Exception as e:
        return create_failure_dict(msg=str(e))
