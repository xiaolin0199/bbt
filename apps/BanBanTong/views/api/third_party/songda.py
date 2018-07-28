# coding=utf-8
from django.http import HttpResponse, HttpResponseRedirect
from BanBanTong.db import models
from BanBanTong.utils import session


def login(request, *args, **kwargs):
    user = request.GET.get('user')
    err_page = request.GET.get('err_page')
    try:
        user = models.User.objects.get(username=user)
    except models.User.DoesNotExist:
        return HttpResponseRedirect(err_page)
    except:
        return HttpResponse(u'<p>服务器状态异常</p>')
    session.save_user(request, user)
    return HttpResponseRedirect('/')
