#!/usr/bin/env python
# coding=utf-8
import bz2
import datetime
import os
import platform
import subprocess
from django.conf import settings
from django.core.management.base import BaseCommand

import BanBanTong.constants
from BanBanTong.db import models
from BanBanTong.utils import cloud_service
DEBUG = settings.DEBUG
del settings


class Command(BaseCommand):
    '''
        通过mysqldump备份banbantong数据库到本地文件和qiniu
          本地备份到BACKUP_TMP_ROOT，每天一个文件，程序不清理，需要手动删除
          qiniu备份到oebbt-backup空间，只有一个文件，覆盖写入
    '''

    def get_grouptb_id(self, server_type):
        obj = models.Group.objects.get(group_type=server_type)
        if server_type == 'province':
            g = models.GroupTB.objects.get(name=obj.name)
        elif server_type == 'city':
            g = models.GroupTB.objects.get(name=obj.name, parent__name=obj.parent.name)
        else:
            g = models.GroupTB.objects.get(name=obj.name, parent__name=obj.parent.name,
                                           parent__parent__name=obj.parent.parent.name)
        return g.group_id

    def handle(self, *args, **options):
        print 'begin to backup'
        server_type = models.Setting.getvalue('server_type')
        if server_type in [None, 'school'] and not 'force' in args:
            print u'本程序只备份县级或更高级别的服务器'
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
            '--create-options',         # 生成的CREATE语句带上MySQL特有的option（其实也没什么特有）
            '--skip-add-drop-table',    # 生成的sql不带DROP TABLE语句，防止导入时误删除
            '--quick',                  # dump时每次SELECT一行，解决表太大内存溢出问题
            '--single-transaction',     # dump时保证数据一致性
            '--skip-extended-insert',   # 导出的INSERT语句每行一条记录，方便查看或编辑
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
            stderr=subprocess.PIPE,
            bufsize=1
        )
        #stdoutput, erroutput = p.communicate()
        compressor = bz2.BZ2Compressor()
        backup_file_path = os.path.join(BanBanTong.constants.BACKUP_TMP_ROOT,
                                        '%s.sql.bz2' % str(datetime.date.today()))
        print backup_file_path
        backup_file = open(backup_file_path, 'wb')

        # 每次从p.stdout读出一行进行压缩，避免一次读出所有dump结果消耗的内存过大
        i = 0
        with p.stdout:
            for line in iter(p.stdout.readline, b''):
                # 处理十万行大约需要4-20秒，产生10M-30M压缩文件。这个频率打log应该还行。
                if i % 100000 == 0:
                    print i, datetime.datetime.now()
                i += 1
                result = compressor.compress(line)
                if result:
                    backup_file.write(result)
        p.wait()
        print i, datetime.datetime.now()
        result = compressor.flush()
        if result:
            backup_file.write(result)
        backup_file.close()

        # 上传到qiniu（作为文件，qiniu sdk会自动分块上传，避免占用内存过大）
        if not DEBUG:
            grouptb_id = self.get_grouptb_id(server_type)
            bucket_name = 'oebbt-backup'
            key = '%s.sql.bz2' % grouptb_id
            mime_type = 'application/x-bzip2'
            cloud_service.qiniu_upload_filepath(backup_file_path, bucket_name, key, mime_type)
