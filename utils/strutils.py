# coding=utf-8
import uuid
import functools


def any2bool(anything):
    if isinstance(anything, bool):
        return anything
    elif isinstance(anything, basestring):
        if anything.isalpha():
            return bool(anything.lower() == 'true')
        if anything.isdigit():
            return not bool(int(anything) == 0)

    elif isinstance(anything, int):
        return not bool(int(anything) == 0)

    return False


def random_key(n=6, format=None):
    """生成指定长度的随机数, 基于MAC地址、当前时间戳、随机数生成"""
    base = list('abcdefghijklmbopqrstuvwxyzABCDEFGHIJKLMBOPQRSTUVWXYZ0123456789')
    seed = ''.join([str(uuid.uuid1()).replace('-', '').lower()
                    for i in range(n * 4 / 32 + 1)])
    lst = []
    for i in range(n):
        hex_str = seed[i * 4:i * 4 + 4]
        x = int(hex_str, 16)
        lst.append(base[x % 62])
    value = ''.join(lst)
    if format == 'upper':
        value = value.upper()

    return value


random_key_8 = functools.partial(random_key, n=8)
random_key_16 = functools.partial(random_key, n=16)
random_key_16_upper = functools.partial(random_key, n=16, format='upper')
random_key_upper = functools.partial(random_key, format='upper')
