#!/usr/bin/env python
# coding=utf-8
import datetime
import time
import random
import threading
import requests
import MySQLdb
import traceback
import uuid
import os
import multiprocessing

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_date
from django.utils.dateparse import parse_time

from BanBanTong.db import models

# 校服务器
SERVER_HOST = 'localhost:8000'

RESOURCE_FROM = [
    u'中央电化教育馆教学资源库',
    u'互联网资源',
    u'课内网资源',
    u'国家基础教育资源网',
    u'优课网资源',
    u'凯瑞教学资源',
    u'电信网教育资源',
    u'教材配套自带',
    u'农村中小学现代远程教育资源',
    u'教学点数字教育资源全覆盖',
    u'自制课件',
    u'其他资源'
]

RESOURCE_TYPE = [
    u'音频',
    u'音视频',
    u'PPT幻灯片',
    u'文档',
    u'动画片',
    u'互动课件',
    u'其他'
]


class Command(BaseCommand):

    def _get_mac_status(self, mac):
        data = {
            'mac': mac
        }
        url = u'http://%s/api/get_mac_status/' % (SERVER_HOST)

        print mac, url
        ret = requests.get(url, params=data, timeout=60)
        ret = ret.json()

        return ret

    def _get_lesson_status(self, mac):
        data = {
            'mac': mac
        }
        url = u'http://%s/api/lesson/status/' % (SERVER_HOST)

        print mac, url
        ret = requests.get(url, params=data, timeout=60)
        ret = ret.json()

        return ret

    def _get_server_settings(self, mac):
        data = {
            'mac': mac
        }
        url = u'http://%s/api/server_settings/' % (SERVER_HOST)

        print mac, url
        ret = requests.get(url, params=data, timeout=60)
        ret = ret.json()

        return ret

    def _get_syllabus_content(self, mac, lesson_name):
        data = {
            'mac': mac,
            'lesson_name': lesson_name
        }
        url = u'http://%s/api/lesson/syllabus-content/' % (SERVER_HOST)

        # print mac , lesson_name , url
        ret = requests.get(url, params=data, timeout=60)
        ret = ret.json()

        return ret

    def _start_lesson_status(self, token):
        data = {
            'token': token
        }

        url = u'http://%s/api/lesson/start_status/' % (SERVER_HOST)

        print token, url
        ret = requests.get(url, params=data, timeout=60)
        ret = ret.json()

        return ret

    def _start_lesson(self, data):
        data = data

        url = u'http://%s/api/lesson/start/' % (SERVER_HOST)

        print url
        ret = requests.get(url, params=data, timeout=60)
        ret = ret.json()

        return ret

    def _upload_screen(self, mac, pic):
        data = {
            'mac': mac
        }

        files = {
            'pic': pic
        }

        url = u'http://%s/api/screen-upload/' % (SERVER_HOST)

        print mac, url
        ret = requests.post(url, data=data, files=files, timeout=60)
        ret = ret.json()

        return ret

    def cala_seconds(self, time):
        '''
            计算time字段的总秒数
        '''
        return time.hour * 3600 + time.minute * 60 + time.second

    def worker(self, mac, lock):
        # lock.acquire()

        started = False
        token = ''
        start_screen_date = datetime.datetime.now()
        while True:
            try:
                try:
                    a = self._get_mac_status(mac)
                    reported = a['data']['reported']
                except Exception as e:
                    reported = None
                if reported:
                    # 申报后开始持续获取 lesson 状态
                    b = self._get_lesson_status(mac)

                    # 没有课了
                    if 'data' not in b:
                        continue

                    # 获取lesson status
                    if 'current_lesson' in b['data']:
                        lesson = b['data']['current_lesson']
                    elif 'next_lesson' in b['data']:
                        lesson = b['data']['next_lesson']
                        started = False
                    else:
                        lesson = None
                        started = False

                    if lesson and not started:
                        if not token:
                            c = self._get_server_settings(mac)
                            # 获取teacher的uuid
                            teacher = lesson['teacher']
                            if c['data']['teacher']:
                                teacher_uuid = c['data']['teacher'][0]['key']
                            else:
                                continue

                            # 获取大纲，并随机选择一个
                            lessoncontent = None
                            f = self._get_syllabus_content(mac, lesson['lesson_name'])
                            if f['status'] == 'success':
                                records = f['data']['records']
                                if records:
                                    lessoncontent = random.choice(records)['id']

                            data = {
                                'username': teacher_uuid,
                                'password': lesson['password'],
                                'mac': mac,
                                'lesson_name': lesson['lesson_name'],
                                'resource_from': random.choice(RESOURCE_FROM),
                                'resource_type': random.choice(RESOURCE_TYPE)
                            }
                            if lessoncontent:
                                data.update({'lessoncontent': lessoncontent})

                            # 点击上课
                            d = self._start_lesson(data)
                            # 如果已经上课
                            if d['data']['started']:
                                started = True
                                token = ''
                            else:
                                if 'token' in d['data']:
                                    token = d['data']['token']

                        else:
                            now_time = datetime.datetime.now().time()
                            start_time = parse_time(lesson['start_datetime'])
                            # 倒计时
                            #time.sleep(self.cala_seconds(start_time) - self.cala_seconds(now_time))
                            if now_time >= start_time:
                                e = self._start_lesson_status(token)
                                try:
                                    if e['data']['started']:
                                        started = True
                                        token = ''
                                except Exception as e:
                                    started = False
                                    token = ''

                    # 上课状态还需要每隔5分钟截屏一次
                    if started:
                    # if False:
                        now = datetime.datetime.now()
                        if now - start_screen_date >= datetime.timedelta(seconds=300):
                            start_screen_date = now
                            # 上课之后还要开始截屏
                            file_name = '%s.png' % (mac)
                            cmd = 'scrot %s' % (file_name)
                            v = os.system(cmd)

                            if v == 0:
                                with open(file_name, 'rb') as f:
                                    self._upload_screen(mac, f.read())

                time.sleep(15)
            except:
                print traceback.print_exc()

        # lock.release()

    def handle(self, *args, **options):
        #server_type = models.Setting.getvalue('server_type')
        #host = models.Setting.getvalue('host')
        #port = models.Setting.getvalue('port')

        # if server_type != 'school':
        #    return

        global SERVER_HOST

        if len(args) != 8:
            print 'args参数需要提供 终端数量(数据库中的起点和数量),校服务器IP及PORT;数据库名,端口，帐号及密码，线程|进程; 以空格分隔 \n'
            print 'python manage.py test_big_school_client 0 100 xx.xx.xx.xx:8000 banbantong 3100 root oseasydads_db [thread|proc]'
            return

        limit_start = args[0]
        limit = args[1]

        SERVER_HOST = args[2]

        host, port = SERVER_HOST.split(':')

        db_name = args[3]
        db_port = int(args[4])
        user = args[5]
        passwd = args[6]
        mode = args[7]

        ############  为没有申报的班级自动申报  ##################
        conn = MySQLdb.connect(host=host, port=db_port, user=user,
                               passwd=passwd, db=db_name, charset='utf8')
        cursor = conn.cursor()

        sql = """SELECT  `mac` FROM  `db_classmacv2` LIMIT %s , %s"""  % (limit_start, limit)

        cursor.execute(sql)
        macs = cursor.fetchall()
        # 如果还没有班级申报，这里自动为其做申报
        if len(macs) < int(limit_start + limit):
            count = 0

            sql = """SELECT uuid FROM Class"""
            cursor.execute(sql)
            for i in cursor.fetchall():
                class_uuid = i[0]

                # 如果已有mac则跳过
                sql = """SELECT * FROM  `db_classmacv2` where class_uuid='%s'"""  % class_uuid
                cursor.execute(sql)
                if cursor.fetchall():
                    continue

                # 生成1个随机的MAC
                mac = '-'.join([''.join(random.sample('0123456789ABCDEF', 2)) for i in range(6)])
                # 生成一个随机的UUID
                u = str(uuid.uuid1()).upper()
                # 申报
                sql = """insert into db_classmacv2 (uuid, class_uuid, mac, ip) values (%s, %s, %s, %s)"""
                parm = (u, class_uuid, mac, '')
                cursor.execute(sql, parm)
                conn.commit()
                ######
                count += 1
                if count >= int(limit_start + limit) - len(macs):
                    break
            # 再次获取MACS
            sql = """SELECT  `mac` FROM  `db_classmacv2` LIMIT %s , %s"""  % (limit_start, limit)
            cursor.execute(sql)
            macs = cursor.fetchall()

        cursor.close()
        conn.close()
        ##############   End   #######################

        if mode == 'thread':
            lock = threading.Lock()
            # 启动线程
            threads = []

            for i in range(len(macs)):
                t = threading.Thread(target=self.worker, args=(macs[i][0], lock,))
                t.start()
                threads.append(t)
                time.sleep(0.5)

            for t in threads:
                t.join()

        elif mode == 'proc':
            lock = multiprocessing.Lock()
            # 启动进程
            procs = []

            for i in range(len(macs)):
                p = multiprocessing.Process(target=self.worker, args=(macs[i][0], lock,))
                p.start()
                procs.append(p)
                time.sleep(1)

            for p in procs:
                p.join()
