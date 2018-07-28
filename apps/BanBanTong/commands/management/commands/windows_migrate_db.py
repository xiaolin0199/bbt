# coding=utf-8
import base64
import bz2
import json
import MySQLdb
import traceback
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.db import OperationalError
from django.db.utils import ProgrammingError
from BanBanTong.db import models


def migrate_from_687(cursor):
    cursor.execute("""ALTER TABLE `Asset` MODIFY COLUMN `reported_by`
                   varchar(20) NOT NULL""")
    cursor.execute("""ALTER TABLE `Asset` MODIFY COLUMN `remark`
                   varchar(180) NOT NULL""")
    cursor.execute("""ALTER TABLE `Asset` ADD KEY
                   `Asset_552efcda` (`reported_by`)""")
    cursor.execute("""ALTER TABLE `AssetLog` MODIFY COLUMN `remark`
                   varchar(180) NOT NULL""")
    cursor.execute("""ALTER TABLE `AssetRepairLog` MODIFY COLUMN `remark`
                   varchar(180) NOT NULL""")
    cursor.execute("""ALTER TABLE `AssetRepairLog` ADD KEY
                   `AssetRepairLog_552efcda` (`reported_by`)""")
    cursor.execute("""ALTER TABLE `LessonPeriod` ADD UNIQUE KEY
                   `term_uuid` (`term_uuid`,`sequence`)""")
    cursor.execute("""ALTER TABLE `Resource` MODIFY COLUMN `remark`
                   varchar(180) NOT NULL""")
    cursor.execute("""ALTER TABLE `Role` MODIFY COLUMN `remark`
                   varchar(180) NOT NULL""")
    cursor.execute("""ALTER TABLE `Teacher` MODIFY COLUMN `remark`
                   varchar(180) NOT NULL""")
    cursor.execute("""ALTER TABLE `User` MODIFY COLUMN `remark`
                   varchar(180) NOT NULL""")
    cursor.execute("""ALTER TABLE `usbkey_teachers` MODIFY COLUMN
                   `usbkey_uuid` varchar(180) NOT NULL""")
    sql = """CREATE TABLE IF NOT EXISTS `south_migrationhistory` (
                `id` int(11) NOT NULL AUTO_INCREMENT,
                `app_name` varchar(255) NOT NULL,
                `migration` varchar(255) NOT NULL,
                `applied` datetime NOT NULL,
                PRIMARY KEY (`id`)) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
    cursor.execute(sql)
    cursor.execute("""INSERT INTO `south_migrationhistory` VALUES
                   (1,'db','0001_initial','2014-03-18 13:38:11')""")


def append_synclog(m):
    q = m.objects.all()
    for i in q:
        models.SyncLog.add_log(i, 'add')


def _calculate_lessonteacher_login_time(objs):
    for one in objs:
        lessonteacher = one.teacherloginlog.lesson_teacher
        login_time = one.login_time
        if lessonteacher:
            #count += 1
            lessonteacher.login_time += login_time
            lessonteacher.save()


def _calculate_teacher_active(server_type, terms):
    for term in terms:
        t = models.LessonTeacher.objects.filter(class_uuid__grade__term=term)
        if server_type == 'city':
            q = models.Group.objects.filter(group_type='country')
            for i in q:
                v = t.filter(class_uuid__grade__term__school__parent__parent=i)
                v = v.values('teacher').distinct().count()
                models.TotalTeachersCountry(country_name=i.name, term=term,
                                            total=v).save()
        if server_type in ('city', 'country'):
            q = models.Group.objects.filter(group_type='town')
            for i in q:
                v = t.filter(class_uuid__grade__term__school__parent=i)
                v = v.values('teacher').distinct().count()
                models.TotalTeachersTown(country_name=i.parent.name,
                                         town_name=i.name, term=term,
                                         total=v).save()
            q = models.Group.objects.filter(group_type='school')
            for i in q:
                v = t.filter(class_uuid__grade__term__school=i)
                v = v.values('teacher').distinct().count()
                models.TotalTeachersSchool(country_name=i.parent.parent.name,
                                           town_name=i.parent.name,
                                           school_name=i.name, term=term,
                                           total=v).save()
        if server_type in ('city', 'country', 'school'):
            q = models.LessonName.objects.filter(deleted=False)
            for i in q:
                v = t.filter(teacher__school=i.school,
                             lesson_name__name=i.name)
                v = v.values('teacher').distinct().count()
                models.TotalTeachersLesson(country_name=i.school.parent.parent.name,
                                           town_name=i.school.parent.name,
                                           school_name=i.school.name,
                                           lesson_name=i.name, term=term,
                                           total=v).save()
            q = models.Grade.objects.all()
            for i in q:
                v = t.filter(class_uuid__grade=i)
                v = v.values('teacher').distinct().count()
                models.TotalTeachersGrade(country_name=i.term.school.parent.parent.name,
                                          town_name=i.term.school.parent.name,
                                          school_name=i.term.school.name,
                                          grade_name=i.name, term=term,
                                          total=v).save()
        if server_type == 'school':
            q = models.LessonTeacher.objects.all()
            for i in q:
                v = t.filter(class_uuid__grade=i.class_uuid.grade,
                             lesson_name=i.lesson_name)
                v = v.values('teacher').distinct().count()
                models.TotalTeachersLessonGrade(town_name=i.class_uuid.grade.term.school.parent.name,
                                                school_name=i.class_uuid.grade.term.school.name,
                                                lesson_name=i.lesson_name.name,
                                                grade_name=i.class_uuid.grade.name,
                                                term=term, total=v).save()
    q = models.TeacherLoginLog.objects.all()
    for i in q:
        func = models.ActiveTeachers.objects.get_or_create
        func(teacher=i.teacher, active_date=i.created_at.date(),
             country_name=i.country_name, town_name=i.town_name,
             school_name=i.school_name, school_year=i.term_school_year,
             term_type=i.term_type, lesson_name=i.lesson_name,
             grade_name=i.grade_name)


class Command(BaseCommand):
    help = "Migrate database on Windows platform."

    # Validation is called explicitly each time the server is reloaded.
    requires_model_validation = False

    def mig_2(self, cursor):
        try:
            cursor.execute("ALTER TABLE `Node` DROP KEY `name`")
            cursor.execute("""ALTER TABLE `Node` MODIFY COLUMN `remark`
                           varchar(180) NOT NULL""")
        except OperationalError:
            pass

    def mig_3(self, cursor):
        try:
            cursor.execute("""CREATE INDEX `TeacherLoginLog_96511a37`
                           ON `TeacherLoginLog` (`created_at`)""")
            cursor.execute("""CREATE INDEX `TeacherAbsentLog_96511a37`
                           ON `TeacherAbsentLog` (`created_at`)""")
        except OperationalError:
            pass

    def mig_4(self, cursor):
        try:
            cursor.execute("""ALTER TABLE `Node` ADD COLUMN `last_upload_time`
                           datetime NULL""")
        except OperationalError:
            pass

    def mig_5(self, cursor):
        cursor.execute("""ALTER TABLE `Node` ADD COLUMN `db_version`
                       int(11) NOT NULL""")

    def mig_6(self, cursor):
        cursor.execute("""ALTER TABLE `usbkey_teachers` ADD COLUMN
                       `sync_uploaded` tinyint(1) NOT NULL""")
        cursor.execute("""CREATE INDEX `usbkey_teachers_faa5c85e`
                       ON `usbkey_teachers` (`sync_uploaded`)""")

    def mig_7(self, cursor):
        cursor.execute("""ALTER TABLE `Node` ADD COLUMN `sync_status`
                       smallint(6) NOT NULL""")

    def mig_8(self, cursor):
        '''新增db_classmacv2 ClassMacV2表'''
        sql = """CREATE TABLE `db_classmacv2` (
                    `uuid` varchar(40) NOT NULL,
                    `class_uuid` varchar(40) NOT NULL,
                    `mac` varchar(64) NOT NULL,
                    PRIMARY KEY (`uuid`),
                    KEY `db_classmacv2_6a845960` (`class_uuid`),
                    CONSTRAINT `class_uuid_refs_uuid_06459dce`
                      FOREIGN KEY (`class_uuid`) REFERENCES `Class` (`uuid`)
                 ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)

    def mig_9(self, cursor):
        '''ClassMac数据迁移到ClassMacV2'''
        host = settings.DATABASES['default']['HOST']
        port = int(settings.DATABASES['default']['PORT'])
        user = settings.DATABASES['default']['USER']
        passwd = settings.DATABASES['default']['PASSWORD']
        db = settings.DATABASES['default']['NAME']
        conn = MySQLdb.connect(host=host, port=port, user=user, passwd=passwd,
                               db=db, charset='utf8')
        c = conn.cursor()
        sql = """SELECT class_uuid, mac FROM ClassMac"""
        c.execute(sql)
        res = c.fetchall()
        for row in res:
            c = models.Class.objects.get(uuid=row[0])
            models.ClassMacV2(class_uuid=c, mac=row[1]).save()
        conn.close()

    def mig_10(self, cursor):
        '''删除ClassMac'''
        cursor.execute("DROP TABLE ClassMac")

    def mig_11(self, cursor):
        '''新增ResourceFrom、ResourceType'''
        sql = """CREATE TABLE `db_resourcefrom` (
          `uuid` varchar(40) NOT NULL,
          `school_uuid` varchar(40) NOT NULL,
          `value` varchar(50) NOT NULL,
          `remark` varchar(180) NOT NULL,
          PRIMARY KEY (`uuid`),
          UNIQUE KEY `db_resourcefrom_school_uuid_3e899f9fa516d4b5_uniq`
            (`school_uuid`,`value`),
          KEY `db_resourcefrom_abbc0ae2` (`school_uuid`),
          KEY `db_resourcefrom_f6915675` (`value`),
          CONSTRAINT `school_uuid_refs_uuid_837a54c7`
            FOREIGN KEY (`school_uuid`) REFERENCES `Group` (`uuid`)
          ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)
        sql = """CREATE TABLE `db_resourcetype` (
          `uuid` varchar(40) NOT NULL,
          `school_uuid` varchar(40) NOT NULL,
          `value` varchar(20) NOT NULL,
          `remark` varchar(180) NOT NULL,
          PRIMARY KEY (`uuid`),
          UNIQUE KEY `db_resourcetype_school_uuid_18f4fce32343aecf_uniq`
            (`school_uuid`,`value`),
          KEY `db_resourcetype_abbc0ae2` (`school_uuid`),
          KEY `db_resourcetype_f6915675` (`value`),
          CONSTRAINT `school_uuid_refs_uuid_7bedc2e0`
            FOREIGN KEY (`school_uuid`) REFERENCES `Group` (`uuid`)
          ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)

    def mig_12(self, cursor):
        '''AssetLog新增asset_from'''
        sql = """ALTER TABLE `AssetLog` ADD COLUMN `asset_from`
          varchar(10) NOT NULL"""
        cursor.execute(sql)
        '''检查mig_11是否正确，防止一部分早期版本的mig_11带来问题'''
        sql = "SELECT * FROM db_resourcefrom"
        cursor.execute(sql)
        l = [i[0] for i in cursor.description]
        if 'school_id' in l:
            sql = """ALTER TABLE db_resourcefrom CHANGE school_id
              school_uuid varchar(40) NOT NULL"""
            cursor.execute(sql)
        if 'remark' not in l:
            sql = """ALTER TABLE db_resourcefrom ADD COLUMN
              `remark` varchar(180) NOT NULL"""
            cursor.execute(sql)
        sql = "SELECT * FROM db_resourcetype"
        cursor.execute(sql)
        l = [i[0] for i in cursor.description]
        if 'school_id' in l:
            sql = """ALTER TABLE db_resourcetype CHANGE school_id
              school_uuid varchar(40) NOT NULL"""
            cursor.execute(sql)
        if 'remark' not in l:
            sql = """ALTER TABLE db_resourcetype ADD COLUMN
              `remark` varchar(180) NOT NULL"""
            cursor.execute(sql)

    def mig_13(self, cursor):
        '''TeachLog增加一些index'''
        sql = """CREATE INDEX `TeacherLoginLog_6151272e`
          ON `TeacherLoginLog` (`class_name`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `TeacherLoginLog_d3244b14`
          ON `TeacherLoginLog` (`lesson_period_sequence`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `TeacherLoginLog_56ac288e`
          ON `TeacherLoginLog` (`school_name`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `TeacherLoginLog_a5b9273f`
          ON `TeacherLoginLog` (`town_name`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `TeacherLoginLog_8a60ca00`
          ON `TeacherLoginLog` (`grade_name`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `TeacherLoginLog_5909220d`
          ON `TeacherLoginLog` (`lesson_name`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `TeacherAbsentLog_6151272e`
          ON `TeacherAbsentLog` (`class_name`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `TeacherAbsentLog_d3244b14`
          ON `TeacherAbsentLog` (`lesson_period_sequence`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `TeacherAbsentLog_56ac288e`
          ON `TeacherAbsentLog` (`school_name`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `TeacherAbsentLog_a5b9273f`
          ON `TeacherAbsentLog` (`town_name`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `TeacherAbsentLog_8a60ca00`
          ON `TeacherAbsentLog` (`grade_name`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `TeacherAbsentLog_5909220d`
          ON `TeacherAbsentLog` (`lesson_name`)"""
        cursor.execute(sql)

    def mig_14(self, cursor):
        '''AssetLog和AssetRepairLog增加country_name'''
        sql = """ALTER TABLE `AssetRepairLog` ADD COLUMN
          `country_name` varchar(100) NOT NULL"""
        cursor.execute(sql)
        sql = """ALTER TABLE `AssetLog` ADD COLUMN
          `country_name` varchar(100) NOT NULL"""
        cursor.execute(sql)

    def mig_15(self, cursor):
        '''（校级）清除老的资产数据，生成新的资产分类'''
        if models.Setting.getvalue('server_type') != 'school':
            return
        models.AssetRepairLog.objects.all().delete()
        models.AssetLog.objects.all().delete()
        models.Asset.objects.all().delete()
        models.AssetType.objects.all().delete()
        try:
            school = models.Group.objects.get(group_type='school')
        except:
            return
        models.AssetType(name='台式计算机', icon='pc', unit_name='台',
                         school=school).save()
        models.AssetType(name='电子白板', icon='whiteboard', unit_name='块',
                         school=school).save()
        models.AssetType(name='投影仪', icon='projector', unit_name='台',
                         school=school).save()
        models.AssetType(name='大屏显示器', icon='lfd', unit_name='台',
                         school=school).save()
        models.AssetType(name='大屏一体机', icon='yitiji', unit_name='台',
                         school=school).save()
        models.AssetType(name='视频展台', icon='visual_presenter', unit_name='台',
                         school=school).save()
        models.AssetType(name='教室中控台', icon='center_console', unit_name='台',
                         school=school).save()
        models.AssetType(name='笔记本', icon='notebook', unit_name='台',
                         school=school).save()
        models.AssetType(name='打印机', icon='printer', unit_name='台',
                         school=school).save()
        models.AssetType(name='瘦终端', icon='thin_terminal', unit_name='台',
                         school=school).save()
        models.AssetType(name='网络交换机', icon='switchboard', unit_name='台',
                         school=school).save()
        models.AssetType(name='路由器', icon='router', unit_name='台',
                         school=school).save()
        models.AssetType(name='服务器', icon='server', unit_name='台',
                         school=school).save()
        models.AssetType(name='平板电脑', icon='pad', unit_name='台',
                         school=school).save()

    def mig_16(self, cursor):
        '''校级：生成新的资源来源和类型，老的资源也转换过来'''
        if models.Setting.getvalue('server_type') != 'school':
            return
        try:
            school = models.Group.objects.get(group_type='school')
        except:
            return
        default_resource_from = ['课内网资源', '国家基础教育资源',
                                 '优课网资源', '凯瑞教学资源',
                                 '电信网教育资源', '教材配套光盘',
                                 '现代远程教育资源', '自制课件',
                                 '其他资源']
        q = models.Resource.objects.values('resource_from').distinct()
        q = q.exclude(resource_from__in=default_resource_from)
        q = q.values_list('resource_from', flat=True)
        for value in q:
            models.ResourceFrom(school=school, value=value).save()
        for value in default_resource_from:
            models.ResourceFrom(school=school, value=value).save()
        default_resource_type = ['音频', '音视频', 'PPT幻灯片',
                                 '文档', '动画片', '互动课件',
                                 '其他']
        q = models.Resource.objects.values('resource_type').distinct()
        q = q.exclude(resource_type__in=default_resource_type)
        q = q.exclude(resource_type='PPT 幻灯片')
        q = q.values_list('resource_type', flat=True)
        for value in q:
            models.ResourceType(school=school, value=value).save()
        for value in default_resource_type:
            models.ResourceType(school=school, value=value).save()

    def mig_17(self, cursor):
        '''新增DesktopPicInfo桌面截屏表'''
        sql = """CREATE TABLE `db_desktoppicinfo` (
          `uuid` varchar(40) NOT NULL,
          `school_uuid` varchar(40) NOT NULL,
          `grade_uuid` varchar(20) NOT NULL,
          `grade_number` int(11) NOT NULL,
          `class_uuid` varchar(20) NOT NULL,
          `class_number` int(11) NOT NULL,
          `lesson_name` varchar(20) NOT NULL,
          `teacher_name` varchar(100) NOT NULL,
          `lesson_period_sequence` int(11) NOT NULL,
          `url` varchar(180) NOT NULL,
          `created_at` datetime NOT NULL,
          PRIMARY KEY (`uuid`),
          KEY `db_desktoppicinfo_abbc0ae2` (`school_uuid`),
          KEY `db_desktoppicinfo_d91b8533` (`grade_uuid`),
          KEY `db_desktoppicinfo_0fc515ee` (`grade_number`),
          KEY `db_desktoppicinfo_6a845960` (`class_uuid`),
          KEY `db_desktoppicinfo_492d5d4b` (`class_number`),
          KEY `db_desktoppicinfo_5909220d` (`lesson_name`),
          KEY `db_desktoppicinfo_1cfabe42` (`teacher_name`),
          KEY `db_desktoppicinfo_d3244b14` (`lesson_period_sequence`),
          KEY `db_desktoppicinfo_96511a37` (`created_at`),
          CONSTRAINT `school_uuid_refs_uuid_64dfb8e2`
          FOREIGN KEY (`school_uuid`) REFERENCES `Group` (`uuid`),
          CONSTRAINT `grade_uuid_refs_uuid_ed18f786`
          FOREIGN KEY (`grade_uuid`) REFERENCES `Grade` (`uuid`),
          CONSTRAINT `class_uuid_refs_uuid_1b9f8fd0`
          FOREIGN KEY (`class_uuid`) REFERENCES `Class` (`uuid`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)

    def mig_18(self, cursor):
        '''新增DesktopGlobalPreview'''
        sql = """CREATE TABLE `db_desktopglobalpreview` (
          `uuid` varchar(40) NOT NULL PRIMARY KEY,
          `pic_uuid` varchar(40) NOT NULL,
          KEY `db_desktopglobalpreview_e2c316d2` (`pic_uuid`),
          CONSTRAINT `pic_uuid_refs_uuid_d8a025cc`
          FOREIGN KEY (`pic_uuid`) REFERENCES `db_desktoppicinfo` (`uuid`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)

    def mig_19(self, cursor):
        '''DesktopPicInfo里有两个uuid太短，这里修正一下'''
        sql = """ALTER TABLE `db_desktoppicinfo` MODIFY COLUMN
          `grade_uuid` varchar(40) NOT NULL"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_desktoppicinfo` MODIFY COLUMN
          `class_uuid` varchar(40) NOT NULL"""
        cursor.execute(sql)

    def mig_20(self, cursor):
        '''DesktopPicInfo增加host'''
        sql = """ALTER TABLE `db_desktoppicinfo` ADD COLUMN
          `host` varchar(180) NOT NULL AFTER `lesson_period_sequence`"""
        cursor.execute(sql)
        sql = """UPDATE `db_desktoppicinfo`
          SET `host`='oe-test1.b0.upaiyun.com'"""
        cursor.execute(sql)

    def mig_21(self, cursor):
        '''新增TotalTeachers若干表'''
        sql = """CREATE TABLE `db_totalteacherscountry` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `country_name` varchar(100) NOT NULL,
          `total` int(11) NOT NULL,
          PRIMARY KEY (`id`),
          KEY `db_totalteacherscountry_b83604d0` (`country_name`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)
        sql = """CREATE TABLE `db_totalteacherstown` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `country_name` varchar(100) NOT NULL,
          `town_name` varchar(100) NOT NULL,
          `total` int(11) NOT NULL,
          PRIMARY KEY (`id`),
          KEY `db_totalteacherstown_b83604d0` (`country_name`),
          KEY `db_totalteacherstown_a5b9273f` (`town_name`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)
        sql = """CREATE TABLE `db_totalteachersschool` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `country_name` varchar(100) NOT NULL,
          `town_name` varchar(100) NOT NULL,
          `school_name` varchar(100) NOT NULL,
          `total` int(11) NOT NULL,
          PRIMARY KEY (`id`),
          KEY `db_totalteachersschool_b83604d0` (`country_name`),
          KEY `db_totalteachersschool_a5b9273f` (`town_name`),
          KEY `db_totalteachersschool_56ac288e` (`school_name`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)
        sql = """CREATE TABLE `db_totalteacherslesson` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `country_name` varchar(100) NOT NULL,
          `town_name` varchar(100) NOT NULL,
          `school_name` varchar(100) NOT NULL,
          `lesson_name` varchar(20) NOT NULL,
          `total` int(11) NOT NULL,
          PRIMARY KEY (`id`),
          KEY `db_totalteacherslesson_b83604d0` (`country_name`),
          KEY `db_totalteacherslesson_a5b9273f` (`town_name`),
          KEY `db_totalteacherslesson_56ac288e` (`school_name`),
          KEY `db_totalteacherslesson_5909220d` (`lesson_name`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)
        sql = """CREATE TABLE `db_totalteachersgrade` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `country_name` varchar(100) NOT NULL,
          `town_name` varchar(100) NOT NULL,
          `school_name` varchar(100) NOT NULL,
          `grade_name` varchar(20) NOT NULL,
          `total` int(11) NOT NULL,
          PRIMARY KEY (`id`),
          KEY `db_totalteachersgrade_b83604d0` (`country_name`),
          KEY `db_totalteachersgrade_a5b9273f` (`town_name`),
          KEY `db_totalteachersgrade_56ac288e` (`school_name`),
          KEY `db_totalteachersgrade_8a60ca00` (`grade_name`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)
        sql = """CREATE TABLE `db_totalteacherslessongrade` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `town_name` varchar(100) NOT NULL,
          `school_name` varchar(100) NOT NULL,
          `lesson_name` varchar(20) NOT NULL,
          `grade_name` varchar(20) NOT NULL,
          `total` int(11) NOT NULL,
          PRIMARY KEY (`id`),
          KEY `db_totalteacherslessongrade_lesson_name_203a83882c722266`
            (`lesson_name`,`grade_name`),
          KEY `db_totalteacherslessongrade_a5b9273f` (`town_name`),
          KEY `db_totalteacherslessongrade_56ac288e` (`school_name`),
          KEY `db_totalteacherslessongrade_5909220d` (`lesson_name`),
          KEY `db_totalteacherslessongrade_8a60ca00` (`grade_name`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)
        sql = """CREATE TABLE `db_activeteachers` (
          `id` int(11) AUTO_INCREMENT NOT NULL PRIMARY KEY,
          `teacher_uuid` varchar(40) NOT NULL,
          `active_date` date NOT NULL,
          `country_name` varchar(100) NOT NULL,
          `town_name` varchar(100) NOT NULL,
          `school_name` varchar(100) NOT NULL,
          `school_year` varchar(20) NOT NULL,
          `term_type` varchar(20) NOT NULL,
          `lesson_name` varchar(20) NOT NULL,
          `grade_name` varchar(20) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_activeteachers`
          ADD CONSTRAINT `teacher_uuid_refs_uuid_51eaf237`
          FOREIGN KEY (`teacher_uuid`) REFERENCES `Teacher` (`uuid`)"""
        cursor.execute(sql)
        indexes = ("""CREATE INDEX `db_activeteachers_c12e9d48`
                     ON `db_activeteachers` (`teacher_uuid`)""",
                   """CREATE INDEX `db_activeteachers_7e570bb2`
                     ON `db_activeteachers` (`active_date`)""",
                   """CREATE INDEX `db_activeteachers_b83604d0`
                     ON `db_activeteachers` (`country_name`)""",
                   """CREATE INDEX `db_activeteachers_a5b9273f`
                     ON `db_activeteachers` (`town_name`)""",
                   """CREATE INDEX `db_activeteachers_56ac288e`
                     ON `db_activeteachers` (`school_name`)""",
                   """CREATE INDEX `db_activeteachers_5909220d`
                     ON `db_activeteachers` (`lesson_name`)""",
                   """CREATE INDEX `db_activeteachers_8a60ca00`
                     ON `db_activeteachers` (`grade_name`)""")
        for sql in indexes:
            cursor.execute(sql)

    def mig_22(self, cursor):
        '''重整恩施县级服务器的SyncLog表'''
        country_name = models.Setting.getvalue('country')
        server_type = models.Setting.getvalue('server_type')
        if country_name != u'恩施市' or server_type != 'country':
            return
        sql = "TRUNCATE TABLE SyncLog"
        cursor.execute(sql)
        # Group
        provinces = models.Group.objects.filter(group_type='province')
        cities = models.Group.objects.filter(group_type='city')
        countries = models.Group.objects.filter(group_type='country')
        towns = models.Group.objects.filter(group_type='town')
        schools = models.Group.objects.filter(group_type='school')
        for i in provinces:
            models.SyncLog.add_log(i, 'add')
        for i in cities:
            models.SyncLog.add_log(i, 'add')
        for i in countries:
            models.SyncLog.add_log(i, 'add')
        for i in towns:
            models.SyncLog.add_log(i, 'add')
        for i in schools:
            models.SyncLog.add_log(i, 'add')
        # Term/Grade/Class/ClassMacv2
        append_synclog(models.Term)
        append_synclog(models.Grade)
        append_synclog(models.Class)
        append_synclog(models.ClassMacV2)
        # Teacher/LessonName/LessonPeriod/LessonSchedule/LessonTeacher
        append_synclog(models.Teacher)
        append_synclog(models.LessonName)
        append_synclog(models.LessonPeriod)
        append_synclog(models.LessonSchedule)
        append_synclog(models.LessonTeacher)
        # Asset/AssetType/AssetLog/AssetRepairLog
        append_synclog(models.AssetType)
        q = models.Asset.objects.filter(related_asset__isnull=True)
        for i in q:
            models.SyncLog.add_log(i, 'add')
        q = models.Asset.objects.filter(related_asset__isnull=False)
        for i in q:
            models.SyncLog.add_log(i, 'add')
        append_synclog(models.AssetLog)
        append_synclog(models.AssetRepairLog)
        # ResourceFrom/ResourceType
        append_synclog(models.ResourceFrom)
        append_synclog(models.ResourceType)
        # TeacherLoginLog/TeacherAbsentLog
        append_synclog(models.TeacherLoginLog)
        append_synclog(models.TeacherAbsentLog)
        # DesktopPicInfo/DesktopGlobalPreview
        append_synclog(models.DesktopPicInfo)
        append_synclog(models.DesktopGlobalPreview)

    def mig_23(self, cursor):
        '''使用时长的基础数据'''
        sql = """CREATE TABLE `db_teacherlogintime` (
          `uuid` varchar(40) NOT NULL PRIMARY KEY,
          `teacherloginlog_id` varchar(40) NOT NULL UNIQUE,
          `login_time` int(11) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_teacherlogintime`
          ADD CONSTRAINT `teacherloginlog_id_refs_uuid_72ba09bc`
          FOREIGN KEY (`teacherloginlog_id`)
          REFERENCES `TeacherLoginLog` (`uuid`)"""
        cursor.execute(sql)
        sql = """CREATE TABLE `db_teacherlogintimetemp` (
          `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
          `teacherloginlog_id` varchar(40) NOT NULL UNIQUE,
          `login_time` int(11) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_teacherlogintimetemp`
          ADD CONSTRAINT `teacherloginlog_id_refs_uuid_4a40c313`
          FOREIGN KEY (`teacherloginlog_id`)
          REFERENCES `TeacherLoginLog` (`uuid`)"""
        cursor.execute(sql)

    def mig_24(self, cursor):
        '''区县市服务器，班班通授课时长使用统计'''
        sql = """CREATE TABLE `db_teacherlogintimecache` (
          `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
          `town_uuid` varchar(40) NOT NULL,
          `school_uuid` varchar(40) NOT NULL,
          `grade_uuid` varchar(40) NOT NULL,
          `class_uuid` varchar(40) NOT NULL,
          `teacher_uuid` varchar(40) NOT NULL,
          `lesson_name` varchar(20) NOT NULL,
          `teacherlogintime_id` varchar(40) NOT NULL UNIQUE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_teacherlogintimecache`
          ADD CONSTRAINT `town_uuid_refs_uuid_e88b9ba3`
          FOREIGN KEY (`town_uuid`) REFERENCES `Group` (`uuid`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_teacherlogintimecache_850831a2`
          ON `db_teacherlogintimecache` (`town_uuid`)"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_teacherlogintimecache`
          ADD CONSTRAINT `school_uuid_refs_uuid_e88b9ba3`
          FOREIGN KEY (`school_uuid`) REFERENCES `Group` (`uuid`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_teacherlogintimecache_abbc0ae2`
          ON `db_teacherlogintimecache` (`school_uuid`)"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_teacherlogintimecache`
          ADD CONSTRAINT `grade_uuid_refs_uuid_20967b13`
          FOREIGN KEY (`grade_uuid`) REFERENCES `Grade` (`uuid`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_teacherlogintimecache_d91b8533`
          ON `db_teacherlogintimecache` (`grade_uuid`)"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_teacherlogintimecache`
          ADD CONSTRAINT `class_uuid_refs_uuid_1f1cd990`
          FOREIGN KEY (`class_uuid`) REFERENCES `Class` (`uuid`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_teacherlogintimecache_6a845960`
          ON `db_teacherlogintimecache` (`class_uuid`)"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_teacherlogintimecache`
          ADD CONSTRAINT `teacher_uuid_refs_uuid_94726dd2`
          FOREIGN KEY (`teacher_uuid`) REFERENCES `Teacher` (`uuid`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_teacherlogintimecache_c12e9d48`
          ON `db_teacherlogintimecache` (`teacher_uuid`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_teacherlogintimecache_5909220d`
          ON `db_teacherlogintimecache` (`lesson_name`)"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_teacherlogintimecache`
          ADD CONSTRAINT `teacherlogintime_id_refs_uuid_d6a2c2e2`
          FOREIGN KEY (`teacherlogintime_id`)
          REFERENCES `db_teacherlogintime` (`uuid`)"""
        cursor.execute(sql)

    def mig_25(self, cursor):
        '''班班通授课综合分析TeacherLoginCountWeekly
        TeacherLoginTimeWeekly'''
        sql = """CREATE TABLE `db_teacherlogincountweekly` (
          `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
          `town_name` varchar(100) NOT NULL,
          `school_name` varchar(100) NOT NULL,
          `term_uuid` varchar(40) NOT NULL,
          `grade_name` varchar(20) NOT NULL,
          `class_name` varchar(20) NOT NULL,
          `week` integer NOT NULL,
          `lesson_count` integer NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_teacherlogincountweekly_a5b9273f`
          ON `db_teacherlogincountweekly` (`town_name`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_teacherlogincountweekly_56ac288e`
          ON `db_teacherlogincountweekly` (`school_name`)"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_teacherlogincountweekly`
          ADD CONSTRAINT `term_uuid_refs_uuid_7cd80deb`
          FOREIGN KEY (`term_uuid`) REFERENCES `Term` (`uuid`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_teacherlogincountweekly_22e62ab6`
          ON `db_teacherlogincountweekly` (`term_uuid`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_teacherlogincountweekly_8a60ca00`
          ON `db_teacherlogincountweekly` (`grade_name`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_teacherlogincountweekly_6151272e`
          ON `db_teacherlogincountweekly` (`class_name`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_teacherlogincountweekly_9136095f`
          ON `db_teacherlogincountweekly` (`week`)"""
        cursor.execute(sql)
        sql = """CREATE TABLE `db_teacherlogintimeweekly` (
          `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
          `town_name` varchar(100) NOT NULL,
          `school_name` varchar(100) NOT NULL,
          `term_uuid` varchar(40) NOT NULL,
          `grade_name` varchar(20) NOT NULL,
          `class_name` varchar(20) NOT NULL,
          `week` integer NOT NULL,
          `total_time` integer NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_teacherlogintimeweekly_a5b9273f`
          ON `db_teacherlogintimeweekly` (`town_name`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_teacherlogintimeweekly_56ac288e`
          ON `db_teacherlogintimeweekly` (`school_name`)"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_teacherlogintimeweekly`
          ADD CONSTRAINT `term_uuid_refs_uuid_62d26c7f`
          FOREIGN KEY (`term_uuid`) REFERENCES `Term` (`uuid`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_teacherlogintimeweekly_22e62ab6`
          ON `db_teacherlogintimeweekly` (`term_uuid`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_teacherlogintimeweekly_8a60ca00`
          ON `db_teacherlogintimeweekly` (`grade_name`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_teacherlogintimeweekly_6151272e`
          ON `db_teacherlogintimeweekly` (`class_name`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_teacherlogintimeweekly_9136095f`
          ON `db_teacherlogintimeweekly` (`week`)"""
        cursor.execute(sql)

    def mig_26(self, cursor):
        '''TotalTeachers表增加term'''
        sql = """ALTER TABLE `db_totalteacherslesson`
          ADD COLUMN `term_uuid` varchar(40) NULL"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_totalteachersgrade`
          ADD COLUMN `term_uuid` varchar(40) NULL"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_totalteacherstown`
          ADD COLUMN `term_uuid` varchar(40) NULL"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_totalteacherscountry`
          ADD COLUMN `term_uuid` varchar(40) NULL"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_totalteachersschool`
          ADD COLUMN `term_uuid` varchar(40) NULL"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_totalteacherslessongrade`
          ADD COLUMN `term_uuid` varchar(40) NULL"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_totalteacherslesson`
          ADD CONSTRAINT `term_uuid_refs_uuid_2c8f2d99`
          FOREIGN KEY (`term_uuid`) REFERENCES `Term` (`uuid`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_totalteacherslesson_22e62ab6`
          ON `db_totalteacherslesson` (`term_uuid`)"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_totalteachersgrade`
          ADD CONSTRAINT `term_uuid_refs_uuid_f208583d`
          FOREIGN KEY (`term_uuid`) REFERENCES `Term` (`uuid`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_totalteachersgrade_22e62ab6`
          ON `db_totalteachersgrade` (`term_uuid`)"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_totalteacherstown`
          ADD CONSTRAINT `term_uuid_refs_uuid_bd166029`
          FOREIGN KEY (`term_uuid`) REFERENCES `Term` (`uuid`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_totalteacherstown_22e62ab6`
          ON `db_totalteacherstown` (`term_uuid`)"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_totalteacherscountry`
          ADD CONSTRAINT `term_uuid_refs_uuid_a2b3c248`
          FOREIGN KEY (`term_uuid`) REFERENCES `Term` (`uuid`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_totalteacherscountry_22e62ab6`
          ON `db_totalteacherscountry` (`term_uuid`)"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_totalteachersschool`
          ADD CONSTRAINT `term_uuid_refs_uuid_1ff7742d`
          FOREIGN KEY (`term_uuid`) REFERENCES `Term` (`uuid`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_totalteachersschool_22e62ab6`
          ON `db_totalteachersschool` (`term_uuid`)"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_totalteacherslessongrade`
          ADD CONSTRAINT `term_uuid_refs_uuid_4fcb854c`
          FOREIGN KEY (`term_uuid`) REFERENCES `Term` (`uuid`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_totalteacherslessongrade_22e62ab6`
          ON `db_totalteacherslessongrade` (`term_uuid`)"""
        cursor.execute(sql)

    def mig_27(self, cursor):
        '''初始化计算一次TotalTeachers/ActiveTeachers表'''
        '''
            注意：由于Term模型有了变化，这里执行mig_27时会报错
            unknown column schedule_time in field_list。
            解决此错误的临时办法是把mig_27移到最后（mig_45），
            但是今后要注意：migrate程序是不应该调用models.*的。
        '''
        return

    def mig_28(self, cursor):
        '''新增SyncLogTemp，Node表增加last_save_id'''
        sql = """CREATE TABLE `db_synclogtemp` (
          `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
          `node_id` integer NOT NULL,
          `data` longtext NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET utf8"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_synclogtemp`
          ADD CONSTRAINT `node_id_refs_id_25d77bef`
          FOREIGN KEY (`node_id`) REFERENCES `Node` (`id`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `db_synclogtemp_e453c5c5`
          ON `db_synclogtemp` (`node_id`)"""
        cursor.execute(sql)
        sql = """ALTER TABLE `Node` ADD COLUMN `last_save_id`
          bigint NULL DEFAULT 0"""
        cursor.execute(sql)

    def mig_29(self, cursor):
        sql = """ALTER TABLE `Grade`
          ADD COLUMN `number` integer NOT NULL DEFAULT 0"""
        cursor.execute(sql)
        sql = """ALTER TABLE `Class`
          ADD COLUMN `number` integer NOT NULL DEFAULT 0"""
        cursor.execute(sql)
        sql = """ALTER TABLE `Class`
          ADD COLUMN `teacher_uuid` varchar(40) NULL"""
        cursor.execute(sql)
        sql = """CREATE INDEX `Grade_d4e7917a` ON `Grade` (`number`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `Class_d4e7917a` ON `Class` (`number`)"""
        cursor.execute(sql)
        sql = """ALTER TABLE `Class`
          ADD CONSTRAINT `teacher_uuid_refs_uuid_c3324bfd`
          FOREIGN KEY (`teacher_uuid`) REFERENCES `Teacher` (`uuid`)"""
        cursor.execute(sql)
        sql = """CREATE INDEX `Class_c12e9d48` ON `Class` (`teacher_uuid`)"""
        cursor.execute(sql)

        # resourceFrom & resourceType 删除字段  school
        try:
            sql = """ALTER TABLE db_resourcefrom DROP FOREIGN KEY school_uuid_refs_uuid_837a54c7"""
            cursor.execute(sql)
        except:
            s = traceback.format_exc()
            self.stdout.write(s)

        try:
            sql = """ALTER TABLE db_resourcetype DROP FOREIGN KEY school_uuid_refs_uuid_7bedc2e0"""
            cursor.execute(sql)
        except:
            s = traceback.format_exc()
            self.stdout.write(s)

        try:
            sql = """ALTER TABLE db_resourcefrom DROP FOREIGN KEY school_id_refs_uuid_837a54c7"""
            cursor.execute(sql)
        except:
            s = traceback.format_exc()
            self.stdout.write(s)

        try:
            sql = """ALTER TABLE db_resourcetype DROP FOREIGN KEY school_id_refs_uuid_7bedc2e0"""
            cursor.execute(sql)
        except:
            s = traceback.format_exc()
            self.stdout.write(s)

        try:
            sql = """ALTER TABLE db_resourcefrom DROP INDEX db_resourcefrom_school_uuid_3e899f9fa516d4b5_uniq"""
            cursor.execute(sql)
        except:
            s = traceback.format_exc()
            self.stdout.write(s)

        try:
            sql = """ALTER TABLE db_resourcetype DROP INDEX db_resourcetype_school_uuid_18f4fce32343aecf_uniq"""
            cursor.execute(sql)
        except:
            s = traceback.format_exc()
            self.stdout.write(s)

        sql = """ALTER TABLE db_resourcefrom DROP COLUMN school_uuid"""
        cursor.execute(sql)
        sql = """ALTER TABLE db_resourcetype DROP COLUMN school_uuid"""
        cursor.execute(sql)

    def mig_30(self, cursor):
        '''ClassTime学期参考计划课时'''
        sql = """CREATE TABLE `db_classtime` (
          `uuid` varchar(40) NOT NULL PRIMARY KEY,
          `class_uuid_id` varchar(40) NOT NULL UNIQUE,
          `schedule_time` integer NOT NULL,
          `assigned_time` integer NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET utf8"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_classtime`
          ADD CONSTRAINT `class_uuid_id_refs_uuid_934d99cb`
          FOREIGN KEY (`class_uuid_id`) REFERENCES `Class` (`uuid`)"""
        cursor.execute(sql)

    def mig_31(self, cursor):
        '''添加newterm,newlessonname,newlessontype'''
        sql = """CREATE TABLE IF NOT EXISTS `newterm` (
            `uuid` varchar(40) NOT NULL,
            `school_year` varchar(20) NOT NULL,
            `term_type` varchar(20) NOT NULL,
            `start_date` date NOT NULL,
            `end_date` date NOT NULL,
            `deleted` tinyint(1) NOT NULL,
            PRIMARY KEY (`uuid`),
            KEY `NewTerm_0a0dd6b6` (`school_year`),
            KEY `NewTerm_af17dbbf` (`term_type`),
            KEY `NewTerm_e1031852` (`start_date`),
            KEY `NewTerm_5b9e4797` (`end_date`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""
        cursor.execute(sql)

        sql = """CREATE TABLE IF NOT EXISTS `newlessontype` (
            `uuid` varchar(40) NOT NULL,
            `name` varchar(20) NOT NULL,
            `remark` varchar(255),
            PRIMARY KEY (`uuid`),
            KEY `NewLessonType_4da47e07` (`name`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""
        cursor.execute(sql)

        sql = """
            CREATE TABLE IF NOT EXISTS `newlessonname` (
            `uuid` varchar(40) NOT NULL,
            `name` varchar(20) NOT NULL,
            `deleted` tinyint(1) NOT NULL,
            PRIMARY KEY (`uuid`),
            KEY `NewLessonName_4da47e07` (`name`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""
        cursor.execute(sql)

    def mig_32(self, cursor):
        '''为lessonname添加一个字段types'''
        sql = """ALTER TABLE lessonname ADD COLUMN types varchar(50) NULL"""
        cursor.execute(sql)

    def mig_33(self, cursor):
        '''newlessonname与newlessontype的多对多关联表'''
        sql = """CREATE TABLE IF NOT EXISTS `newlessonnametype` (
            `uuid` varchar(40) NOT NULL,
            `newlessonname_uuid` varchar(40) NOT NULL,
            `newlessontype_uuid` varchar(40) NOT NULL,
            PRIMARY KEY (`uuid`),
            KEY `NewLessonNameType_b5f5df6c` (`newlessonname_uuid`),
            KEY `NewLessonNameType_01946df9` (`newlessontype_uuid`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""
        cursor.execute(sql)

        sql = """ALTER TABLE `newlessonnametype`
            ADD CONSTRAINT `newlessontype_uuid_refs_uuid_e57c5fb1` FOREIGN KEY (`newlessontype_uuid`) REFERENCES `newlessontype` (`uuid`),
            ADD CONSTRAINT `newlessonname_uuid_refs_uuid_b0cc2900` FOREIGN KEY (`newlessonname_uuid`) REFERENCES `newlessonname` (`uuid`);
            """
        cursor.execute(sql)

    def mig_34(self, cursor):
        '''NewTerm和Term新增schedule_time计划达标课时'''
        sql = """ALTER TABLE `NewTerm`
          ADD COLUMN `schedule_time` integer NOT NULL DEFAULT 0"""
        cursor.execute(sql)
        sql = """ALTER TABLE `Term`
          ADD COLUMN `schedule_time` integer NOT NULL DEFAULT 0"""
        cursor.execute(sql)

    def mig_35(self, cursor):
        '''NewTerm和NewLessonName添加country_uuid'''
        sql = """ALTER TABLE `NewTerm`
          ADD COLUMN `country_uuid` varchar(40) NOT NULL"""
        cursor.execute(sql)
        sql = """ALTER TABLE `NewLessonName`
          ADD COLUMN `country_uuid` varchar(40) NOT NULL"""
        cursor.execute(sql)

        sql = """ALTER TABLE `newterm` ADD CONSTRAINT `country_uuid_refs_uuid_4b2a3431` FOREIGN KEY (`country_uuid`) REFERENCES `group` (`uuid`);"""
        cursor.execute(sql)

        sql = """ALTER TABLE `newlessonname` ADD CONSTRAINT `country_uuid_refs_uuid_5bce7af6` FOREIGN KEY (`country_uuid`) REFERENCES `group` (`uuid`);"""
        cursor.execute(sql)

    def mig_36(self, cursor):
        '''NewLessonType添加country_uuid'''
        sql = """ALTER TABLE `NewLessonType`
          ADD COLUMN `country_uuid` varchar(40) NULL"""
        cursor.execute(sql)

        sql = """ALTER TABLE `newlessontype` ADD CONSTRAINT `country_uuid_refs_uuid_9ce8520c` FOREIGN KEY (`country_uuid`) REFERENCES `group` (`uuid`);"""
        cursor.execute(sql)

    def mig_37(self, cursor):
        '''ResourceFrom和ResourceType添加country_uuid'''
        sql = """ALTER TABLE `db_resourcefrom`
          ADD COLUMN `country_uuid` varchar(40) NULL"""
        cursor.execute(sql)
        sql = """ALTER TABLE `db_resourcetype`
          ADD COLUMN `country_uuid` varchar(40) NULL"""
        cursor.execute(sql)

        sql = """ALTER TABLE `db_resourcefrom` ADD CONSTRAINT `country_uuid_refs_uuid_837a54c7` FOREIGN KEY (`country_uuid`) REFERENCES `group` (`uuid`);"""
        cursor.execute(sql)

        sql = """ALTER TABLE `db_resourcetype` ADD CONSTRAINT `country_uuid_refs_uuid_7bedc2e0` FOREIGN KEY (`country_uuid`) REFERENCES `group` (`uuid`);"""
        cursor.execute(sql)

    def mig_38(self, cursor):
        '''courseware及teacherloginlogcourseware表添加'''
        sql = """CREATE TABLE IF NOT EXISTS `courseware` (
                    `uuid` varchar(40) NOT NULL,
                    `md5` varchar(255) NOT NULL,
                    `create_time` datetime NOT NULL,
                    `title` varchar(50) DEFAULT NULL,
                    `size` varchar(20) DEFAULT NULL,
                    `use_times` int(11) NOT NULL,
                    `download_times` int(11) NOT NULL,
                    `file_name` varchar(100) DEFAULT NULL,
                    `qiniu_url` varchar(255) DEFAULT NULL,
                    PRIMARY KEY (`uuid`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""
        cursor.execute(sql)

        sql = """CREATE TABLE IF NOT EXISTS `teacherloginlogcourseware` (
                    `uuid` varchar(40) NOT NULL,
                    `courseware_uuid` varchar(40) NOT NULL,
                    `teacherloginlog_uuid` varchar(40) NOT NULL,
                    PRIMARY KEY (`uuid`),
                    KEY `TeacherLoginLogCourseWare_a0135362` (`courseware_uuid`),
                    KEY `TeacherLoginLogCourseWare_65a31c80` (`teacherloginlog_uuid`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""
        cursor.execute(sql)

        sql = """ALTER TABLE `teacherloginlogcourseware`
            ADD CONSTRAINT `teacherloginlog_uuid_refs_uuid_cca4eec0` FOREIGN KEY (`teacherloginlog_uuid`) REFERENCES `teacherloginlog` (`uuid`),
            ADD CONSTRAINT `courseware_uuid_refs_uuid_84b10029` FOREIGN KEY (`courseware_uuid`) REFERENCES `courseware` (`uuid`);
            """
        cursor.execute(sql)

    def mig_39(self, cursor):
        '''教学大纲相关model'''
        sql = """CREATE TABLE `db_syllabusgrade` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `school_year` varchar(20) NOT NULL,
          `term_type` varchar(20) NOT NULL,
          `grade_name` varchar(20) NOT NULL,
          `in_use` tinyint(1) NOT NULL,
          PRIMARY KEY (`id`),
          KEY `db_syllabusgrade_8a60ca00` (`grade_name`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)
        sql = """CREATE TABLE `db_syllabusgradelesson` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `syllabus_grade_id` int(11) NOT NULL,
          `lesson_name` varchar(20) NOT NULL,
          `edition` varchar(20) NOT NULL,
          `picture_host` varchar(180) NOT NULL,
          `picture_url` varchar(180) NOT NULL,
          `remark` varchar(180) NOT NULL,
          PRIMARY KEY (`id`),
          KEY `db_syllabusgradelesson_c9d63954` (`syllabus_grade_id`),
          KEY `db_syllabusgradelesson_5909220d` (`lesson_name`),
          CONSTRAINT `syllabus_grade_id_refs_id_f309ce02`
            FOREIGN KEY (`syllabus_grade_id`) REFERENCES `db_syllabusgrade` (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)
        sql = """CREATE TABLE `db_syllabusgradelessoncontent` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `syllabus_grade_lesson_id` int(11) NOT NULL,
          `parent_id` int(11) DEFAULT NULL,
          `seq` int(11) NOT NULL,
          `subseq` int(11) NOT NULL,
          `title` varchar(100) NOT NULL,
          PRIMARY KEY (`id`),
          KEY `db_syllabusgradelessoncontent_d0ff2226` (`syllabus_grade_lesson_id`),
          KEY `db_syllabusgradelessoncontent_410d0aac` (`parent_id`),
          CONSTRAINT `syllabus_grade_lesson_id_refs_id_40affbb5`
            FOREIGN KEY (`syllabus_grade_lesson_id`)
            REFERENCES `db_syllabusgradelesson` (`id`),
          CONSTRAINT `parent_id_refs_id_e6820bf6`
            FOREIGN KEY (`parent_id`)
            REFERENCES `db_syllabusgradelessoncontent` (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)

    def mig_40(self, cursor):
        sql = """CREATE TABLE IF NOT EXISTS `teacherloginloglessoncontent` (
                `uuid` varchar(40) NOT NULL,
                `teacherloginlog_uuid` varchar(40) NOT NULL,
                `title` varchar(100) DEFAULT NULL,
                `lessoncontent_id` int(11) DEFAULT NULL,
                PRIMARY KEY (`uuid`),
                UNIQUE KEY `teacherloginlog_uuid` (`teacherloginlog_uuid`),
                KEY `TeacherLoginLogLessonContent_c914553e` (`lessoncontent_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""
        cursor.execute(sql)

        sql = """ALTER TABLE `teacherloginloglessoncontent`
            ADD CONSTRAINT `lessoncontent_id_refs_id_7b467419` FOREIGN KEY (`lessoncontent_id`) REFERENCES `db_syllabusgradelessoncontent` (`id`),
            ADD CONSTRAINT `teacherloginlog_uuid_refs_uuid_a8b4800b` FOREIGN KEY (`teacherloginlog_uuid`) REFERENCES `teacherloginlog` (`uuid`);
            """
        cursor.execute(sql)

    def mig_41(self, cursor):
        '''县级向校级同步的model'''
        sql = """CREATE TABLE `db_countrytoschoolsynclog` (
          `created_at` bigint(20) NOT NULL AUTO_INCREMENT,
          `operation_type` varchar(10) NOT NULL,
          `operation_content` longtext NOT NULL,
          `used` tinyint(1) NOT NULL,
          PRIMARY KEY (`created_at`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)

    def mig_43(self, cursor):
        '''为LessonTeacher添加login_time'''
        sql = """ALTER TABLE `LessonTeacher`
          ADD COLUMN `login_time` integer NOT NULL DEFAULT 0"""
        cursor.execute(sql)

    def mig_44(self, cursor):
        '''初始统计LessonTeacher的login_time值'''
        if models.Setting.getvalue('installed') != 'True':
            return

        objs = models.TeacherLoginTime.objects.all()
        _calculate_lessonteacher_login_time(objs)

    def mig_45(self, cursor):
        '''暂时放在这儿'''
        '''初始化计算一次TotalTeachers/ActiveTeachers表'''
        if models.Setting.getvalue('installed') != 'True':
            return
        server_type = models.Setting.getvalue('server_type')
        terms = models.Term.objects.all().order_by('start_date')
        for table in ('db_totalteacherscountry', 'db_totalteacherstown',
                      'db_totalteachersschool', 'db_totalteacherslesson',
                      'db_totalteachersgrade', 'db_totalteacherslessongrade',
                      'db_activeteachers'):
            sql = """TRUNCATE TABLE %s""" % table
            cursor.execute(sql)
        _calculate_teacher_active(server_type, terms)

    def mig_46(self, cursor):
        '''对应south的0045'''
        '''746版本升级到这里'''
        '''
            *需要为db_resourcefrom和db_resourcetype初始化数据
             1.找到所有不重复的资源类型和资源来源;
             2.重写入1步中的所有数据，并添加上country_uuid数据
             3.删除所有country_uuid为NULL的数据
            *初始化NewLessonType(小学，初中，高中)
        '''
        if models.Setting.getvalue('installed') != 'True':
            return
        if models.Setting.getvalue('server_type') != 'country':
            return
        try:
            country = models.Group.objects.get(group_type='country')
        except:
            s = traceback.format_exc()
            self.stdout.write(s)
            return

        # 1
        distinct_froms = models.ResourceFrom.objects.all().values_list('value', flat=True).distinct()
        distinct_types = models.ResourceType.objects.all().values_list('value', flat=True).distinct()

        # 2
        for one in distinct_froms:
            models.ResourceFrom.objects.get_or_create(value=one, country=country)
        for one in distinct_types:
            models.ResourceType.objects.get_or_create(value=one, country=country)

        # 3
        models.ResourceFrom.objects.filter(country__isnull=True).delete()
        models.ResourceType.objects.filter(country__isnull=True).delete()

        # NewLessonType
        models.NewLessonType.objects.get_or_create(country=country, name='小学')
        models.NewLessonType.objects.get_or_create(country=country, name='初中')
        models.NewLessonType.objects.get_or_create(country=country, name='高中')

        models.NewLessonType.objects.filter(country__isnull=True).delete()

    def mig_47(self, cursor):
        '''mig_47留给OEBBTModifyTerm'''
        pass

    def mig_48(self, cursor):
        '''746的升级程序通过OEBBTModifyTerm升级到这里'''
        '''mig_48留给OEBBTModifyTerm'''
        pass

    def mig_49(self, cursor):
        '''对应south的0046'''
        sql = """ALTER TABLE `db_syllabusgradelesson` ADD COLUMN publish varchar(20) NOT NULL"""
        cursor.execute(sql)

        sql = """ALTER TABLE `db_syllabusgradelesson` ADD COLUMN bookversion varchar(20) NOT NULL"""
        cursor.execute(sql)

    def mig_50(self, cursor):
        ''''''
        sql = """ALTER TABLE `db_syllabusgradelessoncontent` CHANGE `seq` `seq` DOUBLE NULL DEFAULT NULL"""
        cursor.execute(sql)

        sql = """ALTER TABLE `db_syllabusgradelessoncontent` CHANGE `subseq` `subseq` DOUBLE NULL DEFAULT NULL"""
        cursor.execute(sql)

        # 清空几张表
        sql = """DELETE FROM `teacherloginloglessoncontent`"""
        cursor.execute(sql)

        sql = """DELETE FROM `db_syllabusgradelessoncontent`"""
        cursor.execute(sql)

        sql = """DELETE FROM `db_syllabusgradelesson`"""
        cursor.execute(sql)

        sql = """DELETE FROM `db_syllabusgrade`"""
        cursor.execute(sql)

    def mig_51(self, cursor):
        '''县级同步资源平台'''
        sql = """CREATE TABLE IF NOT EXISTS `db_countrytoresourceplatformsynclog` (
            `created_at` bigint(20) NOT NULL AUTO_INCREMENT,
            `operation_type` varchar(10) NOT NULL,
            `operation_content` longtext NOT NULL,
            `used` tinyint(1) NOT NULL,
            PRIMARY KEY (`created_at`)
        ) ENGINE=InnoDB  DEFAULT CHARSET=utf8"""
        cursor.execute(sql)

    def mig_52(self, cursor):
        '''syllabusgradelesson添加一个字段'''
        sql = """ALTER TABLE `db_syllabusgradelesson`
          ADD COLUMN `in_use` tinyint(1) NOT NULL DEFAULT 0"""
        cursor.execute(sql)

    def mig_53(self, cursor):
        '''db_syllabusgradelesson添加一个字段'''
        sql = """ALTER TABLE `db_syllabusgradelesson`
          ADD COLUMN `volume` VARCHAR(10) NULL DEFAULT NULL"""
        cursor.execute(sql)

    def mig_54(self, cursor):
        '''SyncLogTemp里的内容解包出来，以后不再使用这个表了'''
        def _save_record(line, node):
            try:
                log = json.loads(line)
                created_at = log['created_at']
                if created_at <= node.last_save_id:
                    return
                operation_type = log['operation_type']
                operation_content = log['operation_content']
                models.SyncLogPack.unpack_log(operation_type,
                                              operation_content)
                node.last_save_id = created_at
                node.save()
            except Exception as e:
                raise e

        try:
            q = models.SyncLogTemp.objects.all()
            self.stdout.write('mig_54: total %d objects' % q.count())
            x = 0
            for i in q:
                y = 0
                for line in bz2.decompress(base64.b64decode(i.data)):
                    if line:
                        try:
                            _save_record(line, i.node)
                        except:
                            pass
                    y += 1
                    self.stdout.write('mig_54: %d, %d' % (x, y))
            q.delete()
        except:
            s = traceback.format_exc()
            self.stdout.write(s)

    def mig_55(self, cursor):
        '''classmacv2添加一个ip字段'''
        sql = """ALTER TABLE `db_classmacv2`
          ADD COLUMN `ip` VARCHAR(64) NULL DEFAULT NULL"""
        cursor.execute(sql)

    def mig_56(self, cursor):
        '''添加校园公告表'''
        sql = """CREATE TABLE IF NOT EXISTS `db_schoolpost` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `title` varchar(100) NOT NULL,
            `content` longtext,
            `active` tinyint(1) NOT NULL,
            `create_date` datetime NOT NULL,
            `expire_date` datetime DEFAULT NULL,
            PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;"""
        cursor.execute(sql)

    def mig_57(self, cursor):
        '''TeacherLoginTimeTemp增加last_login_datetime字段'''
        sql = """ALTER TABLE db_teacherlogintimetemp
          ADD COLUMN `last_login_datetime` datetime DEFAULT NULL"""
        cursor.execute(sql)

    def mig_58(self, cursor):
        '''
            清空校级服务器的SyncLog，重新生成。
            清空县级服务器的Node中的last_save_id，以便校级重新上传所有记录。
            等到校级都清理完了，以后再处理县级的SyncLog
        '''
        server_type = models.Setting.getvalue('server_type')
        if server_type == 'school':
            models.SyncLog.objects.all().delete()
            # 生成SyncLog - Group
            obj = models.Group.objects.get(group_type='province')
            models.SyncLog.add_log(obj, 'add')
            obj = models.Group.objects.get(group_type='city')
            models.SyncLog.add_log(obj, 'add')
            obj = models.Group.objects.get(group_type='country')
            models.SyncLog.add_log(obj, 'add')
            obj = models.Group.objects.get(group_type='town')
            models.SyncLog.add_log(obj, 'add')
            obj = models.Group.objects.get(group_type='school')
            models.SyncLog.add_log(obj, 'add')
            # 生成SyncLog - 其他data
            l = [models.Teacher, models.AssetType, models.Asset,
                 models.AssetLog, models.AssetRepairLog, models.Term,
                 models.Grade, models.Class, models.ClassMacV2, models.ClassTime,
                 models.LessonName, models.LessonPeriod,
                 models.LessonSchedule, models.LessonTeacher,
                 models.TeacherLoginLog, models.TeacherLoginTime,
                 models.TeacherAbsentLog, models.DesktopPicInfo,
                 models.DesktopGlobalPreview,
                 models.CourseWare,
                 models.TeacherLoginLogCourseWare,
                 models.TeacherLoginLogLessonContent]
            for m in l:
                if m.__class__.__name__ == 'Asset':
                    q = models.Asset.objects.filter(related_asset__isnull=True)
                    for obj in q:
                        models.SyncLog.add_log(obj, 'add')
                    q = models.Asset.objects.filter(related_asset__isnull=False)
                    for obj in q:
                        models.SyncLog.add_log(obj, 'add')
                else:
                    q = m.objects.all()
                    for obj in q:
                        models.SyncLog.add_log(obj, 'add')
        elif server_type == 'country':
            # models.SyncLog.objects.all().delete()
            models.Node.objects.all().update(last_upload_id=0)

    def mig_59(self, cursor):
        '''
            电脑教室ComputerClass，以及相关的ManyToMany表
        '''
        sql = """CREATE TABLE `db_computerclass` (
          `uuid` varchar(40) NOT NULL,
          `client_number` int(11) NOT NULL,
          `class_bind_to_id` varchar(40) NOT NULL,
          PRIMARY KEY (`uuid`),
          UNIQUE KEY `class_bind_to_id` (`class_bind_to_id`),
          CONSTRAINT `class_bind_to_id_refs_uuid_d6a8ae97`
            FOREIGN KEY (`class_bind_to_id`) REFERENCES `Class` (`uuid`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)
        sql = """CREATE TABLE `db_computerclass_lesson_range` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `computerclass_id` varchar(40) NOT NULL,
          `lessonname_id` varchar(40) NOT NULL,
          PRIMARY KEY (`id`),
          UNIQUE KEY
            `db_computerclass_lesson__computerclass_id_348a3029cb144b73_uniq`
            (`computerclass_id`,`lessonname_id`),
          KEY `db_computerclass_lesson_range_c4ee3393` (`computerclass_id`),
          KEY `db_computerclass_lesson_range_dcb982c1` (`lessonname_id`),
          CONSTRAINT `computerclass_id_refs_uuid_cee708f5`
            FOREIGN KEY (`computerclass_id`)
            REFERENCES `db_computerclass` (`uuid`),
          CONSTRAINT `lessonname_id_refs_uuid_6c88816d`
            FOREIGN KEY (`lessonname_id`) REFERENCES `LessonName` (`uuid`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""
        cursor.execute(sql)

    def mig_60(self, cursor):
        '''
            V4.0的最后一次升级，把south的升级记录写入数据库，
            以后V4.1用south继续升级
        '''
        sql = """TRUNCATE TABLE south_migrationhistory"""
        cursor.execute(sql)
        sql = """INSERT INTO `south_migrationhistory` VALUES
          (1,'db','0001_initial','2014-03-18 13:38:11'),
          (2,'db','0002_auto__del_unique_node_name__chg_field_node_remark','2014-10-30 14:00:09'),
          (3,'db','0003_auto__add_index_teacherloginlog_created_at__add_index_teacherabsentlog','2014-10-30 14:30:21'),
          (4,'db','0004_auto__add_field_node_last_upload_time','2014-10-30 14:30:21'),
          (5,'db','0005_auto__add_field_node_db_version','2014-10-30 14:30:21'),
          (6,'db','0006_auto__add_field_usbkeyteacher_sync_uploaded','2014-10-30 14:30:21'),
          (7,'db','0007_auto__add_field_node_sync_status','2014-10-30 14:30:21'),
          (8,'db','0008_auto__add_classmacv2','2014-10-30 14:30:21'),
          (9,'db','0009_new_classmac','2014-10-30 14:30:21'),
          (10,'db','0010_auto__del_classmac','2014-10-30 14:30:21'),
          (11,'db','0011_auto__add_resourcefrom__add_unique_resourcefrom_school_value__add_reso','2014-10-30 14:30:21'),
          (12,'db','0012_auto__add_field_assetlog_asset_from','2014-10-30 14:30:21'),
          (13,'db','0013_auto__add_index_teacherloginlog_class_name__add_index_teacherloginlog_','2014-10-30 14:30:21'),
          (14,'db','0014_auto__add_field_assetrepairlog_country_name__add_field_assetlog_countr','2014-10-30 14:30:21'),
          (15,'db','0015_asset_type','2014-10-30 14:30:21'),
          (16,'db','0016_auto__add_desktoppicinfo','2014-10-30 14:30:21'),
          (17,'db','0017_auto__add_desktopglobalpreview__chg_field_desktoppicinfo_created_at','2014-10-30 14:30:21'),
          (18,'db','0018_auto__chg_field_desktoppicinfo_url','2014-10-30 14:30:21'),
          (19,'db','0019_auto__add_field_desktoppicinfo_host','2014-10-30 14:30:21'),
          (20,'db','0020_auto__add_totalteacherslesson__add_totalteachersgrade__add_totalteache','2014-10-30 14:30:21'),
          (21,'db','0021_auto__add_teacherlogintime__add_teacherlogintimetemp','2014-10-30 14:30:21'),
          (22,'db','0022_auto__add_teacherlogintimecache','2014-10-30 14:30:21'),
          (23,'db','0023_auto__chg_field_teacherlogintime_login_time__chg_field_teacherlogintim','2014-10-30 14:30:21'),
          (24,'db','0024_auto__add_teacherlogincountweekly','2014-10-30 14:30:21'),
          (25,'db','0025_auto__add_teacherlogintimeweekly','2014-10-30 14:30:21'),
          (26,'db','0026_auto__add_field_totalteacherslesson_term__add_field_totalteachersgrade','2014-10-30 14:30:21'),
          (27,'db','0027_calculate_teacher_active','2014-10-30 14:30:21'),
          (28,'db','0028_auto__add_synclogtemp__add_field_node_last_save_id','2014-10-30 14:30:21'),
          (29,'db','0029_auto__add_field_grade_number__add_field_class_number__add_field_class_','2014-10-30 14:30:21'),
          (30,'db','0029_auto__del_field_resourcefrom_school__del_unique_resourcefrom_school_va','2014-10-30 14:30:21'),
          (31,'db','0030_auto__add_classtime','2014-10-30 14:30:21'),
          (32,'db','0030_auto__add_newlessontype__add_newterm__add_newlessonname','2014-10-30 14:30:21'),
          (33,'db','0031_auto__chg_field_newlessontype_remark','2014-10-30 14:30:21'),
          (34,'db','0032_auto__add_field_grade_number__add_field_class_number__add_field_class_','2014-10-30 14:30:21'),
          (35,'db','0033_auto__add_newlessonnametype__add_classtime','2014-10-30 14:30:21'),
          (36,'db','0034_auto__add_field_term_schedule_time__add_field_newterm_schedule_time','2014-10-30 14:30:21'),
          (37,'db','0035_auto__add_field_newlessonname_country__add_field_newterm_country','2014-10-30 14:30:21'),
          (38,'db','0036_auto__add_field_newlessontype_country','2014-10-30 14:30:21'),
          (39,'db','0037_auto__add_field_resourcefrom_country__add_unique_resourcefrom_country_','2014-10-30 14:30:21'),
          (40,'db','0038_auto__add_courseware__add_teacherloginlogcourseware','2014-10-30 14:30:21'),
          (41,'db','0039_auto__add_syllabusgradelessoncontent__add_syllabusgrade__add_syllabusg','2014-10-30 14:30:21'),
          (42,'db','0040_auto__add_teacherloginloglessoncontent','2014-10-30 14:30:21'),
          (43,'db','0041_auto__add_countrytoschoolsynclog','2014-10-30 14:30:21'),
          (44,'db','0042_auto__chg_field_teacherloginloglessoncontent_lessoncontent__del_unique','2014-10-30 14:30:21'),
          (45,'db','0043_auto__add_field_lessonteacher_login_time','2014-10-30 14:30:21'),
          (46,'db','0044_calculate_lessonteacher_login_time','2014-10-30 14:30:21'),
          (47,'db','0045_init_schooluuid_countryuuid','2014-10-30 14:30:21'),
          (48,'db','0046_auto__add_field_syllabusgradelesson_publish__add_field_syllabusgradele','2014-10-30 14:30:21'),
          (49,'db','0047_auto__chg_field_syllabusgradelessoncontent_subseq__chg_field_syllabusg','2014-10-30 14:30:21'),
          (50,'db','0048_auto__add_countrytoresourceplatformsynclog','2014-10-30 14:30:21'),
          (51,'db','0049_auto__add_field_syllabusgradelesson_in_use','2014-10-30 14:30:22'),
          (52,'db','0050_auto__add_field_syllabusgradelesson_volume','2014-10-30 14:30:22'),
          (53,'db','0051_auto__add_field_classmacv2_ip','2014-10-30 14:30:22'),
          (54,'db','0052_auto__add_schoolpost','2014-10-30 14:30:22'),
          (55,'db','0053_auto__add_field_teacherlogintimetemp_last_login_datetime','2014-10-30 14:30:22'),
          (56,'db','0054_auto__add_computerclass','2014-10-30 14:30:22')"""
        cursor.execute(sql)

    def _migrate(self, db_version, cursor, obj):
        for i in range(99):
            if i <= db_version:
                continue
            func = getattr(self, 'mig_%d' % i, None)
            if func:
                self.stdout.write('migrate %d' % i)
                try:
                    func(cursor)
                except:
                    self.stdout.write('step %d: ' % i)
                    s = traceback.format_exc()
                    self.stdout.write(s + '\n')
                    break
                obj.value = str(i)
                obj.save()
            else:
                continue

    def handle(self, *args, **options):
        try:
            cursor = connection.cursor()
        except:
            s = traceback.format_exc()
            self.stdout.write(s)
            return
        try:
            cursor.execute("SELECT COUNT(*) FROM `south_migrationhistory`")
        except ProgrammingError:
            self.stdout.write('migrate from 687')
            migrate_from_687(cursor)
        except:
            s = traceback.format_exc()
            self.stdout.write(s)
            return
        else:
            self.stdout.write('newer than 687')
        try:
            name = 'migration_step'
            obj, c = models.Setting.objects.get_or_create(name=name)
            if c:
                self.stdout.write('set migration_step to 0')
                obj.value = '0'
                obj.save()
            try:
                step = int(obj.value)
            except:
                step = 0

            cursor.execute('SET unique_checks=0')
            cursor.execute('SET foreign_key_checks=0')
            self._migrate(step, cursor, obj)
            cursor.execute('SET unique_checks=1')
            cursor.execute('SET foreign_key_checks=1')
        except:
            s = traceback.format_exc()
            self.stdout.write(s)
