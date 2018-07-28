# coding=utf-8
import json
import logging
import urllib
import urllib2
import traceback
from django.core.cache import cache
from BanBanTong.db import models
from BanBanTong.utils import simplecache


class Task(object):
    '''
        把本机cache的内容更新给上级服务器
        1. class-%s-active-time 班级在线状态
        2. teacher-%s-active-time 教师在线状态
        3. class-%s-teacherlogintime 使用时长

        4. class-%s-active-time 电脑教室在线状态
        5. computerclass-teacher-%s-active-time 电脑教室教师在线状态
    '''
    run_period = 5
    logger = logging.getLogger(__name__)

    def update_class_active_status(self, host, port, key):
        url = 'http://%s:%s/api/class/set-active-status/' % (host, port)
        terms = models.Term.get_current_term_list()
        q = models.Class.objects.filter(grade__term__in=terms)
        q = q.values_list('uuid', flat=True)
        res = {}
        for uu in q:
            k = 'class-%s-active-time' % uu
            v = cache.get(k)
            if v:
                res[k] = v
        data = {'key': key, 'data': json.dumps(res)}
        try:
            req = urllib2.urlopen(url, urllib.urlencode(data))
        except:
            return
        try:
            # ret = req.read()
            req.fp._sock.recv = None
            req.close()
        except:
            return

    def update_teacher_active_status(self, host, port, key):
        url = 'http://%s:%s/api/class/set-active-status/' % (host, port)
        q = models.Teacher.objects.all()
        q = q.values_list('uuid', flat=True)
        res = {}
        for uu in q:
            k = 'teacher-%s-active-time' % uu
            v = cache.get(k)
            if v:
                res[k] = v
        data = {'key': key, 'data': json.dumps(res)}
        try:
            req = urllib2.urlopen(url, urllib.urlencode(data))
        except:
            return
        try:
            # ret = req.read()
            req.fp._sock.recv = None
            req.close()
        except:
            return

    def update_computerclass_teacher_active_status(self, host, port, key):
        url = 'http://%s:%s/api/class/set-active-status/' % (host, port)
        q = models.Teacher.objects.all()
        q = q.values_list('uuid', flat=True)
        res = {}
        for uu in q:
            k = 'computerclass-teacher-%s-active-time' % uu
            v = cache.get(k)
            if v:
                res[k] = v
        data = {'key': key, 'data': json.dumps(res)}
        try:
            req = urllib2.urlopen(url, urllib.urlencode(data))
        except:
            return
        try:
            # ret = req.read()
            req.fp._sock.recv = None
            req.close()
        except:
            return

    def update_teacherlogintime(self, host, port, key):
        url = 'http://%s:%s/api/class/set-active-status/' % (host, port)
        terms = models.Term.get_current_term_list()
        q = models.Class.objects.filter(grade__term__in=terms)
        q = q.values_list('uuid', flat=True)
        res = {}
        for uu in q:
            k = 'class-%s-teacherlogintime' % uu
            v = cache.get(k)
            if v:
                res[k] = v
        data = {'key': key, 'data': json.dumps(res)}
        try:
            req = urllib2.urlopen(url, urllib.urlencode(data))
        except:
            return
        try:
            # ret = req.read()
            req.fp._sock.recv = None
            req.close()
        except:
            return

    def update_online(self):
        server_type = models.Setting.getvalue('server_type')
        if server_type == 'school':
            term = models.Term.get_current_term_list()
            if not term:
                return
            try:
                p = models.Statistic.objects.get(
                    school_year=term[0].school_year,
                    term_type=term[0].term_type,
                    type='province'
                )
                print p.key
            except:
                traceback.print_exc()
            c = p.child_set.all()
            t = models.Statistic.get_items_descendants(c, 'town')
            s = models.Statistic.get_items_descendants(t, 'school')
            g = models.Statistic.get_items_descendants(s, 'grade')
            for o in g:
                simplecache.update_online(o)
            for o in s:
                simplecache.update_online(o)
            for o in t:
                simplecache.update_online(o)
            for o in c:
                simplecache.update_online(o)
            for o in p:
                simplecache.update_online(o)

    def update_total(self):
        # TODO 这个不应该放在定时任务里面跑
        server_type = models.Setting.getvalue('server_type')
        if server_type == 'school':
            term = models.Term.get_current_term_list()
            if not term:
                return
            try:
                p = models.Statistic.objects.get(
                    school_year=term[0].school_year,
                    term_type=term[0].term_type,
                    type='province'
                )
            except:
                traceback.print_exc()
            c = p.child_set.all()
            t = models.Statistic.get_items_descendants(c, 'town')
            s = models.Statistic.get_items_descendants(t, 'school')
            g = models.Statistic.get_items_descendants(s, 'grade')
            c = models.Statistic.get_items_descendants(c, 'class')
            for o in c:
                simplecache.set_totals(o)
            for o in g:
                simplecache.update_totals(o)
            for o in s:
                simplecache.update_totals(o)
            for o in t:
                simplecache.update_totals(o)
            for o in c:
                simplecache.update_totals(o)
            for o in p:
                simplecache.update_totals(o)

    def __init__(self):
        # if models.Setting.getvalue('server_type') != 'school':
        #     return
        # if models.Setting.getvalue('installed') != 'True':
        #     return
        # host = models.Setting.getvalue('sync_server_host')
        # port = models.Setting.getvalue('sync_server_port')
        # key = models.Setting.getvalue('sync_server_key')
        # if host and port and key:
        #     pass
        # else:
        #     print host, port, key, 'update cache will return directly'
        #     return
        # self.update_class_active_status(host, port, key)
        # self.update_teacher_active_status(host, port, key)
        # self.update_computerclass_teacher_active_status(host, port, key)
        # self.update_teacherlogintime(host, port, key)

        print 'update online'
        self.update_online()
        print 'update total'
        self.update_total()
