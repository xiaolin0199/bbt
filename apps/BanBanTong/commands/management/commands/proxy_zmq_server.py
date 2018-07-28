#!/usr/bin/env python
# coding=utf-8

import os
import sys
import time
import logging
import traceback
import ConfigParser
import socket
import threading
import select
import struct
import hashlib
import signal
import zmq
import bson
import cPickle as pickle
from django.core.management.base import BaseCommand
from BanBanTong import constants
from BanBanTong.db import models

c = None
s = None
subscriber = None
zmq_host = 'tcp://0.0.0.0:%s' % (constants.BANBANTONG_ZMQ_PORT)  # bind_to , connect_to

logger = logging.getLogger(__name__)


def start_publisher():
    '''
        PUB发布端服务
    '''
    global c, s
    print 'starting zmq publisher'
    if not c:
        c = zmq.Context()
    if not s:
        s = c.socket(zmq.PUB)
        try:
            s.bind(zmq_host)
        except zmq.ZMQError:
            pass
        except:
            logger.exception('')

    print 'zmq socket started'


def send_msg(*args, **kwargs):
    '''
        推送指令 (关机, 播放视频)
    '''
    global s

    type = kwargs.get('type', '')
    delay = kwargs.get('delay', '30')
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
                b = bson.BSON.encode({'messagetype': 'shutdown', 'delay': delay})
            elif type == 'reboot':
                b = bson.BSON.encode({'messagetype': 'reboot', 'delay': delay})
            elif type == 'play-video':
                if filename:
                    b = bson.BSON.encode({'messagetype': 'video-broadcast', 'filename': filename})
                else:
                    continue

            buf = str(mac) + '\0' + b

            s.send(buf)

            time.sleep(0.1)

    except KeyboardInterrupt:
        pass


class Command(BaseCommand):

    def handle(self, *args, **options):
        # TCP套接字
        self.srvsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srvsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srvsock.bind(('0.0.0.0', 9528))
        self.srvsock.listen(100)

        # 启动PUB端发布服务 (9527)
        start_publisher()
        # 开始监听ZMQ代理程序 (9528)
        while True:
            # 阻塞，等待连接
            connection, address = self.srvsock.accept()

            try:
                # connection.settimeout(5)
                buf = connection.recv(102400)

                if buf:
                    try:
                        type, delay, macfilter = buf.split('###')
                        macfilter = pickle.loads(macfilter)
                        # 推入PUB
                        send_msg(type=type, delay=delay, macfilter=macfilter)
                    except:
                        connection.send('pickle error!')
                else:
                    connection.send('buf is not be null')
            except socket.timeout:
                print 'time out'

            connection.close()

        # 关闭服务器套接字
        self.srvsock.close()
