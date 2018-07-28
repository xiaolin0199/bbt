# coding=utf-8
import json
import logging
import datetime
from autobahn.twisted import choosereactor, websocket
from twisted.internet import protocol, endpoints, task
import copy
from django.conf import settings
from BanBanTong.db import models

import ws.instructions.client
import ws.instructions.common
import ws.instructions.server
import ws.dispatchers
import ws.dbapi
import ws.cache

logger = logging.getLogger(__name__)

CLIENT = {
    'key': None,            # sync_server_port
    'host': None,           # sync_server_host
    'port': None,           # sync_server_key
    'login': False,
    'status': None,
    'connect': None,
    'factory': None,
    'sync-misc': None,      # updated after periodical_sync
    'server_type': None,    # server_type
}

SERVER = {
    'caches': {
        'node-sync-in-progress': set(),     # 正在处理同步数据的node
        'restore-data': {},                 # 回传时打包完成的数据先在这里缓存一份
    },
    'factory': None,
    'dispatchers': {},
    'server_type': None,
}
CONNECTS = {}

try:
    CONF = settings.CONF.websocket
except AttributeError:
    # 校级服务器配置项从数据库中获取, 这里这样写是为了兼容旧版本的代码
    logger.warning('use local config')

    class Conf(object):
        debug = settings.DEBUG
        wsurl = 'ws://0.0.0.0:8001'
        websocket = 'tcp:8001'
    CONF = Conf()


class WSClientProtocol(websocket.WebSocketClientProtocol):

    def onConnect(self, request):
        """接受客户端连接，初始化clients状态，获取客户端ip"""
        self.factory.log.debug('onConnect: peer=%s', request.peer)
        # self.factory.log.debug('onConnect: origin=%s path=%s', request.origin, request.path)

    def onOpen(self):
        """onConnect成功的话，就是onOpen。把消耗较大的操作放在onOpen里"""
        # self.factory.log.debug('onOpen')
        CLIENT['connect'] = self
        ws.instructions.client.login(CLIENT)

    def onMessage(self, message, isBinary):
        """接受客户端消息"""
        self.factory.log.debug('onMessage: message=%s, isBinary=%s', message, isBinary)
        if isBinary:
            self.factory.log.warning('binary message not supported')
            return

        message = message.decode('utf8')
        try:
            data = json.loads(message)
        except ValueError:
            self.factory.log.debug('invalid message format')
            self.sendClose()
            return

        if 'ret' not in data:
            self.factory.log.warning('wrong json fields. data=%s', data)
            self.sendClose()
            return
        if 'slug' in data:
            new_msg = CLIENT['dispatchers'][data['slug']].consume(self, CLIENT, data)
            if new_msg:
                self.sendMessage(new_msg)

    def onClose(self, wasClean, code, reason):
        """客户端关闭了连接"""
        CLIENT['connect'] = None
        self.factory.log.debug('onClose: wasClean=%s, code=%s, reason=%s', wasClean, code, reason)

    def sendMessage(self, payload, *args, **kw):
        if ws.cache.get_status() == 'maintain':
            self.factory.log.debug('Server in %s mode', ws.cache.get_status())
            return
        if isinstance(payload, dict):
            payload = json.dumps(payload, ensure_ascii=False).encode('utf8')
        elif isinstance(payload, unicode):
            payload = payload.encode('utf8')
        self.factory.log.debug('sendMessage: payload=%s', payload)
        websocket.WebSocketClientProtocol.sendMessage(self, payload, *args, **kw)


