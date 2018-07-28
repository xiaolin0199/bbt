# coding=utf-8
# 授权激活,同激活服务器通信,同校级服务器通信的接口方法
import time
import json
import uuid
import logging
import platform
import datetime
import ConfigParser
import urllib
import urllib2
from django.conf import settings

from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.utils.str_util import CryptHelper

from activation.decorator import get_use_activate
from activation.decorator import has_activate as get_activate_status
from activation.utils import create_success_dict, create_failure_dict
DEBUG = settings.DEBUG

LANG = settings.LANGUAGE_CODE
AES_KEY = constants.AES_KEY
TOKENURL = constants.TOKENURL
ACQUIREURL = constants.ACQUIREURL
ACTIVATE_USER = constants.ACTIVATE_USER
IV = AES_KEY[8:24]

logger = logging.getLogger(__name__)

CODES = {
    'en': {
        '0': 'success',
        '1': 'sn_not_exist',
        '2': 'canceled_sn',
        '3': 'mcd_not_match_with_license',
        '4': 'canceled_license',
        '5': 'mcd_not_match_with_product',
        '6': 'server_error',
        '7': 'sn_error',
        '8': 'mcd_error',
        '9': 'email_error',
        '10': 'lang_error',
        '11': 'server_down',
        '12': 'not_generated_sn',
        '13': 'sn_not_match_with_product_type',
        '14': 'version_error',
        '15': 'exceed_sn_num_limit',
        '16': 'sn_not_exist_cancel',
        '17': 'expired_sn',
        '18': 'county_not_match',
        '19': 'invalid_county',
        '20': 'city_not_match',
        '21': 'invalid_city',
        '22': 'sn_error',
        '1001': 'authorized_failed',
        '1002': 'invalid_request',
        '1003': 'request_too_frequently',

        '-1': 'connection_lost',
        '-500': 'request_failed',
        '-501': 'configuration_not_found',
        '-502': u'wrong_city_id',
        '-503': u'wrong_country_id',
        '-504': u'wrong_message_format',
        '-505': u'token_get_failed',
    },
    'zh-cn': {
        '0': u'操作成功',
        '1': u'当前密钥不存在',
        '2': u'被拒绝的密钥',
        '3': u'目标机器与密钥不匹配',
        '4': u'canceled_license',
        '5': u'这似乎不是用于该产品的密钥',
        '6': u'服务器错误',
        '7': u'错误的密钥',
        '8': u'错误的机器码',
        '9': u'email_error',
        '10': u'错误的软件语言',
        '11': u'server_down',
        '12': u'不存在的密钥',
        '13': u'密钥与软件类型不符',
        '14': u'密钥与授权软件版本不符',
        '15': u'exceed_sn_num_limit',
        '16': u'sn_not_exist_cancel',
        '17': u'密钥已失效',
        '18': u'授权区域与服务器中不匹配',
        '19': u'授权区县与使用的密钥不匹配',
        '20': u'授权区域与服务器中不匹配',
        '21': u'错误的市',
        '22': u'错误的密钥(22)',
        '1001': u'权限验证失败',
        '1002': u'非法请求',
        '1003': u'请求过于频繁',

        '-1': u'连接丢失',
        '-500': u'请求失败',
        '-501': u'获取配置项失败',
        '-502': u'获取区县标识失败',
        '-503': u'获取区县标识失败',
        '-504': u'服务器返回的错误的格式的数据',
        '-505': u'Token获取失败',
    },
}


def _getToken(user):
    salt = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data = {
        'user': user,
        'salt': CryptHelper.encrypt(salt, AES_KEY, IV)
    }
    logger.debug(u'_getToken: 请求数据:%s', data)
    try:
        result = urllib2.urlopen(TOKENURL, urllib.urlencode(data)).read()
        d = json.loads(result)
        logger.debug(u'_getToken: 返回数据:%s', d)
        if d.has_key('token'):
            return CryptHelper.decrypt(d['token'], AES_KEY, IV), 0
        return None, d['code']
    except KeyError:
        return None, '-505'
    except ValueError:
        return None, '-504'
    except Exception as e:
        logger.exception(e)
        return None, '-500'


