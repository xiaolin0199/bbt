# coding=utf-8

import logging
from django.core.management.base import BaseCommand
from BanBanTong.db import models
from django.conf import settings
DEBUG = settings.DEBUG


logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, *args, **options):
        server_type = models.Setting.getvalue('server_type')
        if server_type == 'school':
           term = models.Term.get_current_term_list()
           term = term and term[0] or None
        else:
           term = models.NewTerm.get_current_term()
        if not term:
           return

        logger.debug('task-update-statictic-term: %s %s' % (term.school_year, term.term_type))
        models.Statistic.update_all(term)


def run_by_http(request):
    from django.http import HttpResponse
    cmd = Command()
    logger.debug('task-update-statictic-term: from http begin')
    cmd.handle()
    logger.debug('task-update-statictic-term: from http end')
    return HttpResponse('操作成功,<a href="/">返回</a>')