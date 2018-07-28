#!/usr/bin/env python
# coding=utf-8
import ConfigParser
import datetime
import logging
import os
import pymongo
import pypinyin
from django.db.models import fields
from django.utils.dateparse import parse_date
from BanBanTong import constants
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import get_page_info

logger = logging.getLogger(__name__)


def _get_conn():
    SETTINGS_FILE = os.path.join(constants.BANBANTONG_BASE_PATH, '..', 'mongo.ini')
    if not os.path.isfile(SETTINGS_FILE):
        return
    config = ConfigParser.SafeConfigParser()
    config.read(SETTINGS_FILE)
    try:
        HOST = config.get('mongodb', 'host')
    except:
        HOST = '127.0.0.1'
    try:
        PORT = config.getint('mongodb', 'port')
    except:
        PORT = 27017
    try:
        client = pymongo.MongoClient(host=HOST, port=PORT, max_pool_size=1,
                                     connectTimeoutMS=1000)
    except:
        logger.exception('')
        return
    return client


def class_to_dict(obj):
    d = {'province_name': obj.grade.term.school.parent.parent.parent.parent.name,
         'city_name': obj.grade.term.school.parent.parent.parent.name,
         'country_name': obj.grade.term.school.parent.parent.name,
         'town_name': obj.grade.term.school.parent.name,
         'school_name': obj.grade.term.school.name,
         'school_year': obj.grade.term.school_year,
         'term_type': obj.grade.term.term_type,
         'start_date': datetime.datetime.combine(obj.grade.term.start_date,
                                                 datetime.time.min),
         'end_date': datetime.datetime.combine(obj.grade.term.end_date,
                                               datetime.time.max),
         'grade_name': obj.grade.name,
         'class_name': obj.name}
    d['province_pinyin'] = ' '.join(pypinyin.lazy_pinyin(d['province_name'],
                                                         style=pypinyin.TONE2))
    d['city_pinyin'] = ' '.join(pypinyin.lazy_pinyin(d['city_name'],
                                                     style=pypinyin.TONE2))
    d['country_pinyin'] = ' '.join(pypinyin.lazy_pinyin(d['country_name'],
                                                        style=pypinyin.TONE2))
    d['town_pinyin'] = ' '.join(pypinyin.lazy_pinyin(d['town_name'],
                                                     style=pypinyin.TONE2))
    d['school_pinyin'] = ' '.join(pypinyin.lazy_pinyin(d['school_name'],
                                                       style=pypinyin.TONE2))
    return d


def save_class(obj):
    client = _get_conn()
    if not client:
        return
    table = client.banbantong.classes
    try:
        d = class_to_dict(obj)
        table.insert(d)
    except:
        logger.exception('')
    finally:
        client.close()


def get_teacherloginlog(request):
    client = _get_conn()
    if not client:
        return
    table = client.banbantong.teacherloginlog
    try:
        page_info = get_page_info(request)
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        lesson_period = request.GET.get('lesson_period')
        country_name = request.GET.get('country_name')
        town_name = request.GET.get('town_name')
        school_name = request.GET.get('school_name')
        grade_name = request.GET.get('grade_name')
        class_name = request.GET.get('class_name')
        lesson_name = request.GET.get('lesson_name')
        teacher_name = request.GET.get('teacher_name')

        cond = {}
        if start_date:
            s = datetime.datetime.combine(parse_date(start_date),
                                          datetime.time.min)
            cond['created_at'] = {'$gte': s}
        if end_date:
            e = datetime.datetime.combine(parse_date(end_date),
                                          datetime.time.max)
            if 'created_at' not in cond:
                cond['created_at'] = {}
            cond['created_at']['$lte'] = e
        if lesson_period:
            cond['lesson_period_sequence'] = lesson_period
        if country_name:
            cond['country_name'] = country_name
        if town_name:
            cond['town_name'] = town_name
        if school_name:
            cond['school_name'] = school_name
        if grade_name:
            cond['grade_name'] = grade_name
        if class_name:
            cond['class_name'] = class_name
        if lesson_name:
            cond['lesson_name'] = {'$regex': lesson_name}
        if teacher_name:
            cond['teacher_name'] = {'$regex': teacher_name}

        fields = ['uuid', 'province_name', 'city_name', 'country_name', 'town_name',
                  'school_name', 'grade_name', 'class_name', 'teacher_name',
                  'lesson_period_sequence', 'lesson_name', 'created_at',
                  'time_used']
        proj = {}
        for i in fields:
            proj[i] = True
        proj['_id'] = False
        skip = (page_info['page_num'] - 1) * page_info['page_size']
        limit = page_info['page_size']
        cursor = table.find(spec=cond, fields=proj, skip=skip, limit=limit,
                            sort=[('created_at', pymongo.DESCENDING)])
        record_count = cursor.count()
        page_count = (record_count + limit - 1) / limit
        records = []
        for row in cursor:
            records.append(row)
        cursor.close()
        client.close()
        return create_success_dict(data={
            'records': records,
            'page': page_info['page_num'],
            'page_size': page_info['page_size'],
            'record_count': record_count,
            'page_count': page_count,
        })
    except:
        logger.exception('')
        return create_failure_dict(msg='系统错误')


