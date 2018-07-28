# coding=utf-8
import logging
# from BanBanTong.db import models
# from BanBanTong.utils import create_failure_dict
# from BanBanTong.utils import create_success_dict
# from BanBanTong.utils import model_list_to_dict


logger = logging.getLogger(__name__)


def get_node_id(request):
    # 这个api应该放在核心代码中,否则machine_time_used未安装的话,
    # 初始化安装就会报 获取上机NODEID 失败的错误.
    from BanBanTong.views.system.node import get_node_id
    return get_node_id(request)
