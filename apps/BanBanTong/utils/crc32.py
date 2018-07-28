# coding=utf-8
import binascii
import datetime


def getunsined_crc32(seed, length=4):
    return str(binascii.crc32('%s-%s' % (
        seed, datetime.datetime.now().strftime('%Y-%m-%d')
    )) & 0xffffffff)[:length]
