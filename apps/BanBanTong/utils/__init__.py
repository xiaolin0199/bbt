# coding=utf-8
import os
import datetime
import decimal
import json
import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict as django_model_to_dict
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models.query import QuerySet, ValuesIterable as ValuesQuerySet
DEBUG = settings.DEBUG


def is_admin(user):
    return user.username in settings.ADMIN_USERS


def get_page_info(request):
    order_field = None
    order_direction = None
    page_num = 1
    page_size = 30

    if request.GET.get('page'):
        try:
            page_num = int(request.GET.get('page'))
        except:
            pass

    if request.GET.get('limit'):
        try:
            page_size = int(request.GET.get('limit'))
        except:
            pass

    if request.GET.get('order_field'):
        order_field = request.GET.get('order_field')

    if request.GET.get('order_direction'):
        order_direction = request.GET.get('order_direction')

    return {
        'order_field': order_field,
        'order_direction': order_direction,
        'page_num': page_num,
        'page_size': page_size,
    }


class RevisedDjangoJSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time and decimal types.
    """

    def default(self, o):
        # See "Date Time String Format" in the ECMA-262 specification.
        if isinstance(o, datetime.datetime):
            r = o.strftime('%Y-%m-%d %H:%M:%S')
            if o.microsecond:
                r = r[:23] + r[26:]
            if r.endswith('+00:00'):
                r = r[:-6] + 'Z'
            return r
        elif isinstance(o, datetime.date):
            return o.isoformat()
        elif isinstance(o, datetime.time):
            # if is_aware(o):
            #    raise ValueError("JSON can't represent timezone-aware times.")
            r = o.isoformat()
            if o.microsecond:
                r = r[:12]
            return r
        elif isinstance(o, decimal.Decimal):
            return str(o)
        elif isinstance(o, uuid.UUID):
            return str(o)
        # elif isinstance(o, ValuesQuerySet) and not o:
        #     return []
        elif hasattr(o, 'to_dict'):
            return o.to_dict()
        else:
            try:
                return super(RevisedDjangoJSONEncoder, self).default(o)
            except:
                return str(o)


def create_failure_dict(**kwargs):
    if not DEBUG and 'debug' in kwargs:
        del kwargs['debug']
    elif 'debug' in kwargs:
        kwargs['#debug'] = kwargs['debug']
        del kwargs['debug']
    ret = {'status': 'failure'}
    ret.update(kwargs)
    return ret


def create_success_dict(**kwargs):
    if not DEBUG and 'debug' in kwargs:
        del kwargs['debug']
    elif 'debug' in kwargs:
        kwargs['#debug'] = kwargs['debug']
        del kwargs['debug']
    ret = {'status': 'success', 'success': True}
    ret.update(kwargs)
    return ret


def get_all_privilege_keys(privileges):
    keys = []
    for p in privileges:
        # p['name'] = _('Privilege:%s' % p['key'])

        if 'privileges' in p:
            keys += get_all_privilege_keys(p['privileges'])
        else:
            keys.append(p['key'])

    return keys


def get_ip(request):
    return request.META['REMOTE_ADDR']


def get_macs():
    ifconfig = os.popen('ifconfig -a|grep HWaddr').read().lower().split('\n')
    macs = [line.split('hwaddr')[-1] for line in ifconfig]
    macs = [mac.replace(' ', '').replace(':', '').upper() for mac in macs if mac]
    return macs


def model_to_dict(instance, max_depth=5, depth=0, *args, **kw):
    if isinstance(instance, models.Model):
        return instance.to_dict()
    if isinstance(instance, dict):
        return instance
    if not hasattr(instance, '_meta'):
        return None

    opts = instance._meta
    depth += 1
    data = django_model_to_dict(instance, *args, **kw)
    fields = kw.get('fields') or []
    exclude = kw.get('exclude') or []
    for field_name in opts.get_all_field_names():
        if fields and field_name in fields:
            continue
        if exclude and field_name in exclude:
            continue
        _cached_key = '_%s_cache' % field_name
        field = opts.get_field_by_name(field_name)[0]
        if field.__class__.__name__ in ('DateTimeField', 'DateField',
                                        'TimeField'):
            value = getattr(instance, field_name)
            data[field_name] = None
            if value or value == datetime.time(0, 0):
                if field.__class__.__name__ == 'DateTimeField':
                    data[field_name] = value.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    data[field_name] = value.isoformat()
        elif field.__class__.__name__ == 'ForeignKey':
            if _cached_key in instance.__dict__:
                if depth >= max_depth:
                    continue
                data[field_name] = {}
                try:
                    value = getattr(instance, field_name)
                except (ObjectDoesNotExist, AttributeError):
                    continue
                data[field_name] = model_to_dict(value, depth=depth)
        elif field.__class__.__name__ in ('RelatedObject', 'ManyToManyField'):
            if field_name in data:
                del data[field_name]
        else:
            data[field_name] = field.value_from_object(instance)

    return data


def model_list_to_dict(instances, max_depth=2, depth=0):
    _list = []

    for instance in instances:
        _list.append(model_to_dict(instance, max_depth=max_depth, depth=depth))

    return _list

# MH


def paginatoooor(request, q, **kwargs):
    """封装django自带的分页组件"""
    page_info = get_page_info(request)
    order_field = page_info['order_field']
    order_direction = page_info['order_direction']
    page_num = page_info['page_num']
    page_size = page_info['page_size']
    pag = Paginator(q, page_size)

    try:
        records = pag.page(page_num)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        records = pag.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        records = pag.page(pag.num_pages)

    # # 排序
    if order_field:
        order_fields = []
        if isinstance(order_field, (str, unicode)):
            if order_direction == 'desc':
                order_fields.append('-%s' % order_field)

            else:
                order_fields.append(order_field)

        elif isinstance(order_field, list):
            for f in order_field:
                if order_direction == 'desc':
                    order_fields.append('-%s' % f)

                else:
                    order_fields.append(f)
        if order_fields:
            try:
                pag = pag.order_by(*order_fields)
            except Exception:
                pass
        '''
        try:
            records = records.all()[offset:offset + page_size]
        except Exception,e:
            records = records[offset:offset + page_size]
        '''

    paged = create_success_dict(data={
        'page': page_num,
        'page_size': page_size,
        'record_count': pag.count,
        'page_count': pag.num_pages,
        'records': model_list_to_dict(records)
    })
    paged['data'].update(kwargs)
    return paged


def page_object(request, q, **kwargs):
    # 将querys分页,返回分页信息和单页queryset供二次格式化
    page_info = get_page_info(request)
    pag = Paginator(q, page_info['page_size'])
    try:
        if isinstance(q, QuerySet):
            records = pag.page(page_info['page_num']).object_list
        elif isinstance(q, ValuesQuerySet):
            records = pag.page(page_info['page_num'])
        else:
            records = pag.page(page_info['page_num'])
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        if isinstance(q, QuerySet):
            records = pag.page(1).object_list
        elif isinstance(q, ValuesQuerySet):
            records = pag.page(1)
        else:
            records = pag.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        if isinstance(q, QuerySet):
            records = pag.page(pag.num_pages).object_list
        elif isinstance(q, ValuesQuerySet):
            records = pag.page(pag.num_pages)
        else:
            records = pag.page(pag.num_pages)
    data = {
        'page_count': pag.num_pages,
        'record_count': pag.count,
        'page': page_info['page_num'],
        'page_size': page_info['page_size'],
        'records': [],
    }
    data.update(kwargs)
    return records, data  # 本页数据, 分页信息
