# coding=utf-8
import datetime
import os
import traceback
import uuid
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db.models import Count
from django.utils.dateparse import parse_date
from BanBanTong import constants
from BanBanTong.db import models
from BanBanTong.db import utils as db_utils
from BanBanTong.forms.teacher import TeacherForm
from BanBanTong.forms.teacher import TeacherUploadForm
from BanBanTong.forms.teacher import TeacherUploadVerifyForm
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import get_page_info
from BanBanTong.utils import model_list_to_dict
from BanBanTong.utils import model_to_dict
import xlwt
from BanBanTong.utils.translate import trans2pinyin


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_teacher')
def add(request, *args, **kwargs):
    if request.method == 'POST':
        name = request.POST.get('name')
        birthday = request.POST.get('birthday')
        birthday = parse_date(birthday)
        if not (name and birthday):
            return create_failure_dict(msg=u'教师名和出生年月是必填字段.')
        school = models.Group.objects.get(group_type='school')
        names = [name, '%s(%s)' % (name, birthday.strftime('%y%m%d'))]
        objs = models.Teacher.objects.filter(
            name__in=names,
            school=school
        )
        if objs.exists():
            for obj in objs:
                if obj.birthday == birthday:
                    if obj.deleted:
                        obj.deleted = False
                        obj.save()
                    return create_success_dict(msg=u'添加教师成功！', data=obj.to_dict())

            name = '%s(%s)' % (name, birthday.strftime('%y%m%d'))

        try:
            instance = models.Teacher.objects.get(
                name=name,
                birthday=birthday,
                school=school,
                deleted=True
            )
        except models.Teacher.DoesNotExist:
            record = TeacherForm(request.POST)
        else:
            record = TeacherForm(request.POST, instance=instance)

        if record.is_valid():
            teacher = record.save(commit=False)
            teacher.school = school
            teacher.deleted = False
            teacher.save()
            return create_success_dict(msg=u'添加教师成功！', data=teacher.to_dict())
        else:
            return create_failure_dict(msg=u'添加教师失败！', errors=record.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_teacher')
def delete(request, *args, **kwargs):
    if request.method == 'POST':
        teacher_uuid = request.POST.get('uuid')
        try:
            t = models.Teacher.objects.get(uuid=teacher_uuid)
        except:
            return create_failure_dict(msg='错误的uuid')
        if t.lessonteacher_set.filter(class_uuid__grade__term__deleted=False).count() > 0:
            return create_failure_dict(msg='该教师有班级课程老师记录，不能删除')
        t.deleted = True
        t.save()
        return create_success_dict(msg='删除教师成功！')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_teacher')
def detail(request, *args, **kwargs):
    if request.method == 'GET':
        try:
            uu = request.GET.get('uuid')
            obj = models.Teacher.objects.get(uuid=uu)
            data = model_to_dict(obj)
            return create_success_dict(data=data)
        except:
            return create_failure_dict(msg='错误的uuid！')


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_teacher')
def edit(request, *args, **kwargs):
    # 如果编辑教师时，修改教师的生日，导致(name, birthday, school)
    # 与已删除的隐藏记录重复，这里先删掉隐藏教师。
    if request.method == 'POST':
        try:
            uu = request.POST.get('uuid')
            record = models.Teacher.objects.get(uuid=uu)
        except:
            traceback.print_exc()
            return create_failure_dict(msg='错误的uuid！')

        teacher_form = TeacherForm(request.POST, instance=record)

        if teacher_form.is_valid():
            teacher = teacher_form.save(commit=False)
            school = models.Group.objects.get(group_type='school')
            teacher.school = school
            try:
                teacher.save()
            except IntegrityError, e:
                if 'Duplicate entry' in str(e):
                    return create_failure_dict(msg='已存在同名且同生日的教师')
                old = models.Teacher.objects.get(
                    name=teacher.name,
                    school=school,
                    birthday=teacher.birthday,
                    deleted=True
                )
                old.delete()
                teacher.save()
            except Exception as e:
                traceback.print_exc()
                return create_failure_dict(msg='服务器错误', debug=str(e))
            return create_success_dict(msg='编辑教师成功！',
                                       data=model_to_dict(teacher))

        return create_failure_dict(msg='编辑教师失败！', errors=teacher_form.errors)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_teacher')
def import_from(request, *args, **kwargs):
    if request.method == 'POST':
        try:
            f = TeacherUploadForm(request.POST, request.FILES)
            if f.is_valid():
                teachers = f.save()
                return create_success_dict(data=model_list_to_dict(teachers))
            return create_failure_dict(
                msg='导入教职人员基础信息失败！',
                errors=f.errors
            )
        except:
            traceback.print_exc()


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_teacher')
def export(request, *args, **kwargs):
    # pt = datetime.datetime.strptime
    xls = xlwt.Workbook(encoding='utf8')
    title = u'教职人员信息'
    sheet = xls.add_sheet(title)
    head = [u'ID', u'姓名', u'性别', u'学历', u'出生年月',
            u'教师职称', u'注册时间', u'移动电话', u'QQ', u'备注']
    for i in range(len(head)):
        sheet.write(0, i, head[i])
    row = 1
    q = models.Teacher.objects.filter(deleted=False)
    q = q.values('sequence', 'name', 'sex', 'edu_background', 'birthday',
                 'title', 'register_at', 'mobile', 'qq', 'remark')
    for i in q:
        sheet.write(row, 0, i['sequence'])
        sheet.write(row, 1, i['name'])
        if i['sex'] == u'male':
            sex = u'男'
        else:
            sex = u'女'
        sheet.write(row, 2, sex)
        sheet.write(row, 3, i['edu_background'])
        birthday = str(i['birthday']).replace('-', '')
        # sheet.write(row, 4, pt(birthday, '%Y%m%d').strftime('%Y-%m-%d'))
        sheet.write(row, 4, birthday)
        sheet.write(row, 5, i['title'])
        sheet.write(row, 6, str(i['register_at']))
        sheet.write(row, 7, i['mobile'])
        sheet.write(row, 8, i['qq'])
        sheet.write(row, 9, i['remark'])
        row += 1
    cached_id = str(uuid.uuid1())
    tmp_file = os.path.join(constants.CACHE_TMP_ROOT, cached_id)
    xls.save(tmp_file)
    filename = u'%s.xls' % title
    return create_success_dict(url=reverse('base:xls_download',
                                           kwargs={'cached_id': cached_id,
                                                   'name': filename}))


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_teacher')
def list_current(request, *args, **kwargs):
    page_info = get_page_info(request)
    edu_background = request.GET.get('edu_background')
    sex = request.GET.get('sex')
    status = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    teacher_name = request.GET.get('teacher_name')
    title = request.GET.get('title')
    trans_2_pinyin = request.GET.get('trans2pinyin', False)
    terms = models.Term.objects.filter(deleted=False)
    q = models.Teacher.objects.filter(deleted=False)
    if edu_background:
        q = q.filter(edu_background=edu_background)
    if sex:
        if sex == u'男':
            sex = 'male'
        else:
            sex = 'female'
        q = q.filter(sex=sex)

    recount_status = False
    if status:
        if status == u'授课':
            q = q.annotate(status_count=Count('lessonteacher')).filter(lessonteacher__class_uuid__grade__term__in=terms)
        else:
            if terms:
                q = q.annotate(status_count=Count('lessonteacher')).exclude(lessonteacher__class_uuid__grade__term__in=terms)
                recount_status = True
            else:
                q = q.annotate(status_count=Count('lessonteacher'))
                recount_status = True
    else:
        q = q.annotate(status_count=Count('lessonteacher'))
        recount_status = True

    if start_date and end_date:
        s = parse_date(start_date)
        e = parse_date(end_date)
        s = datetime.datetime.combine(s, datetime.time.min)
        e = datetime.datetime.combine(e, datetime.time.max)
        q = q.filter(register_at__range=(s, e))
    if teacher_name:
        q = q.filter(name__contains=teacher_name)
    if title:
        q = q.filter(title=title)
    q = q.values('uuid', 'sequence', 'name', 'sex', 'edu_background',
                 'birthday', 'title', 'register_at', 'mobile', 'qq',
                 'status_count', 'remark')

    if recount_status:
        q = list(q)
        for one in q:
            if one['status_count'] > 0:
                obj = models.Teacher.objects.get(uuid=one['uuid'])
                if not obj.lessonteacher_set.filter(class_uuid__grade__term__in=terms):
                    one['status_count'] = 0
    if trans_2_pinyin == 'true':
        q = list(q)
        for o in q:
            o.update(trans2pinyin(o['name']))

    page_data = db_utils.pagination(q, **page_info)

    return create_success_dict(data={
        'records': model_list_to_dict(page_data['records']),
        'page': page_data['page_num'],
        'page_size': page_data['page_size'],
        'record_count': page_data['record_count'],
        'page_count': page_data['page_count'],
    })


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_teacher')
def verify(request, *args, **kwargs):
    if request.method == 'POST':
        try:
            f = TeacherUploadVerifyForm(request.POST, request.FILES)
            if f.is_valid():
                objs = f.save()
                return create_success_dict(data=model_list_to_dict(objs))
            return create_failure_dict(msg='验证教职人员基础信息失败！',
                                       errors=f.errors)
        except:
            traceback.print_exc()


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_teacher')
def reset_pwd(request, *args, **kwargs):
    uuid = request.POST.get('uuid', None)
    try:
        o = models.Teacher.objects.get(uuid=uuid)
        pwd = o.birthday.strftime('%m%d')
        o.password = pwd
        o.save()
        return create_success_dict(data={'pwd': pwd})
    except:
        return create_failure_dict(msg='错误的uuid')
