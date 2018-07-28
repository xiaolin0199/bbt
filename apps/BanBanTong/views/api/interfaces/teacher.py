# coding=utf-8
from BanBanTong.db import models
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import create_failure_dict


def usb_check(request):
    if models.Setting.getvalue('server_type') != 'school':
        return create_failure_dict()
    if request.method == 'GET':
        key = request.GET.get('key')
        mac = request.GET.get('mac')
        try:
            u = models.UsbkeyTeacher.objects.get(usbkey_uuid=key)
        except:
            return create_failure_dict(msg='无效的USBKey！')
        try:
            t = models.Teacher.objects.get(uuid=u.teacher_uuid)
        except:
            return create_failure_dict(msg='找不到对应教师！')
        try:
            c = models.Class.objects.get(classmacv2__mac=mac)
        except:
            return create_failure_dict(msg='MAC地址未申报！')
        q = models.LessonTeacher.objects.filter(class_uuid=c, teacher=t)
        if not q.exists():
            return create_failure_dict(msg='教师在本班没有排课！')
        data = {'teacher': {'key': t.uuid, 'sequence': t.sequence,
                            'name': t.name, 'password': t.password}}
        return create_success_dict(data=data)
