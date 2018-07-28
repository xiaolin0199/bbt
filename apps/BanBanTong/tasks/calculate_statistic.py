# coding=utf-8
import logging
from BanBanTong.db.models import Term, NewTerm
from BanBanTong.db.models import Statistic, Setting
from django.conf import settings
DEBUG = settings.DEBUG
del settings

logger = logging.getLogger(__name__)


class Task(object):
    '''
        计算统计分析的数据(只计算历史学期的数据)
    '''
    if DEBUG:
        run_period = 60 * 5
    else:
        run_period = 60 * 60 * 5

    def handle(self, *args, **options):
        server_type = Setting.getvalue('server_type')
        if server_type != 'school':
            current_term = NewTerm.get_current_term()
            terms = NewTerm.objects.all()
            if current_term:
                terms = terms.exclude(pk=current_term.pk)
        else:
            current_term = Term.get_current_term_list()
            terms = Term.objects.all()
            if current_term:
                uuids = [o.pk for o in current_term]
                terms = terms.exclude(pk__in=uuids)

        uuids = Setting.objects.filter(name='task-init-statictic-term')
        uuids = list(uuids.values_list('value', flat=True))
        if uuids:
            terms = terms.exclude(pk__in=uuids)

        for term in terms:
            logger.debug('task-init-statictic-term: %s %s' % (term.school_year, term.term_type))
            Statistic.init_all(term)
            Statistic.update_all(term)

    def __init__(self):
        self.handle()


def test_task(debug=False):
    if debug or DEBUG:
        o = Task()
        o.handle()


def run_by_http(request, *args, **kwargs):
    from django.http import HttpResponse
    debug = DEBUG or False
    test_task(debug)
    return HttpResponse('综合分析历史数据更新完毕,<a href="/">返回</a>')
