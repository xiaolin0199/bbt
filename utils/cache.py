# coding=utf-8
import logging
import functools
from django.db import models
from django.core.cache import cache
from django.utils import decorators
from oecloud_dashboard.api.base import APIDictWrapper, APIResourceWrapper
from django_redis import get_redis_connection


PRODUCT = 'oecloud'

logger = logging.getLogger(__name__)


def _get_obj_key(obj, k='id'):
    """获取对象的主键"""
    if isinstance(obj, dict):
        return obj.get(k) or obj.get('id') or obj.get('uuid')
    return getattr(obj, k, getattr(obj, 'id', None) or getattr(obj, 'uuid', None))


def get_obj_value(obj, k=None, v=None, debug=False):
    """
    获取对象中指定字段的键值

    :param k: 对象中对应的一个key
    :param v: 获取k对应的值失败的时候返回的默认值
    """
    if k is None:
        return obj
    elif hasattr(obj, k):
        value = getattr(obj, k)
        return callable(value) and value() or value
    elif isinstance(obj, dict):
        return obj.get(k)
    elif isinstance(obj, (APIDictWrapper, APIResourceWrapper)):
        d = obj.to_dict()
        return d.get(k)
    else:
        return v


def generate_cachekey(prefix='', suffix='', **kw):
    """
    生成缓存的键

    :param prefix: 缓存的key的前缀
    :param suffix: 缓存的key的后缀
    :param kw: 暂时没用到的其他参数
    """
    # if not (prefix is not None and bool(suffix) is not False):
    #     return
    assert prefix is not None, 'prefix is not given'
    assert bool(suffix) is not False, 'suffix is not given'
    return '%s-%s::%s' % (PRODUCT, prefix or 'CACHE', suffix)


def _get_cachevalue(obj, prefix=None, suffix=None, which_key=None, debug=False, **kw):
    cachevalue = get_obj_value(obj, which_key)
    if not (cachevalue and isinstance(cachevalue, (dict, APIResourceWrapper, APIDictWrapper, models.Model))):
        # 此处的目的在于当某个对象更新了时候对应的'更新/删除'缓存
        # 所以如果对象传进来了, 但是值不对, 那么需要把旧的缓存清理掉
        if suffix:
            cachekey = generate_cachekey(prefix, suffix)
            cache.delete(cachekey)
        logger.debug(u'😀😀😀cache_set_obj::BAD obj=%s\n'
                     u'😀😀😀cache_set_obj::delete cachekey=%s' % (obj, cachekey))
        return

    # 直接使用APIResourceWrapper的话在序列化的时候会出问题
    # 这里先把内部的数据类型转换为dict, 然后在to_dict上面做一点工作
    if isinstance(cachevalue, APIResourceWrapper):
        try:
            cachevalue = cachevalue.__class__(cachevalue.to_dict())
        except:
            cachevalue = cachevalue.to_dict()
    return cachevalue


def find_obj_by_path(original, path, debug=False):
    if isinstance(original, (APIDictWrapper, APIResourceWrapper)):
        base = original.to_dict()
    else:
        base = original
    objs = []
    paths = path.split('::')

    key = paths[0]
    paths = paths[1:]
    if debug:
        logger.debug('base=%s, type=%s' % (base, type(base)))

    if isinstance(base, dict):
        base = base.get(key, {})
    elif isinstance(base, (str, unicode)):
        return [base]

    if isinstance(base, list):
        # logger.error('list base=%s' % base)
        for obj in base:
            objs.extend(find_obj_by_path(obj, '::'.join(paths)))
    elif isinstance(base, dict) and base:
        # logger.error('dict base=%s' % base)
        objs.extend(find_obj_by_path(base, '::'.join(paths)))
    else:
        # logger.error('else base=%s' % base)
        objs.append(base)
    return objs


