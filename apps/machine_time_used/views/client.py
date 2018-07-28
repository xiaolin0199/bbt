# coding=utf-8
# 同客户端底层交互
import logging
import datetime

from django import forms
from django.db import connection

from machine_time_used.models import MachineTimeUsed
from BanBanTong.db.models import ClassMacV2, Group, Term

from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict

logger = logging.getLogger(__name__)


class UploadForm(forms.Form):
    mac = forms.CharField()         # Mac
    date = forms.CharField()         # 时间
    count = forms.CharField()        # 开机次数
    runtimes = forms.CharField()     # 开机时长(分钟)
    offlinetimes = forms.CharField()  # 不在线时长(分钟)


def get_status(request, *args, **kwargs):
    '''
        客户端获取欲上传机器时长日期
    '''
    mac = request.GET.get('mac', '')
    if mac:
        try:
            t = Term.get_current_term_list()[0]
        except:
            return create_failure_dict(msg='尚未设置当前学期')
        # 根据mac获取班级信息
        try:
            class_obj = ClassMacV2.objects.get(mac=mac, class_uuid__grade__term=t).class_uuid
        except:
            return create_failure_dict(msg=u'机器使用时长MAC错误')
        class_name = class_obj.name

        grade_obj = class_obj.grade
        grade_name = grade_obj.name

        term = grade_obj.term
        term_school_year = term.school_year
        term_type = term.term_type

        objs = MachineTimeUsed.objects.filter(term_school_year=term_school_year, term_type=term_type, grade_name=grade_name, class_name=class_name).order_by('-create_time')

        now = datetime.datetime.now()
        now = now.date()

        if objs:
            obj = objs[0]
            date = obj.create_time.date()
            # 如果当天是最近的一天，则返回前一天
            if now == date:
                date = date - datetime.timedelta(days=1)

            return create_success_dict(data={'date': date})

        return create_success_dict(data={'date': term.start_date})

    return create_failure_dict(msg=u'请求需mac参数')


def upload(request, *args, **kwargs):
    '''
        客户端上传机器时长信息
    '''
    if request.method == 'GET':
        f = UploadForm(request.GET)
        if f.is_valid():
            mac = f.cleaned_data['mac']
            create_time = datetime.datetime.strptime(f.cleaned_data['date'], '%Y-%m-%d')
            use_count = int(f.cleaned_data['count'])
            use_time = int(f.cleaned_data['runtimes'])

            try:
                t = Term.get_current_term_list()[0]
            except:
                return create_failure_dict(msg='尚未设置当前学期')

            try:
                class_obj = ClassMacV2.objects.get(mac=mac, class_uuid__grade__term=t).class_uuid
            except:
                return create_failure_dict(msg=u'机器使用时长MAC错误')
            class_name = class_obj.name
            grade_name = class_obj.grade.name

            term = None
            terms = Term.objects.all()
            for obj in terms:
                if create_time.date() >= obj.start_date and create_time.date() <= obj.end_date:
                    term = obj
                    break

            term_school_year = term.school_year if term else u''
            term_type = term.term_type if term else u''

            school = Group.objects.get(group_type='school')
            school_name = school.name
            town_name = Group.objects.get(group_type='town').name
            country_name = Group.objects.get(group_type='country').name
            city_name = Group.objects.get(group_type='city').name
            province_name = Group.objects.get(group_type='province').name

            cursor = connection.cursor()
            cursor.execute('Lock TABLES machine_time_used_machinetimeused WRITE;')

            # 新建 或 更新
            try:
                s = datetime.datetime.combine(create_time, datetime.time.min)
                e = datetime.datetime.combine(create_time, datetime.time.max)
                obj = MachineTimeUsed.objects.get(
                    term_school_year=term_school_year,
                    term_type=term_type,
                    province_name=province_name,
                    city_name=city_name,
                    country_name=country_name,
                    town_name=town_name,
                    school_name=school_name,
                    grade_name=grade_name,
                    class_name=class_name,
                    mac=mac,
                    school=school,
                    create_time__range=(s, e))
                if obj.use_time != use_time or obj.use_count != use_count:
                    obj.use_time = use_time
                    obj.use_count = use_count
                    obj.save()
            except MachineTimeUsed.DoesNotExist:
                MachineTimeUsed(
                    term_school_year=term_school_year,
                    term_type=term_type,
                    province_name=province_name,
                    city_name=city_name,
                    country_name=country_name,
                    town_name=town_name,
                    school_name=school_name,
                    grade_name=grade_name,
                    class_name=class_name,
                    mac=mac,
                    school=school,
                    create_time=create_time,
                    use_time=use_time,
                    use_count=use_count).save()
            except:
                s = datetime.datetime.combine(create_time, datetime.time.min)
                e = datetime.datetime.now()
                obj = MachineTimeUsed.objects.filter(
                    term_school_year=term_school_year,
                    term_type=term_type,
                    province_name=province_name,
                    city_name=city_name,
                    country_name=country_name,
                    town_name=town_name,
                    school_name=school_name,
                    grade_name=grade_name,
                    class_name=class_name,
                    mac=mac,
                    school=school,
                    create_time__range=(s, e)).all().delete()
                logger.exception('')
                cursor.execute('UNLOCK TABLES;')
                cursor.close()
                return create_failure_dict()
            cursor.execute('UNLOCK TABLES;')
            cursor.close()
            return create_success_dict(msg='成功上传机器使用时长数据')

        return create_failure_dict(msg='机器使用时长数据上传失败', errors=f.errors)
