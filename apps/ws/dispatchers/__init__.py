# coding=utf-8
import os
import glob
import imp
import inspect
import logging
from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import python_2_unicode_compatible


logger = logging.getLogger(__name__)

base_modulename = 'ws.dispatchers'


class NotRegistered(Exception):
    pass


class Registry(object):
    """注册后的任务会自动加入到schedule的任务队列中"""
    _objects = {}

    def __init__(self):
        if not getattr(self, '_registerable_class', None):
            raise ImproperlyConfigured('Subclasses of Registry must set a "_registerable_class" property.')

    def _register(self, cls):
        """注册给指定的Class, 如果已经被注册则忽略"""
        if not inspect.isclass(cls):
            raise ValueError('Only classes may be registered.')
        elif not issubclass(cls, self._registerable_class):
            raise ValueError('Only %s classes or subclasses may be registered.' % self._registerable_class.__name__)

        if cls not in self._objects:
            cls._registered_with = self
            self._objects[cls.slug] = cls
        return self._objects[cls.slug]

    def _unregister(self, cls):
        """取消注册指定的Class, 如果未注册则抛出``NotRegistered``异常"""
        if not issubclass(cls, self._registerable_class):
            raise ValueError('Only %s classes or subclasses may be unregistered.' % self._registerable_class)

        if cls.slug not in self._objects.keys():
            raise NotRegistered('%s is not registered' % cls)

        del self._objects[cls.slug]
        return True

    def _registered(self, cls):
        if inspect.isclass(cls) and issubclass(cls, self._registerable_class):
            found = self._objects.get(cls.slug, None)
            if found:
                return found
        else:
            # Allow for fetching by slugs as well.
            for registered in self._objects.values():
                if registered.slug == cls:
                    return registered

        registerable_class = self._registerable_class.__name__
        slug = getattr(cls, "slug", cls)
        if hasattr(self, "_registered_with"):
            raise NotRegistered('%(type)s with slug "%(slug)s" is not registered with %(parent)s "%(name)s".' % {
                "type": registerable_class,
                "slug": slug,
                "parent": self._registered_with._registerable_class.__name__,
                "name": cls.__name__
            })
        else:
            raise NotRegistered('%(type)s with slug "%(slug)s" is not registered.' % {
                "type": registerable_class,
                "slug": slug
            })

    def _has_registered(self, cls):
        if inspect.isclass(cls) and issubclass(cls, self._registerable_class):
            found = self._objects.get(cls.slug)
            if found:
                return True
        else:
            # Allow for fetching by slugs as well.
            for registered in self._objects.values():
                if registered.slug == cls.slug:
                    return True
        return False


@python_2_unicode_compatible
class DispatcherComponent(object):

    def __init__(self):
        super(DispatcherComponent, self).__init__()
        # url
        if not self.slug:
            raise ImproperlyConfigured('Every %s must have a slug.' % self.__class__)

        if not self.allowed_server_types:
            raise ImproperlyConfigured('Every %s must have a allowed_server_types.' % self.__class__)

        if not self.allowed_categories:
            raise ImproperlyConfigured('Every %s must have a allowed_categories.' % self.__class__)

        if not isinstance(self.allowed_server_types, list):
            raise ImproperlyConfigured('Dispatcher %s.allowed_server_types must be a list.' % self.__class__)

        if not isinstance(self.allowed_categories, list):
            raise ImproperlyConfigured('Dispatcher %s.allowed_categories must be a list.' % self.__class__)

    def __str__(self):
        name = getattr(self, 'name', u"Unnamed %s" % self.__class__.__name__)
        return name


class DispatcherBase(DispatcherComponent):
    """所有Dispatcher的基类"""
    name = ''
    slug = ''
    allowed_server_types = []
    allowed_categories = []
    properties = {}

    def __init__(self, *args, **kw):
        super(DispatcherBase, self).__init__(*args, **kw)

    def dispatch(self, factory, connects, server, msgdict):
        # if 'operation' not in msgdict:
        #     return {'ret': 1001, 'msg': '错误的指令格式'}

        # dispatch_func = None
        # if msgdict['operation'] == 'echo':
        #     dispatch_func = self.process_echo

        # if dispatch_func:
        #     return dispatch_func(factory.transport.sessionno, connects, server, msgdict)
        raise ImproperlyConfigured('Every %s must have a dispatch function.' % self.__class__)


class Dispatchers(Registry, DispatcherComponent):
    """全局的Dispatchers类, 所有的任务处理都在该类中实现"""

    # Required for registry
    _registerable_class = DispatcherBase

    name = 'Dispatchers'
    slug = 'dispatchers'

    def __repr__(self):
        return u"<Dispatcher: %s>" % self.slug

    def _autodiscover(self):
        """从 ``settings.INSTALLED_APPS`` 自动发现dispatchers下的任务并注册"""
        if getattr(self, "_autodiscover_complete", False):
            return
        if not getattr(self, '_registerable_class', None):
            raise ImproperlyConfigured('You must set a "_registerable_class" property in order to use autodiscovery.')

        py_files = glob.glob(os.path.join(os.path.dirname(__file__), '*.py'))
        for path in py_files:
            last_modulename = os.path.splitext(os.path.split(path)[1])[0]
            if last_modulename != '__init__':
                imp.load_source('%s.%s' % (base_modulename, last_modulename), path)

        pyc_files = glob.glob(os.path.join(os.path.dirname(__file__), '*.pyc'))
        for path in pyc_files:
            if path[:-1] in py_files:
                continue
            last_modulename = os.path.splitext(os.path.split(path)[1])[0]
            if last_modulename != '__init__':
                imp.load_compiled('%s.%s' % (base_modulename, last_modulename), path)

        # logger.debug('Dispatchers._autodiscover_complete\nregistered objs: %s', self._objects)
        self._autodiscover_complete = True

    def register(self, dispatcher):
        # logger.debug('Dispatchers.register: %s', dispatcher)
        self._register(dispatcher)
        return dispatcher

    def unregister(self, dispatcher):
        return self._unregister(dispatcher)

    def registered(self, cls_or_slug):
        return self._registered(cls_or_slug)

    def has_registered(self, cls_or_slug):
        return self._has_registered(cls_or_slug)

    def get_dispatcher(self, cls_or_slug):
        return self._registered(cls_or_slug)

    def get_dispatchers(self, server_type):
        if not getattr(self, '_autodiscover_complete', False):
            self._autodiscover()
        dispatchers = {
            slug: dispatcher_cls for slug, dispatcher_cls in self._objects.items()
            if server_type in dispatcher_cls.allowed_server_types
        }
        # logger.debug('get_dispatchers: %s', dispatchers)
        return dispatchers

    def check_category(self, server, slug, category):
        """检查客户端请求的path和category与服务器server_type合法性"""
        for d in server['dispatchers'].values():
            if server['server_type'] in d.allowed_server_types and d.slug == slug and category in d.allowed_categories:
                return True

        return False


class SingletonDispatchers(Dispatchers):
    """单例模式"""
    _instance = None

    def __new__(cls, *args, **kw):
        if not cls._instance:
            cls._instance = super(SingletonDispatchers, cls).__new__(cls, *args, **kw)
        return cls._instance

DISPATCHERS = SingletonDispatchers()

__all__ = ['DispatcherBase', 'DISPATCHERS']
