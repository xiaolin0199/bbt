#!/usr/bin/env python
# coding=utf-8
import json
import math
import uuid
import base64
from django.conf import settings
from Crypto.Cipher import AES
try:
    from BanBanTong import constants
    AES_KEY = constants.AES_KEY
except:
    AES_KEY = 'b6lUu-Ws)4aitz@7S1Ats17f$qA$RtQC'


def format_byte(size):
    if size <= 0:
        return '0KB'
    lst = ['KB', 'MB', 'GB', 'TB', 'PB']
    i = int(math.log(size, 1024))
    if i >= len(lst):
        i = len(lst) - 1

    return ('%.2f' + ' ' + lst[i]) % (size / math.pow(1024, i))


def class_name_to_number(class_name):
    try:
        return int(class_name)
    except:
        return 999


def generate_node_key(length=16):
    base = list(
        # 'abcdefghijklmbopqrstuvwxyzABCDEFGHIJKLMBOPQRSTUVWXYZ0123456789'
        'abcdefABCDEF0123456789'
    )

    seed = ''.join([str(uuid.uuid4()).replace('-', '')
                    for i in range(length * 4 / 32 + 1)])
    lst = []
    for i in range(length):
        sub_str = seed[i * 4:i * 4 + 4]
        x = int(sub_str, 16)
        # lst.append(base[x % 62])
        lst.append(base[x % 22])
    return ''.join(lst).upper()


def grade_name_to_number(grade_name):
    l = [
        u'一', u'二', u'三', u'四', u'五', u'六',
        u'七', u'八', u'九', u'十', u'十一', u'十二',
        u'电脑教室',
        # u'初一', u'初二', u'初三', u'高一', u'高二', u'高三'
    ]
    try:
        if not isinstance(grade_name, unicode):
            grade_name_map = {k.decode('utf8'): v.decode('utf8') for k, v in settings.CONF.server.grade_map.items()}
            grade_name = grade_name_map.get(grade_name) or grade_name
        return l.index(grade_name) + 1
    except:
        return 999


class CryptHelper(object):
    PADDING = '\0'
    BLOCK_SIZE = 32

    @staticmethod
    def pad(s):
        return s + (CryptHelper.BLOCK_SIZE - len(s) % CryptHelper.BLOCK_SIZE) * CryptHelper.PADDING

    @staticmethod
    def unpad(s):
        return s.rstrip(CryptHelper.PADDING)

    @staticmethod
    def encrypt(s, key, iv):
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(CryptHelper.pad(s))
        return base64.b64encode(encrypted)

    @staticmethod
    def decrypt(s, key, iv):
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return CryptHelper.unpad(cipher.decrypt(base64.b64decode(s)))


def _salt(length=32, seed=None, magic=None):
    """获取指定长度的salt"""
    magic = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789~!@#$%^&*()_+')
    hex_base = list('abcdefABCDEF0123456789')
    if not seed:
        seed = str(uuid.uuid4()).replace('-', '')
    else:
        seed = list(seed)
        # 下面需要对字串进行16进制的转换,所以将不能转换的字符替换掉
        for i, v in enumerate(seed[:]):
            seed[i] = seed[i] in hex_base and seed[i] or hex_base[i % 22]
        seed = ''.join(seed)
    seed = ''.join([seed for i in range(length * 4 / len(seed) + 1)])
    lst = []
    for i in range(length):
        hex_str = seed[i * 4:i * 4 + 4]
        x = int(hex_str, 16)
        lst.append(magic[x % len(magic)])
    salt = ''.join(lst)
    return salt


def encode(content, **kwargs):
    if kwargs.has_key('key') and kwargs['key']:
        key = _salt(32, kwargs['key'])
    else:
        key = AES_KEY

    iv = key[8:24]
    content = json.dumps(content)
    return CryptHelper.encrypt(content, key, iv), key


def decode(scret, **kwargs):
    if kwargs.has_key('key') and kwargs['key']:
        key = _salt(32, kwargs['key'])
    else:
        key = AES_KEY
    iv = key[8:24]
    content = CryptHelper.decrypt(scret, key, iv)
    content = json.loads(content)
    return content

if __name__ == '__main__':
    print generate_node_key(length=16)
    content = {
        'quota': 300,
        'update_time': '2015-01-01 00:00:01',
        'start_date': '2015-01-01',
        'end_date': '2015-12-31',
    }
    IV = None

    # 基于机器码
    print u'-----基于机器码-------'
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:].upper()
    secret, salt = encode(content, key=mac)
    print u'初始密钥: ', mac
    print u'加密密文: %r' % secret
    print u'解密明文: ', decode(secret, key=mac)

    # 基于时间的随机码
    print u'\n\n-----基于时间的随机码-------'
    random_str = str(uuid.uuid4()).replace('-', '')
    secret, salt = encode(content, key=random_str)
    print u'初始密钥: ', random_str
    print u'加密密文: %r' % secret
    print u'解密明文: ', decode(secret, key=random_str)

    # 指定密钥
    print u'\n\n-----指定密钥-------'
    # 约定用于加密解密的SALT
    secret, salt = encode(content, key=AES_KEY)
    print u'初始密钥: ', AES_KEY, salt
    print u'加密密文: %r' % secret
    print u'解密明文: ', decode(secret, key=AES_KEY)

    # 随机密钥
    print u'\n\n-----随机密钥-------'
    secret, key = encode(content)
    print u'初始密钥: ', key
    print u'加密密文: %r' % secret
    print u'解密明文: ', decode(secret)