class WSClientFactory(websocket.WebSocketClientFactory, protocol.ReconnectingClientFactory):
    """WebSocket客户端Factory类，支持断线重连"""
    maxDelay = settings.DEBUG and 5 or 3600
    initialDelay = 5.0
    protocol = WSClientProtocol
    log = logging.getLogger('ws')

    def __init__(self, *args, **kw):
        websocket.WebSocketClientFactory.__init__(self, *args, **kw)
        server_type = ws.dbapi.blocking_get_server_type()
        CLIENT['server_type'] = server_type
        CLIENT['dispatchers'] = {slug: dispatcher() for slug, dispatcher in ws.dispatchers.DISPATCHERS.get_dispatchers(server_type).items()}
        CLIENT['factory'] = self

    def clientConnectionFailed(self, connector, reason):
        try:
            self.log.debug(u'连接失败. 原因:%s', reason)
            self.retry(connector)
        except Exception as e:
            self.log.exception(e)

    def clientConnectionLost(self, connector, reason):
        try:
            self.log.debug(u'连接丢失. 原因:%s', reason)
            self.retry(connector)
        except Exception as e:
            self.log.exception(e)

    def retry(self, connector=None):
        if ws.cache.get_status() == 'maintain':
            self.log.debug('Server in %s mode', ws.cache.get_status())
            return
        if connector is None:
            if self.connector is None:
                raise ValueError("no connector to retry")
            connector = self.connector

        CLIENT['host'] = models.Setting.getvalue('sync_server_host')
        CLIENT['port'] = int(models.Setting.getvalue('sync_server_port'))
        CLIENT['key'] = models.Setting.getvalue('sync_server_key')
        connector.host = CLIENT['host']
        connector.port = CLIENT['port']
        connector.getDestination()
        protocol.ReconnectingClientFactory.retry(self, connector)


class WSServerProtocol(websocket.WebSocketServerProtocol):

    def onConnect(self, request):
        """接受客户端连接，初始化clients状态，获取客户端ip"""
        self.transport.setTcpNoDelay(True)
        if 'x-forwarded-for' in request.headers:
            remote_ip = request.headers['x-forwarded-for']
        else:
            remote_ip = request.peer.split(':')[1]
        self.factory.log.debug('onConnect: addr=%s, origin=%s, path=%s', remote_ip, request.origin, request.path)

        try:
            dispatcher = SERVER['dispatchers'][request.path]()
            CONNECTS[self.transport.sessionno] = {
                'dispatch': dispatcher,
                'last_active_datetime': datetime.datetime.now(),
                'ip': remote_ip,
                'path': request.path,
                'connect': self,
                'properties': copy.deepcopy(dispatcher.properties),
                'sessionno': self.transport.sessionno,
                'login': False,
                'should_close': False,
                'last_message': ''
            }
        except KeyError as e:
            self.factory.log.exception('Missing dispatcher, slug=%s', request.path)
            self.sendMessage({'ret': 400, 'msg': 'Bad slug'})
            self.sendClose()

        except Exception as e:
            self.sendMessage({'ret': 500, 'msg': u'Internal Server Error. err=%s' % e})
            self.factory.log.exception(e)
        else:
            CONNECTS[self.transport.sessionno]['properties']['sync-data-length'] = 50

    def onMessage(self, message, isBinary=False):
        """接受客户端消息, 根据消息类型分发给具体的处理模块"""
        self.factory.log.debug('onMessage: message=%s, type=%s, isBinary=%s', message, type(message), isBinary)
        connect = CONNECTS[self.transport.sessionno]
        connect['last_active_datetime'] = datetime.datetime.now()
        try:
            message = message.decode('utf8')
            data = json.loads(message)
            assert isinstance(data, dict), ValueError('Bad datatype, which should be dict.')

        except UnicodeDecodeError as e:
            self.factory.log.warning('UnicodeDecodeError: e=%s, message=(%s ... %s), ', e, repr(message)[:50], repr(message)[-50:])
            self.sendMessage({'ret': 400, 'msg': str(e)})
            connect['should_close'] = True

        except ValueError as e:
            self.factory.log.warning('ValueError: e=%s,  message=(%s ... %s), ', e, repr(message)[:50], repr(message)[-50:])
            if 'Bad datatype' in str(e):
                self.sendMessage({'ret': 400, 'msg': str(e)})
                connect['should_close'] = True
            else:
                # 数据量太大, 网络环境太差导致传输分片了
                length = max(CONNECTS[self.transport.sessionno]['properties']['sync-data-length'] / 2, 16)
                self.sendMessage({'ret': 0, 'operation': 'refresh-properties', 'data': {'sync-data-length': length}})

        except Exception as e:
            connect['should_close'] = True
            self.factory.log.exception('Internal Server Error: %s', e)

        else:
            # 服务器处理客户端发送的数据
            if not ws.dispatchers.DISPATCHERS.check_category(SERVER, connect['path'], data['category']):
                self.factory.log.warning(
                    'wrong server_type/path/category server_type: %s, dispatchers=%s, path=%s, category=%s',
                    SERVER['server_type'], SERVER['dispatchers'], connect['path'], data['category']
                )
                self.sendMessage({'ret': 400, 'msg': 'Bad category, category=%s' % data.get('category')})
                connect['should_close'] = True

                server_type = ws.dbapi.blocking_get_server_type()
                SERVER['server_type'] = server_type
                SERVER['dispatchers'] = ws.dispatchers.DISPATCHERS.get_dispatchers(server_type)

            else:
                # 请求分发到具体的任务
                ret = connect['dispatch'].dispatch(connect, CONNECTS, SERVER, data)
                if ret:
                    try:
                        if 'callback' in data:
                            ret['callback'] = data['callback']
                        sendbuf = json.dumps(ret, encoding='utf8', ensure_ascii=False)
                    except Exception as e:
                        self.factory.log.exception('Data Handle Error: ret=%s, err=%s', ret, e)

                    else:
                        self.factory.log.debug('sendMessage: %s', sendbuf)
                        self.sendMessage(sendbuf)

        if connect['should_close']:
            self.sendClose()

    def onClose(self, wasClean, code, reason):
        """关闭客户端连接"""
        # self.factory.log.debug('onClose:wasClean=%s, code=%s, reason=%s', wasClean, code, reason)
        # connect = CONNECTS.get(self.transport.sessionno)
        # if connect:
        #     communicate_key = connect['properties'].get('key')
        #     if communicate_key:
        #         self.factory.log.debug('Node.last_active_time update: %s', communicate_key)
        #         models.Node.objects.filter(communicate_key=communicate_key).update(last_active_time=datetime.datetime.now())
        if self.transport.sessionno in CONNECTS:
            del CONNECTS[self.transport.sessionno]

    def onPong(self, data):
        """
        在心跳检测时，服务器向发呆的客户端发送ping。
        如果这里收到pong，说明客户端在线，就更新last_active_datetime
        """
        CONNECTS[self.transport.sessionno]['last_active_datetime'] = datetime.datetime.now()
        node = CONNECTS[self.transport.sessionno]['properties'].get('node')
        if node:
            ws.cache.set_online(node.pk)

    def sendMessage(self, payload, *args, **kw):
        if isinstance(payload, dict):
            payload = json.dumps(payload, ensure_ascii=False).encode('utf8')
        elif isinstance(payload, unicode):
            payload = payload.encode('utf8')
        websocket.WebSocketServerProtocol.sendMessage(self, payload, *args, **kw)


