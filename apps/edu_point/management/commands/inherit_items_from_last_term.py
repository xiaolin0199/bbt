# coding=utf-8
from edu_point import models
from django.core.management.base import BaseCommand
from BanBanTong.db.models import NewTerm, Setting


class Command(BaseCommand):
    """
    新建学年学期后,将旧学年学期的教学点基础数据继承到新的学年学期
    基础数据包括:
        EduPoint
        # EduPointResourceCatalog
        EduPointDetail
    """

    def handle(self, *args, **options):
        server_type = Setting.getvalue('server_type')
        if server_type != 'country':
            print 'Wrong server_type'
            raise Exception(u'错误的服务器级别')

        term = NewTerm.get_current_or_next_term()
        if not term:
            print 'There is no term available in the database'
            raise Exception(u'无可用学年学期')
        print 'current term', term.school_year, term.term_type

        pre_term = NewTerm.get_previous_term(term=term)
        if not pre_term:
            print 'There is no pre_term'
            raise Exception(u'无可用学年学期')
        print 'pre_term', pre_term.school_year, pre_term.term_type

        objs1 = models.EduPoint.objects.filter(
            school_year=pre_term.school_year,
            term_type=pre_term.term_type
        )

        for o in objs1:
            point, is_new = models.EduPoint.objects.get_or_create(
                school_year=term.school_year,
                term_type=term.term_type,
                province_name=o.province_name,
                city_name=o.city_name,
                country_name=o.country_name,
                town_name=o.town_name,
                point_name=o.point_name,
                number=o.number,
                remark=o.remark,
                communicate_key=o.communicate_key
            )

            if is_new:
                print 'create one edupoint item:', point.point_name

            objs = list(o.edupointdetail_set.all())
            if is_new:
                print 'child_set count:', objs.count()
            for oo in objs:
                models.EduPointDetail.objects.create(
                    edupoint=point,
                    type=oo.type,
                    name=oo.name,
                    communicate_key=oo.communicate_key,
                    grade_name=oo.grade_name,
                    class_name=oo.class_name,
                    cpuID=oo.cpuID,
                    need_confirm=True
                )


def run_by_http(request):
    from django.http import HttpResponse
    cmd = Command()
    cmd.handle()
    return HttpResponse('数据继承完毕,<a href="/">返回</a>')


def run_as_view(*args, **kwargs):
    cmd = Command()
    cmd.handle()