def count_teacherloginlog(cond):
    client = _get_conn()
    if not client:
        return
    table = client.banbantong.teacherloginlog
    try:
        start_date = cond.get('start_date')
        end_date = cond.get('end_date')
        lesson_period = cond.get('lesson_period')
        country_name = cond.get('country_name')
        town_name = cond.get('town_name')
        school_name = cond.get('school_name')
        grade_name = cond.get('grade_name')
        class_name = cond.get('class_name')
        lesson_name = cond.get('lesson_name')
        teacher_name = cond.get('teacher_name')

        cond = {}
        if start_date:
            s = datetime.datetime.combine(parse_date(start_date),
                                          datetime.time.min)
            cond['created_at'] = {'$gte': s}
        if end_date:
            e = datetime.datetime.combine(parse_date(end_date),
                                          datetime.time.max)
            if 'created_at' not in cond:
                cond['created_at'] = {}
            cond['created_at']['$lte'] = e
        if lesson_period:
            cond['lesson_period_sequence'] = lesson_period
        if country_name:
            cond['country_name'] = country_name
        if town_name:
            cond['town_name'] = town_name
        if school_name:
            cond['school_name'] = school_name
        if grade_name:
            cond['grade_name'] = grade_name
        if class_name:
            cond['class_name'] = class_name
        if lesson_name:
            cond['lesson_name'] = {'$regex': lesson_name}
        if teacher_name:
            cond['teacher_name'] = {'$regex': teacher_name}

        cursor = table.find(spec=cond)
        count = cursor.count()
        cursor.close()
        client.close()
        return count
    except:
        logger.exception('')
        return -1


def _obj_to_dict(obj):
    ret = {}
    for field in obj._meta.fields:
        v = getattr(obj, field.name)
        if isinstance(field, fields.related.ForeignKey):
            if v:
                ret[field.name] = v.pk
            else:  # Foreignkey为null
                ret[field.name] = None
        elif isinstance(v, datetime.datetime):
            ret[field.name] = v
        elif isinstance(v, datetime.date):
            # MongoDB(BSON)不支持date和time，需要转为datetime
            ret[field.name] = datetime.datetime.combine(v, datetime.time.min)
        elif isinstance(v, datetime.time):
            ret[field.name] = datetime.datetime.combine(datetime.date(1900, 1, 1), v)
        elif isinstance(field, (fields.CharField, fields.IntegerField)):
            ret[field.name] = v
        else:
            # 还有什么没处理的类型？
            ret[field.name] = v
    return ret


def save_teacherloginlog(obj):
    client = _get_conn()
    if not client:
        return
    table = client.banbantong.teacherloginlog
    try:
        d = _obj_to_dict(obj)
        table.insert(d)
    except:
        logger.exception('')
    finally:
        client.close()


def save_teacherlogintime(obj):
    client = _get_conn()
    if not client:
        return
    table = client.banbantong.teacherloginlog
    try:
        table.update({'uuid': obj.teacherloginlog.uuid},
                     {'$set': {'time_used': obj.login_time}})
    except:
        logger.exception('')
    finally:
        client.close()
