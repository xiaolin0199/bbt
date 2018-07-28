# coding=utf-8
from django.http.response import HttpResponseRedirect
from BanBanTong.db import models
from BanBanTong.utils import session


def login(request, *args, **kwargs):
    # role = request.GET.get('role')
    # token = request.GET.get('token')
    user = models.User.objects.get(username='admin')
    session.save_user(request, user)
    return HttpResponseRedirect('/')
