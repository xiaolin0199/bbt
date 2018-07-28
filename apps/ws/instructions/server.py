# coding=utf-8
import logging
import datetime
import ws.cache
logger = logging.getLogger(__name__)


def check_heartbeat(connects):
    '''
        每15秒检测一次所有连接：
        1. 如果连接的last_active_datetime距现在超过15秒，就发送一个ping
        2. 如果连接的last_active_datetime距现在超过60秒，就认为连接超时，关闭
    '''
    now = datetime.datetime.now()
    for k in connects.keys():
        elapsed = (now - connects[k]['last_active_datetime']).total_seconds()
        if elapsed > 60:
            connects[k]['connect'].sendClose()
        elif elapsed > 15:
            try:
                connects[k]['connect'].sendPing()
            except Exception as e:
                logger.exception(e)
                connects[k]['connect'].sendClose()
        else:
            node = connects[k]['properties'].get('node')
            if node:
                ws.cache.set_online(node.pk)