class WSServerFactory(websocket.WebSocketServerFactory):
    maxDelay = 15
    initialDelay = 15
    protocol = WSServerProtocol
    log = logging.getLogger('ws')

    def __init__(self, *args, **kw):
        websocket.WebSocketServerFactory.__init__(self, *args, **kw)
        server_type = ws.dbapi.blocking_get_server_type()
        SERVER['factory'] = self
        SERVER['server_type'] = server_type
        SERVER['dispatchers'] = ws.dispatchers.DISPATCHERS.get_dispatchers(server_type)


def start_server():
    logger.info('Running on reactor.\nInfo:wsurl=%s, tcpurl=%s', CONF.wsurl, CONF.websocket)
    reactor = choosereactor.install_reactor()
    wsfactory = WSServerFactory(CONF.wsurl)
    wsserver = endpoints.serverFromString(reactor, CONF.websocket)

    task.LoopingCall(ws.instructions.server.check_heartbeat, CONNECTS).start(15)
    task.LoopingCall(ws.instructions.common.ping_mysql).start(15)
    wsserver.listen(wsfactory)
    reactor.run()


def start_client():
    logger.info('start_client')
    host, port, key = ws.dbapi.blocking_get_sync_host_port_key()
    CLIENT['host'] = host
    CLIENT['port'] = port
    CLIENT['key'] = key
    wsurl = 'ws://%s:%s/ws/sync' % (host, port)
    reactor = choosereactor.install_reactor()
    logger.info('Running on reactor. Upstream:wsurl=%s', wsurl)
    wsfactory = WSClientFactory(wsurl)
    task.LoopingCall(ws.instructions.client.periodical_sync_data, CLIENT).start(settings.DEBUG and 15 or 180)  # 3min
    task.LoopingCall(ws.instructions.client.periodical_sync_cache, CLIENT).start(15)
    task.LoopingCall(ws.instructions.client.periodical_sync_misc, CLIENT).start(settings.DEBUG and 15 or 1800)  # 30min
    websocket.connectWS(wsfactory)
    reactor.run()
