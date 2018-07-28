# coding=utf-8
import bz2
import json
import traceback
from django.db import connection
from BanBanTong.db import models
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils import decorator
from BanBanTong.utils import is_admin
from BanBanTong.views.system.install import _truncate_tables


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('system_restore')
def restore(request, *args, **kwargs):
    if request.method == 'POST':
        if not is_admin(request.current_user):
            return create_failure_dict(msg='只有系统管理员admin才能执行此操作！')
        try:
            f = request.FILES.get('excel')
            data = ''
            for chunk in f.chunks():
                data += chunk
            data = bz2.decompress(data)
            lines = data.split('\n')
            # 清空数据库
            _truncate_tables()
            meta = {}
            for line in lines:
                if len(line) == 0:
                    continue
                if line.startswith('meta:'):
                    # print line
                    meta = json.loads(line[5:])
                else:
                    models.SyncLogPack.unpack_log('add', line)
            # 清空SyncLog
            models.SyncLog.objects.all().delete()
            # 设置SyncLog AUTO_INCREMENT
            cursor = connection.cursor()
            n = meta['last_upload_id'] + 1
            cursor.execute('ALTER TABLE SyncLog AUTO_INCREMENT=%d' % n)
            return create_success_dict(msg='数据恢复成功！')
        except:
            traceback.print_exc()
