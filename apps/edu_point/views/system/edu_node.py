# coding=utf-8
import logging

from django import forms
from django.core.paginator import Paginator
from django.core.cache import cache

from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import model_list_to_dict
from BanBanTong.utils import get_page_info

from edu_point.models import EduPoint, EduPointResourceCatalog
from activation.decorator import get_none_activate
from BanBanTong.db.models import Setting, NewTerm

logger = logging.getLogger(__name__)


class EduPointUploadForm(forms.ModelForm):

    def clean_number(self):
        # 欲分配
        number = self.cleaned_data.get('number', 0)
        # 可分配
        none_number = get_none_activate()

        # 欲分配不合法
        if number < 0:
            raise forms.ValidationError(u'新增教学点: 欲分配授权终端数量需为正整数')

        # 已无可分配的数量
        if none_number <= 0:
            raise forms.ValidationError(u'新增教学点: 已无可分配授权终端数量')
        else:
            # 欲分配  > 可分配
            if number > none_number:
                raise forms.ValidationError(u'新增教学点: 可分配授权终端数量已不足')

        return number

    class Meta:
        model = EduPoint
        exclude = ['create_time', 'update_time']


class EduPointEditForm(forms.ModelForm):

    def clean_number(self):
        # 原分配
        old_number = self.instance.number
        # 欲分配
        number = self.cleaned_data.get('number', 0)
        # 可分配
        none_number = get_none_activate()

        # 欲分配不合法
        if number < 0:
            raise forms.ValidationError(u'更新教学点: 欲分配授权终端数量需为正整数')

        # 已无可分配的数量
        if none_number <= 0:
            if number > old_number:
                raise forms.ValidationError(u'更新教学点: 可分配授权终端数量不足，请更新授权')
        else:
            # 欲分配 - 原分配 > 可分配
            if number - old_number > none_number:
                raise forms.ValidationError(u'更新教学点: 可分配授权终端数量不足，请更新授权')

        return number

    class Meta:
        model = EduPoint
        fields = ['number', 'remark']


class EduPointResourceCatalogForm(forms.ModelForm):

    class Meta:
        model = EduPointResourceCatalog
        fields = ['catalog']


# 教学点管理
def list(request, *args, **kwargs):
    """
        教学点管理>列表显示
    """
    school_year = request.GET.get('school_year')
    term_type = request.GET.get('term_type')
    town_name = request.GET.get('town_name')
    point_name = request.GET.get('point_name')

    q = EduPoint.objects.all()
    if school_year or term_type:
        if school_year:
            q = q.filter(school_year=school_year)
        if term_type:
            q = q.filter(term_type=term_type)
    else:
        term = NewTerm.get_nearest_term()
        if term:
            q = q.filter(
                school_year=term.school_year,
                term_type=term.term_type
            )

    if town_name:
        q = q.filter(town_name=town_name)
    if point_name:
        q = q.filter(point_name=point_name)

    page_info = get_page_info(request)

    q = q.values('id', 'school_year', 'term_type', 'town_name', 'point_name', 'number', 'remark').distinct()

    # 添加一个uuid,与id是一样的
    map(lambda x: x.setdefault('uuid', x['id']), q)

    paginator = Paginator(q, page_info['page_size'])
    records = paginator.page(page_info['page_num']).object_list

    ret = create_success_dict(data={
        'page': page_info['page_num'],
        'page_count': paginator.num_pages,
        'page_size': page_info['page_size'],
        'record_count': paginator.count,
        'records': model_list_to_dict(records),
    })

    return ret


def add(request, *args, **kwargs):
    '''
        教学点管理>添加
    '''
    def _getvalue(name):
        return Setting.getvalue(name)

    term = NewTerm.get_current_or_next_term()
    if not term:
        return create_failure_dict(msg=u'无可用学年学期')

    if request.method == 'POST':
        if _getvalue('server_type') != 'country':
            return create_failure_dict(msg='教学点仅支持县级服务器')

        f = EduPointUploadForm(request.POST)
        if f.is_valid():
            # 新建教学点
            cleaned_data = f.cleaned_data
            obj, c = EduPoint.objects.get_or_create(
                school_year=cleaned_data['school_year'],
                term_type=cleaned_data['term_type'],
                province_name=_getvalue('province'),
                city_name=_getvalue('city'),
                country_name=_getvalue('country'),
                town_name=cleaned_data['town_name'],
                point_name=cleaned_data['point_name'].replace(' ', ''),
                defaults={
                    'number': cleaned_data['number'],
                    'remark': cleaned_data['remark'],
                }
            )
            if c:
                return create_success_dict(msg='成功添加教学点')
            else:
                return create_failure_dict(msg='不能重复添加教学点')

        return create_failure_dict(msg='教学点添加失败', errors=f.errors)


