# coding=utf-8
import logging
import mimetypes
import os
import sys
from wsgiref.util import FileWrapper
from django.http.response import HttpResponse
from django.utils.http import urlquote
from BanBanTong.utils import session
from BanBanTong.utils import is_admin
from BanBanTong.utils import create_failure_dict


logger = logging.getLogger(__name__)


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


def authorized_user(func):
    def _inner(request, *args, **kwargs):
        request.current_user = session.get_user(request)
        return func(request, *args, **kwargs)

    return _inner


def authorized_user_with_redirect(func):
    def _inner(request, *args, **kwargs):
        request.current_user = session.get_user(request)
        if not request.current_user:
            return create_failure_dict(status='not login',
                                       msg='您未登录或登录超时，请重新登录！')

        try:
            return func(request, *args, **kwargs)
        except UnicodeEncodeError, e:
            logger.exception(e.object)

    return _inner


def authorized_privilege(privilege_key):
    def _func(func):
        def _inner(request, *args, **kwargs):
            if not is_admin(request.current_user):
                privilege_keys = privilege_key.split(',')
                for i in privilege_keys:
                    ret = create_failure_dict(status='permission_denied',
                                              msg='您没有权限访问当前功能！')
                    if not request.current_user.role:
                        # 当前用户没有配置角色
                        return ret
                    else:
                        r = request.current_user.role
                        count = r.roleprivilege_set.filter(privilege=i).count()
                        if count == 0:
                            # 当前用户的角色没有该权限
                            return ret

            return func(request, *args, **kwargs)

        return _inner
    return _func


class TailRecurseException:

    def __init__(self, args, kwargs):
        self.args = args
        self.kwargs = kwargs


def tail_call_optimized(g):
    def func(*args, **kwargs):
        f = sys._getframe()
        if f.f_back and f.f_back.f_back and f.f_back.f_back.f_code == f.f_code:
            # 抛出异常
            raise TailRecurseException(args, kwargs)
        else:
            while 1:
                try:
                    return g(*args, **kwargs)
                except TailRecurseException, e:
                    # 捕获异常, 拿到参数, 退出被修饰函数的递归调用栈
                    args = e.args
                    kwargs = e.kwargs
    func.__doc__ = g.__doc__
    return func
