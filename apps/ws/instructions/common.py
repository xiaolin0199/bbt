# coding=utf-8
import json
import django.db
import django.db.utils
import logging

logger = logging.getLogger(__name__)


def ping_mysql():
    '''
        ping一下数据库，防止掉线
    '''
    cursor = django.db.connection.cursor()
    try:
        cursor.execute('SELECT 1')
        cursor.close()
    except django.db.utils.OperationalError:  # MySQL断线了，关闭连接触发重连
        django.db.connection.close()


def test(client):
    logger.debug('%s.test', client)
    if not client['factory']:
        return
    sendbuf = json.dumps({'category': 'test', 'operation': 'echo', 'data': {'key': client['key'], }}, ensure_ascii=False, encoding='utf8')
    # print sendbuf, client['connect']
    # client['connect'].sendMessage(sendbuf)
    # try:
    #     client['status'] = 'test'
    # except:
    #     logger.exctption('%s.test', __name__)