def edit(request):
    '''
        教学点管理>编辑
    '''
    if request.method == 'POST':
        if Setting.getvalue('server_type') != 'country':
            return create_failure_dict(msg='教学点仅支持县级服务器')

        id = request.POST.get('uuid')
        obj = EduPoint.objects.get(id=id)

        f = EduPointEditForm(request.POST, instance=obj)
        if f.is_valid():
            number = f.cleaned_data['number']
            remark = f.cleaned_data['remark']
            if number < obj.number:
                return create_failure_dict(msg='教学点修改终端数量不能小于原始数量')

            obj.number = number
            obj.remark = remark
            obj.save()

            return create_success_dict(msg='成功编辑教学点')

        return create_failure_dict(msg='教学点添加失败', errors=f.errors)


def delete(request, *args, **kwargs):
    """
        教学点管理>删除节点
    """
    if request.method == 'POST':
        if not cache.get('sudo'):
            return create_failure_dict(msg='请输入正确的超级管理员admin密码！')

        if Setting.getvalue('server_type') != 'country':
            return create_failure_dict(msg='教学点仅支持县级服务器')

        id = request.POST.get('uuid')
        try:
            obj = EduPoint.objects.get(id=id)
        except Exception, e:
            logger.exception(e)
            return create_failure_dict(msg='无该教学点ID, 不能删除')

        # 如果该教学点下的教室有已申报的情况，需要提示先取消申报才可删除教学点
        if not obj.has_delete():
            return create_failure_dict(msg='先解除终端绑定,才能删除教学点！')

        obj.delete()

        return create_success_dict(msg='成功删除教学点')


def resource_catalog_list(request):
    '''
        教学点对应的卫星资源接收目录列表
    '''
    id = request.GET.get('uuid')
    try:
        obj = EduPoint.objects.get(id=id)
    except Exception, e:
        logger.exception(e)
        return create_failure_dict(msg='无该教学点ID')

    records = obj.edupointresourcecatalog_set.all().values('id', 'edupoint_id', 'catalog')

    # 添加一个uuid,与id是一样的
    map(lambda x: x.setdefault('uuid', x['id']), records)

    ret = create_success_dict(data={
        'records': model_list_to_dict(records),
    })

    return ret


def resource_catalog_add(request):
    '''
        教学点对应的卫星资源接收目录添加
    '''
    if request.method == 'POST':
        if Setting.getvalue('server_type') != 'country':
            return create_failure_dict(msg='教学点仅支持县级服务器')

        f = EduPointResourceCatalogForm(request.POST)
        if f.is_valid():
            catalog = f.cleaned_data['catalog']
            edupoint_id = request.POST.get('edupoint_id')
            try:
                edupoint = EduPoint.objects.get(id=edupoint_id)
            except Exception, e:
                logger.exception(e)
                return create_failure_dict(msg='无该教学点ID')

            if edupoint.edupointresourcecatalog_set.all().count() >= 10:
                return create_failure_dict(msg='教学点只能拥有10个资源接收目录')

            obj, c = EduPointResourceCatalog.objects.get_or_create(edupoint=edupoint, catalog=catalog)

            if not c:
                return create_failure_dict(msg='教学点不能保存相同的资源接收目录')

            return create_success_dict(msg='成功添加教学点卫星资源接收目录')


def resource_catalog_delete(request):
    '''
        教学点对应的卫星资源接收目录删除
    '''
    if request.method == 'POST':
        if not cache.get('sudo'):
            return create_failure_dict(msg='请输入正确的超级管理员admin密码！')

        if Setting.getvalue('server_type') != 'country':
            return create_failure_dict(msg='教学点仅支持县级服务器')

        id = request.POST.get('uuid')

        try:
            obj = EduPointResourceCatalog.objects.get(id=id)
        except Exception, e:
            logger.exception(e)
            return create_failure_dict(msg='教学点没有该卫星资源接收目录')

        obj.delete()

        return create_success_dict(msg='成功删除教学点卫星资源接收目录')


def resource_catalog_list_new(request):
    '''
        教学点对应的卫星资源接收目录列表
    '''
    o = Setting.objects.filter(name='resource_catalog')
    records = o.values('uuid', 'name', 'value')

    ret = create_success_dict(data={
        'records': model_list_to_dict(records),
    })
    return ret


def resource_catalog_add_new(request):
    '''
        教学点对应的卫星资源接收目录添加
    '''
    if Setting.getvalue('server_type') != 'country':
        return create_failure_dict(msg=u'资源接收目录仅支持县级服务器')

    path = request.REQUEST.get('catalog', None)
    if not path:
        return create_failure_dict(msg=u'未获取到资源接收目录')

    if Setting.objects.filter(name='resource_catalog').count() > 9:
        return create_failure_dict(msg=u'最多添加10个资源接收目录')
    o, is_new = Setting.objects.get_or_create(
        name='resource_catalog',
        value=path
    )
    o.save()
    return create_success_dict(msg=u'成功设定资源接收目录')


def resource_catalog_delete_new(request):
    uuid = request.POST.get('uuid', None)
    if not uuid:
        return create_failure_dict(msg=u'参数获取失败.')
    Setting.objects.filter(pk=uuid, name='resource_catalog').all().delete()
    return create_success_dict(msg=u'删除资源接收目录完毕.')
