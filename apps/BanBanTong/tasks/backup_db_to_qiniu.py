# coding=utf-8
import os
import bz2
import logging
import datetime
import platform
import subprocess
import BanBanTong.constants

from BanBanTong.db import models
from BanBanTong.utils import cloud_service
from django.conf import settings
DEBUG = settings.DEBUG
del settings

logger = logging.getLogger(__name__)


class Task(object):
    if DEBUG:
        run_period = 60 * 10
    else:
        run_period = 60 * 60 * 24

    def get_grouptb_id(self, server_type):
        obj = models.Group.objects.get(group_type=server_type)
        if server_type == 'province':
            g = models.GroupTB.objects.get(name=obj.name)
        elif server_type == 'city':
            g = models.GroupTB.objects.get(
                name=obj.name,
                parent__name=obj.parent.name
            )
        else:
            g = models.GroupTB.objects.get(
                name=obj.name, parent__name=obj.parent.name,
                parent__parent__name=obj.parent.parent.name
            )
        return g.group_id

    def handle(self, *args, **options):
        if DEBUG:
            print 'begin to backup'
        server_type = models.Setting.getvalue('server_type')
        if server_type in [None, 'school']:
            # print u'本程序只备份县级或更高级别的服务器'
            return
        if platform.system() == 'Windows':
            if BanBanTong.constants.MYSQL_PATH:
                mysqldump = os.path.join(BanBanTong.constants.MYSQL_PATH, 'mysqldump.exe')
            else:
                mysqldump = os.path.join(BanBanTong.constants.BANBANTONG_BASE_PATH,
                                         '..', '..', '..', 'mysql', 'bin', 'mysqldump.exe')
            mysqldump = '"' + mysqldump + '"'
        else:
            mysqldump = 'mysqldump'
        command = [
            mysqldump, '-u %s' % BanBanTong.constants.BANBANTONG_DB_USER,
            '-p%s' % BanBanTong.constants.BANBANTONG_DB_PASSWORD,
            '-P %s' % BanBanTong.constants.BANBANTONG_DB_PORT,
            '-h %s' % BanBanTong.constants.BANBANTONG_DB_HOST,
            BanBanTong.constants.BANBANTONG_DB_NAME
        ]
        command = ' '.join(command)
        # Tips:
        # 这里可以先命令行下输出到文件中,然后直接打包.
        # cmd2 = command + ' >_tmp.sql'
        # subprocess.check_call(cmd2, stderr=subprocess.STDOUT, shell=True)
        print command
        # ret = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        # content = bz2.compress(ret)
        # command = "dir"

        # Tips:
        # 在实际使用过程中,我们会遇到mysql抛出Waring等的异常,
        # 这些异常信息会一并的写入到.sql文件中了,所以选用Popen方法,利用PIPE
        # 分别去处理标准输入输出和错误信息
        p = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdoutput, erroutput = p.communicate()
        # print stdoutput, erroutput

        content = bz2.compress(stdoutput)

        # 保存到本地文件
        backup_file = os.path.join(BanBanTong.constants.BACKUP_TMP_ROOT,
                                   '%s.sql.bz2' % str(datetime.date.today()))
        with open(backup_file, 'wb') as f:
            f.write(content)

        # 上传到qiniu
        if not DEBUG:
            grouptb_id = self.get_grouptb_id(server_type)
            bucket_name = 'oebbt-backup'
            key = '%s.sql.bz2' % grouptb_id
            mime_type = 'application/x-bzip2'
            cloud_service.qiniu_upload_content(content, bucket_name, key, mime_type)

    def __init__(self):
        # print 'backup begin'
        # logger.debug('begin to backup database')
        try:
            self.handle()
        except:
            logger.exception('')
        # logger.debug('end to backup database')
        # print 'backup end'
