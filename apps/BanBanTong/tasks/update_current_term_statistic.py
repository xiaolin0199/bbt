# coding=utf-8
import logging
from BanBanTong.db import models
from django.conf import settings
DEBUG = settings.DEBUG

logger = logging.getLogger(__name__)


class Task(object):
    '''
        更新当前学年学期的数据
    '''
    if DEBUG:
        run_period = 30
    else:
        run_period = 60 * 60 * 3

    def __init__(self):
        server_type = models.Setting.getvalue('server_type')
        if server_type == 'school':
            term = models.Term.get_current_term_list()
            term = term and term[0] or None
        else:
            term = models.NewTerm.get_current_term()

        if not term:
            logger.debug('task-update-statictic-term: no term available')

        else:
            if DEBUG:
                logger.debug('task-update-statictic-term: %s %s' % (term.school_year, term.term_type))
            models.Statistic.update_all(term)
