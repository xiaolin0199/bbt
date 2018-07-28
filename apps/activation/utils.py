# coding=utf-8
from django.conf import settings
DEBUG = settings.DEBUG


def create_failure_dict(**kwargs):
    if not DEBUG and 'debug' in kwargs:
        del kwargs['debug']
    elif 'debug' in kwargs:
        kwargs['#debug'] = kwargs['debug']
        del kwargs['debug']
    ret = {'status': 'failure'}
    ret.update(kwargs)
    return ret


def create_success_dict(**kwargs):
    if not DEBUG and 'debug' in kwargs:
        del kwargs['debug']
    elif 'debug' in kwargs:
        kwargs['#debug'] = kwargs['debug']
        del kwargs['debug']
    ret = {'status': 'success', 'success': True}
    ret.update(kwargs)
    return ret
