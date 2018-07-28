#!/usr/bin/env python
# coding=utf-8
import bson
import logging
import time
import zmq
from BanBanTong import constants
from BanBanTong.db import models

context = None
socket = None
subscriber = None
zmq_host = 'tcp://0.0.0.0:%s' % (constants.BANBANTONG_ZMQ_PORT)  # bind_to , connect_to

logger = logging.getLogger(__name__)


def start_publisher():
    '''
        PUB发布端服务
    '''
    global context, socket
    print 'starting zmq publisher'
    if not context:
        context = zmq.Context()
    if not socket:
        socket = context.socket(zmq.PUB)
        try:
            socket.bind(zmq_host)
        except zmq.ZMQError:
            pass
        except:
            logger.exception('')
    print 'zmq socket started'


def send_msg(*args, **kwargs):
    '''
        推送指令 (关机, 播放视频)
    '''
    global socket

    type = kwargs.get('type', '')
    macfilter = kwargs.get('macfilter', [])
    filename = kwargs.get('filename', '')

    if not type:
        return

    if not macfilter:
        # 所有MAC
        macfilter = models.ClassMacV2.objects.all().values_list('mac', flat=True).distinct()

    try:
        for mac in macfilter:
            if type == 'shutdown':
                b = bson.BSON.encode({'messagetype': 'shutdown'})
            elif type == 'reboot':
                b = bson.BSON.encode({'messagetype': 'reboot'})
            elif type == 'play-video':
                if filename:
                    b = bson.BSON.encode({'messagetype': 'video-broadcast', 'filename': filename})
                else:
                    continue

            buf = str(mac) + '\0' + b

            socket.send(buf)
            time.sleep(0.1)

    except KeyboardInterrupt:
        pass

"""
def send_shutdown(macfilter=[]):
    '''
        推送关机指令
    '''
    global socket

    if not macfilter:
        #所有MAC
        macfilter = models.ClassMacV2.objects.all().values_list('mac', flat=True).distinct()

    try:
        for mac in macfilter:
            b = bson.BSON.encode({'messagetype': 'shutdown'})
            buf = str(mac) + '\0' + b

            socket.send(buf)
            time.sleep(0.1)

    except KeyboardInterrupt:
        pass


def send_play_video(macfilter=[], filename=None):
    '''
        推送视频播放指令
    '''
    global socket

    if not macfilter:
        #所有MAC
        macfilter = models.ClassMacV2.objects.all().values_list('mac', flat=True).distinct()

    try:
        for mac in macfilter:
            b = bson.BSON.encode({'messagetype': 'video-broadcast','filename': filename})
            buf = str(mac) + '\0' + b

            socket.send(buf)
            time.sleep(0.1)

    except KeyboardInterrupt:
        pass



def recv_msg(*args, **kwargs):
    '''
        客户端不停的监视指令
    '''
    start_subscriber()

    try:
        while True:
            msg = subscriber.recv()
            mac , cmd = msg.split('\0')
            cmd = bson.BSON.decode(cmd)
            print mac
            print cmd
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        subscriber.close()
"""


def start_subscriber():
    '''
        SUB订阅端服务
    '''
    global context, subscriber
    server_type = models.Setting.getvalue('server_type')
    # print server_type
    if not server_type:
        return
    server_name = models.Setting.getvalue(server_type)
    # print server_name
    if not server_name:
        return
    #host = models.Setting.getvalue('host')
    # if not host:
    #    return
    #sync_server_host = models.Setting.getvalue('sync_server_host')
    # print sync_server_host
    # if not sync_server_host:
    #    return
    #sync_server_key = models.Setting.getvalue('sync_server_key')
    # print sync_server_key
    # if not sync_server_key:
    #    return
    if not context:
        context = zmq.Context()

    subscriber = context.socket(zmq.SUB)
    subscriber.setsockopt_string(zmq.SUBSCRIBE, server_name)
    #subscriber.setsockopt(zmq.SUBSCRIBE, 'broadcast-message')
    subscriber.setsockopt(zmq.SUBSCRIBE, '')
    subscriber.connect(zmq_host)
