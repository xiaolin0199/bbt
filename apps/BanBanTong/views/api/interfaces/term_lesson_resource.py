# coding=utf-8
import json
import base64
import datetime
import logging
from django.core import serializers
from BanBanTong.db import models
from BanBanTong.utils import create_success_dict
from django.conf import settings
from BanBanTong.utils import str_util
DEBUG = settings.DEBUG
del settings

logger = logging.getLogger(__name__)


def getall(request):
    # 学年学期,课程,资源来源,资源类型这些'静态'数据可以放进缓存中,使用的时候
    # 直接从缓存中获取,当更新了的时候更新一下缓存,这样可以减少一下数据库查询
    data = {
        'term': '',
        'lesson': [],
        'resourcefrom': '',
        'resourcetype': '',
        'quota': '{}'
    }
    q = models.NewTerm.objects.all()
    data['term'] = serializers.serialize('json', q)
    q = models.NewLessonName.objects.all()
    lessons = []
    for obj in q:
        lesson = {}
        lesson['name'] = obj.name
        lesson['deleted'] = obj.deleted
        lesson['types'] = ','.join([i.name for i in obj.lesson_type.all()])
        lessons.append(lesson)
    data['lesson'] = lessons
    q = models.ResourceFrom.objects.all()
    data['resourcefrom'] = serializers.serialize('json', q)
    q = models.ResourceType.objects.all()
    data['resourcetype'] = serializers.serialize('json', q)

    # 处理一下授权激活信息
    communicate_key = request.POST.get('communicate_key', None)
    if communicate_key:
        try:
            node = models.Node.objects.get(communicate_key=communicate_key)
            d = models.Setting.getval('activation')
            if d:
                info = d
                info['quota'] = node.activation_number
                info['update_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                info['school_name'] = node.name
                try:
                    del info['mcd']
                    del info['product_key']
                    del info['sn']
                except:
                    info['mcd'] = ''
                    info['product_key'] = ''
                    info['sn'] = ''
                # 用key可name一起来加密数据
                # 防止A学校用B的key连接获取B的配额的情况
                # A学校本地会用自己的name和key来解密
                key = '%s-%s' % (communicate_key, node.name)
                key = base64.b64encode(json.dumps(key))
                content, key = str_util.encode(info, key=key)
                data['quota'] = base64.b64encode(content)
        except models.Node.DoesNotExist:
            pass
        except Exception as e:
            logger.exception(e)

    return create_success_dict(data=data)
