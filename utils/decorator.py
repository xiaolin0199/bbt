# coding=utf-8
import os
import functools
import logging
import mimetypes
import json
from django import http
from django.utils.translation import ugettext_lazy as _
from django.utils import decorators
from wsgiref.util import FileWrapper
from django.http import HttpResponse, HttpResponseRedirect
# from django.core.exceptions import ValidationError
from django.utils.http import urlquote
from django.core.urlresolvers import reverse

from utils.http import JsonResponse

logger = logging.getLogger(__name__)


def ajax(authenticated=True, data_required=True, action=None, **kwargs):
    """
    `from django.views.generic import View` 类下面的get/post/put/delete
    方法的一个装饰器, 用于处理request中的数据和判定用户登录, 权限

    authenticated 是否需要登录
    data_required 请求中是否需要数据
    data_required_except_action 不需要数据的action
    action 当前进行的操作(参数)
    """
    ACTION_FUNCS = {
        'get': 'Read',
        'post': 'Create',
        'put': 'Update',
        'delete': 'Delete'
    }

    def get_action(params):
        if isinstance(params, dict):
            action_format = params.get('format') or '%(act)s%(obj)s'
            ctx = params.copy()
            ctx['act'] = ACTION_FUNCS.get(ctx['func'], ctx['func'])
            for key, value in ctx.items():
                if isinstance(value, basestring):
                    ctx[key] = _(value)
            return action_format % ctx
        return params

    def decorator(func, authenticated=authenticated, data_required=data_required):
        @functools.wraps(func, assigned=decorators.available_attrs(func))
        def _wrapped(self, request, *args, **kw):
            data_required_except_action = kwargs.get('data_required_except_action')
            if isinstance(data_required_except_action, basestring):
                data_required_except_action = [data_required_except_action]
            data_required_except_action = data_required_except_action or []
            action_params = {'func': func.__name__.lower()}
            if isinstance(action, dict):
                action.update(kwargs)
                action_params.update(action)
                act = get_action(action_params)
            else:
                act = isinstance(action, basestring) and action or kw.get('action')

            if authenticated and not request.user.is_authenticated():
                return JsonResponse({
                    'msg': _('you are not authenticated'),
                    'action': act
                }, status=401)

            # if data_required and kw.get('action') not in data_required_except_action:
            request.DATA = None
            try:
                request.DATA = json.loads(request.body)
            except (TypeError, ValueError) as e:
                # 兼容一下表单形式的POST提交
                request.DATA = request.QueryDict
                if data_required and kw.get('action') not in data_required_except_action and request.DATA is None:
                    return JsonResponse({
                        'msg': _('malformed JSON request: %(err)s' % {'err': e}),
                        'action': act
                    }, status=400)
            except Exception as e:
                if data_required and kw.get('action') not in data_required_except_action and request.DATA is None:
                    logger.exception('Internal Server Error: %(err)s' % {'err': e})
                    return JsonResponse({
                        'msg': _('Internal Server Error: %(err)s' % {'err': e}),
                        'action': act
                    }, status=500)

            data = func(self, request, *args, **kw)
            if isinstance(data, http.HttpResponse):
                return data

            return JsonResponse(data)

        return _wrapped
    return decorator


class FixedFileWrapper(FileWrapper):

    def __iter__(self):
        self.filelike.seek(0)
        return self


def file_response(func):
    def _inner(request, *args, **kwargs):
        result = func(request, *args, **kwargs)
        if isinstance(result, HttpResponse):
            return result
        wrapper = FixedFileWrapper(open(result['path'], 'rb'))
        content_type = mimetypes.guess_type(result['name'])[0]
        response = HttpResponse(wrapper, content_type)
        response['Content-Length'] = os.path.getsize(result['path'])
        filename = urlquote(os.path.basename(result['name']))
        disp = "attachment; filename=%s" % filename
        response['Content-Disposition'] = disp
        return response

    return _inner


def login_required(func):
    def _inner(request, *args, **kwargs):
        user = request.user
        if not user or not user.is_active:
            return HttpResponseRedirect(reverse('base:login'))
        return func(request, *args, **kwargs)

    return _inner


def admin_required(func):
    @login_required
    def _inner(request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            # TODO raise 403
            return HttpResponseRedirect('/')
        return func(request, *args, **kwargs)

    return _inner


class cached_property(object):

    def __init__(self, func, name=None):
        self.func = func
        self.__doc__ = getattr(func, '__doc__')
        self.name = name or func.__name__

    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        res = instance.__dict__[self.name] = self.func(instance)
        return res