def delete_related_cache(obj=None, prefix=None, suffix=None, which_key=None, debug=False, **kw):
    """
    关联对象缓存更新

    用于删除失效关联缓存数据(例如子网更新了需要更新子网所在的网络缓存,
    这里直接删除掉旧缓存, 下次取值重新设置缓存)

    :param obj: dict, APIResourceWrapper或APIDictWrapper类型的对象
    :param prefix: 缓存的key的前缀，一般来说， `obj` 使用uuid主键的时候flag不需要提供, 使用id的则需要提供一个标识位
    :param suffix: 缓存的key的后缀，一般来说， `obj` 的主键作为此字段的值
    :param which_key: 从obj里面取到which_key的值作为缓存的键值的一部分
        该字段的用法可能是 obj.which_key,obj['which_key']或者obj.which_key()
    """
    relateds = kw.get('related')
    logged_msg = []
    logged_msg.append('obj=%s\n'
                      'prefix=%s\n'
                      'suffix=%s\n'
                      'which_key=%s\n'
                      'relateds=%s\n' % (
                          type(obj), prefix, suffix, which_key, relateds
                      ))

    if relateds:
        relateds = [r for r in relateds.split('|') if r]
        for related in relateds:
            if not obj:
                cache_key = generate_cachekey(prefix, suffix)
                obj = cache.get(cache_key)
            cachevalue = _get_cachevalue(obj, prefix, suffix, which_key, debug, **kw)
            related_prefix, related_key = related.split('::', 1)
            lst = []
            if '::' not in related_key:
                lst = _get_obj_key(cachevalue, related_key)
                lst = isinstance(lst, list) and lst or [lst]

            else:
                lst = find_obj_by_path(cachevalue, related_key)
                if kw.get('debug'):
                    logged_msg.append('will be deleted: related_prefix=%s, keys=%s\n' % (related_prefix, lst))
                lst = [i for i in lst if i]

            for related_obj_id in lst:
                if not related_obj_id:
                    continue
                related_cache_key = generate_cachekey(related_prefix, related_obj_id, **kw)
                cache.delete(related_cache_key)
                if debug:
                    logged_msg.append(u'GET related_cache_key=%s\n' % related_cache_key)
    if debug:
        logger.debug(''.join(logged_msg))


def redis_naive_delete_cache(ids):
    con = get_redis_connection("default")
    dirty_keys = []
    for id in ids:
        keys = con.keys('*%s*' % id)
        dirty_keys.extend(keys)
    if dirty_keys:
        logger.debug('redis_naive_delete_cache keys=%s' % dirty_keys)
        con.delete(*dirty_keys)


related_status_map = {
    # 任意健康监控处于非临界状态
    'lb-pool': lambda obj: any(map(
        lambda hm: hm and str(hm.get('status')).lower().startswith('pending'),
        obj and obj.get('health_monitors_status') or []
    ))
}


def cache_set_obj(obj, prefix=None, suffix=None, which_key=None, debug=False, **kw):
    """
    对象缓存

    缓存可以用来缓存的对象, 返回该对象和其对应的缓存键

    :param obj: dict, APIResourceWrapper或APIDictWrapper类型的对象
    :param prefix: 缓存的key的前缀，一般来说， `obj` 使用uuid主键的时候flag不需要提供, 使用id的则需要提供一个标识位
    :param suffix: 缓存的key的后缀，一般来说， `obj` 的主键作为此字段的值
    :param which_key: 从obj里面取到which_key的值作为缓存的键值的一部分
        该字段的用法可能是 obj.which_key,obj['which_key']或者obj.which_key()
    """
    if not suffix:
        suffix = _get_obj_key(obj)
    cachekey = generate_cachekey(prefix, suffix)
    cachevalue = None
    cachevalue = _get_cachevalue(obj, prefix, suffix, which_key, debug, **kw)
    obj_status = getattr(cachevalue, 'status', '') or getattr(cachevalue, 'status', '')

    if str(obj_status).lower().startswith('pending') or str(obj_status).lower().endswith('ing'):
        if debug:
            logger.debug(u'stop create cache because cache in %s status\n'
                         u'DEL cachekey=%s \n' % (obj_status, cachekey))
        cache.delete(cachekey)

    elif related_status_map.has_key(prefix) and related_status_map[prefix](obj):
        if debug:
            logger.debug(u'stop create cache because related cache in PENDING status\n'
                         u'DEL cachekey=%s\n'
                         u'obj=%s\n' % (cachekey, obj))
        cache.delete(cachekey)

    else:
        cache.set(cachekey, cachevalue, 60 * 60 * 4)
        if debug:
            logger.debug(u'SET cachekey=%s\ncachevalue=%s' % (cachekey, cachevalue))
    delete_related_cache(obj, prefix, suffix, which_key, debug=debug, **kw)
    return obj, cachevalue


def cache_get_obj(prefix=None, suffix=None, debug=False, **kw):
    """缓存获取"""
    cachekey = generate_cachekey(prefix, suffix)
    cached_obj = cache.get(cachekey)
    if debug:
        logger.debug(
            'cachekey=%s\n'
            'cached_value=%s\n' % (cachekey, type(cached_obj)))

    if str(getattr(cached_obj, 'status', '')).lower().startswith('pending') or str(getattr(cached_obj, 'status', '')).lower().endswith('ing'):
        logger.warning(u'cache_get_obj::stop get cache\n'
                       u'cache_get_obj::delete cachekey=%s\n'
                       u'cache_get_obj::cached_obj=%s\n' % (cachekey, cached_obj))
        cache.delete(cachekey)
        return
    elif related_status_map.has_key(prefix) and related_status_map[prefix](cached_obj):
        logger.warning(u'cache_get_obj::stop get cache because related cache in PENDING status\n'
                       u'obj=%s\n'
                       u'cache_get_obj::delete cachekey=%s\n'
                       u'cache_get_obj::cached_obj=%s ' % (cached_obj, cachekey, cached_obj))
        cache.delete(cachekey)
        return

    return cached_obj


