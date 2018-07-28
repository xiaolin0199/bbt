# coding=utf-8
from BanBanTong.db import models


def save_user(request, user):
    request.session['current_user'] = user.uuid


def get_user(request):
    try:
        uu = request.session.get('current_user')
        if uu:
            return models.User.objects.get(uuid=uu)
        else:
            return None
    except:
        return None


def clear_user(request):
    if hasattr(request, 'current_user') and request.current_user:
        request.current_user = None
        delattr(request, 'current_user')
        if request.session.get('current_user'):
            del request.session['current_user']