def _getLicense(sn, token):
    # 获取地域标识
    province = models.Setting.getvalue('province')
    city = models.Setting.getvalue('city')
    country = models.Setting.getvalue('country')
    try:
        obj = models.GroupTB.objects.get(
            name=country,
            parent__name=city,
            parent__parent__name=province
        )
        country_id = obj.group_id
        city_id = obj.parent.group_id
    except models.GroupTB.DoesNotExist:
        return {'code': '-502'}
    except Exception:
        return {'code': '-502'}

    # 获取版本标识
    platform_system = platform.system()
    if platform_system == 'Linux':
        version = 'Linux'
    else:
        path = constants.BANBANTONG_VERSION_FILE
        config_file = ConfigParser.RawConfigParser()
        config_file.read(path)
        major = config_file.get('Version', 'Version number')
        minor = config_file.get('Version', 'svn')
        version = major + '.' + minor
    try:
        models.Setting.objects.get_or_create(
            name='Version',
            defaults={'value': version}
        )
    except models.Setting.MultipleObjectsReturned:
        models.Setting.objects.filter(name='Version').delete()
        models.Setting.objects.get_or_create(
            name='Version',
            defaults={'value': version}
        )

    body = {
        'sn': sn,
        'county': country_id,
        'city': city_id,
        'mcd': str(uuid.uuid4()),
        'timestamp': time.time(),
        'version': version,
        'product_key': 'bbt',
        'lang': 'zh_CN'
    }

    logger.debug(u'_getLicense: 请求数据:%s', body)
    postData = {
        'token': token,
        'body': CryptHelper.encrypt(json.dumps(body), AES_KEY, IV)
    }
    result = urllib2.urlopen(ACQUIREURL, urllib.urlencode(postData)).read()
    try:
        result = json.loads(result)
        logger.debug(u'_getLicense: 返回数据:%s', result)
        return result
    except:
        return {'code': '-500'}


def activate(request, *args, **kwargs):
    # 1.获取token
    token, code = _getToken(ACTIVATE_USER)
    logger.debug('1.get token=%s', token)
    if not token:
        create_failure_dict(
            msg=u'激活失败',
            debug=[token, code],
            errors=u'Token获取失败',
            reason=CODES.get(LANG, CODES['en']).get(str(code), 'unknown error'),
        )

    # 获取激活密钥
    sn = request.POST.get('activate_key')
    if DEBUG:
        sn = request.POST.get('activate_key', request.GET.get('activate_key'))
    if not sn:
        return create_failure_dict(msg=u'激活密钥获取失败')

    data = _getLicense(sn, token)

    if isinstance(data, dict) and data.get('code') == 0:
        if not data.has_key('body'):
            return create_failure_dict(msg=u'激活数据获取失败', debug=data)
        body = CryptHelper.decrypt(data['body'], AES_KEY, IV)
        quota = json.loads(body)
        country = models.GroupTB.objects.get(group_id=quota['county'])
        country_name = country.name
        city_name = country.parent.name
        province_name = country.parent.parent.name

        quota['update_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        quota['country_name'] = country_name
        quota['city_name'] = city_name
        quota['area'] = '%s %s %s' % (province_name, city_name, country_name)

        models.Setting.setval('activation', quota)
        val = models.Setting.getval('activation')
        return create_success_dict(msg=u'激活成功', val=val)

    return create_failure_dict(
        msg=CODES.get(LANG, CODES['en']).get(str(data['code']), 'unknown error'),
        reason=CODES.get(LANG, CODES['en']).get(str(data['code']), 'unknown error'),
        debug=data
    )


def update_activate_info(d):
    "校级服务器更新配额"
    if not (isinstance(d, dict) and d.has_key('quota')):
        return

    has_activate, x, old_info = get_activate_status()
    if not has_activate or old_info['quota'] < d['quota']:
        # 1.未激活,分几种情况,所以这里value使用更新的方式.
        # 2.扩大校级的配额的情况,也是直接更新.
        old_info.update(d)
        models.Setting.setval('activation', old_info)

    elif get_use_activate() > d['quota']:
        # 如果当前校级使用点数超过县级的最新配额
        # 既然能同步下来,那么说明网络是通畅的,
        # 那么何不告诉上级,分配的不够了呢.
        # i_need_more = {
        #     'quota': get_use_activate()
        # }
        # tell_my_father(i_need_more)
        logger.debug('get_use_activate: %s, quota: %s', get_use_activate(), d['quota'])
    else:
        logger.debug('get_use_activate: %s, quota: %s', get_use_activate(), d['quota'])
        old_info.update(d)
        models.Setting.setval('activation', old_info)
