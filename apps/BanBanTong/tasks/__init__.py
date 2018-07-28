# coding=utf-8
import logging
from BanBanTong.utils import decorator


logger = logging.getLogger(__name__)


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_user')
def run_task(request, name):
    if name == 'sync_baseinfo':
        from . import sync_baseinfo
        sync_baseinfo.Task(force=True)


__all__ = [  # noqa
    'calculate_teacher_finished_time',  # noqa
    'desktop_preview',  # noqa
    # 'export_statistics_teaching_time', # noqa
    # 'export_statistics_time_used', # noqa
    'ntpdate',  # noqa
    'optimize_db',  # noqa
    'sync_country_to_resourceplatform',  # noqa
    'sync_country_to_school',  # noqa
    'teaching_analysis',  # noqa
    # 'teach_monitor', # 锐哥说不要不要 # noqa
    'term_lesson_resource',  # noqa
    'time_used',  # noqa
    'calculate_statistic',  # noqa
    'backup_db_to_qiniu',  # noqa
    'scheduler_remote_shutdown',  # noqa
    'update_current_term_statistic',  # noqa
    'sync_baseinfo',  # noqa
]