def _cache_handle_base(mode, **wrapper_kwargs):
    """
    对象被更新后对应的更新缓存

    一些常用参数
    :param prefix: 缓存的key的前缀
    :param suffix: 缓存的key的后缀
    :param suffix_key: 缓存的key的后缀在传参中的名字(作用于getfunc(self, *args, **kw) 形式)
    :param which_key: 用来缓存的部分(obj.which_key)
    :param anonymous(boolean): 目标函数的调用方式
        True: 作用于形如 getfunc(self, *args, **kw) 的函数
        False: 作用于形如 getfunc(self, obj_id, *args, **kw) 的函数
    :param related: 关联的资源(prefix::key)
        关联的资源(当前资源更新后关联资源缓存被删除)
    :param debug: 调试模式
    """
    import api.jobs

    def _wrapper(func):

        @functools.wraps(func, assigned=decorators.available_attrs(func))
        def _inner(self, *args, **kw):
            logged_msg = []
            inner_kwargs = wrapper_kwargs.copy()
            use_cache = kw.pop('use_cache', True)
            debug = inner_kwargs.get('debug')
            cached_obj = None
            if mode != 'create':
                suffix = kw.get(inner_kwargs.get('suffix_key')) or wrapper_kwargs.get(
                    inner_kwargs.get('suffix_key') or 'suffix')
                suffix = suffix or args and args[0] or None
                inner_kwargs['suffix'] = suffix
            logged_msg.append(
                'mode=%s\n'
                'call=%s\n'
                'args=%s\n'
                'kw=%s\n'
                'use_cache=%s\n'
                'kwargs=%s\n' % (
                    mode, func.__name__, args, kw, use_cache, inner_kwargs
                ))

            # list/get 的时候优先从缓存中获取返回值, 没有的时候才会调用func
            if mode == 'list':
                obj = func(self, *args, **kw)
                prefix = inner_kwargs.pop('prefix')
                suffix_key_path = inner_kwargs.pop('suffix_key', 'id')
                diff_key_path = inner_kwargs.get('diff_key', 'status')
                logged_msg.append('ADD api.jobs.cache_diff_and_destroy')
                api.jobs.rq_run(api.jobs.cache_diff_and_destroy, obj, prefix,
                                suffix_key_path, diff_key_path, **inner_kwargs)
            elif mode == 'get':
                obj = use_cache and cache_get_obj(**inner_kwargs)
                if not obj:
                    obj = func(self, *args, **kw)
                    cache_set_obj(obj, **inner_kwargs)

            # create/update/delete 的时候需要对应更新缓存
            elif mode in ('create', 'update', 'delete'):
                try:
                    cachekey = generate_cachekey(**inner_kwargs)
                    cached_obj = cache.get(cachekey)
                    delete_related_cache(debug=True, **inner_kwargs)
                except:
                    pass
                obj = func(self, *args, **kw)
                if mode == 'create' and not inner_kwargs.get('suffix'):
                    inner_kwargs.update({'suffix': _get_obj_key(obj)})

                if mode in ('create', 'update') and obj:
                    cache_set_obj(obj, **inner_kwargs)

                else:
                    try:
                        logged_msg.append('inner_kwargs=%s\n' % inner_kwargs)
                        delete_related_cache(obj, **inner_kwargs)
                        cachekey = generate_cachekey(**inner_kwargs)
                        cache.delete(cachekey)
                        logged_msg.append('DEL cache=%s\n' % cachekey)
                    except:
                        pass

                logged_msg.append(
                    'cached_obj=%(cached_obj)s\n'
                    'output obj=%(obj)s\n' % {
                        'cached_obj': cached_obj,
                        'obj': obj
                    })
            if debug:
                logger.debug(''.join(logged_msg) + '\n' + '#' * 80)
            return obj

        assert mode in ('list', 'get', 'create', 'update', 'delete')
        return _inner
    return _wrapper


# decorators
cache_handle_list = functools.partial(_cache_handle_base, mode='list')
cache_handle_get = functools.partial(_cache_handle_base, mode='get')
cache_handle_create = functools.partial(_cache_handle_base, mode='create')
cache_handle_update = functools.partial(_cache_handle_base, mode='update')
cache_handle_delete = functools.partial(_cache_handle_base, mode='delete')
