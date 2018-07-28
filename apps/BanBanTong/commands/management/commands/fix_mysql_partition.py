#!/usr/bin/env python
# coding=utf-8
import datetime
import hashlib
import math
import random
import uuid
import MySQLdb
import threading

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


DEBUG = True


class Command(BaseCommand):

    cursor = connection.cursor()

    def parti_teacherloginlog(self):
        '''
             处理 TeacherLoginLog
        '''
        self.cursor.execute('DROP TABLE IF EXISTS `TeacherLoginLog`')

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS `TeacherLoginLog` (
  `uuid` varchar(40) NOT NULL,
  `teacher_name` varchar(100) NOT NULL,
  `lesson_name` varchar(20) NOT NULL,
  `province_name` varchar(100) NOT NULL,
  `city_name` varchar(100) NOT NULL,
  `country_name` varchar(100) NOT NULL,
  `town_name` varchar(100) NOT NULL,
  `school_name` varchar(100) NOT NULL,
  `term_school_year` varchar(20) NOT NULL,
  `term_type` varchar(20) NOT NULL,
  `term_start_date` date NOT NULL,
  `term_end_date` date NOT NULL,
  `grade_name` varchar(20) NOT NULL,
  `class_name` varchar(20) NOT NULL,
  `lesson_period_sequence` int(11) NOT NULL,
  `lesson_period_start_time` time NOT NULL,
  `lesson_period_end_time` time NOT NULL,
  `weekday` varchar(10) NOT NULL,
  `teacher_uuid` varchar(40) DEFAULT NULL,
  `province_uuid` varchar(40) NOT NULL,
  `city_uuid` varchar(40) NOT NULL,
  `country_uuid` varchar(40) DEFAULT NULL,
  `town_uuid` varchar(40) DEFAULT NULL,
  `school_uuid` varchar(40) NOT NULL,
  `term_uuid` varchar(40) DEFAULT NULL,
  `grade_uuid` varchar(40) DEFAULT NULL,
  `class_uuid` varchar(40) DEFAULT NULL,
  `lesson_period_uuid` varchar(40) DEFAULT NULL,
  `lesson_teacher_uuid` varchar(40) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `resource_from` varchar(50) NOT NULL,
  `resource_type` varchar(20) NOT NULL,
  PRIMARY KEY (`uuid`,`term_school_year`),
  KEY `TeacherLoginLog_c12e9d48` (`teacher_uuid`),
  KEY `TeacherLoginLog_35b8c010` (`province_uuid`),
  KEY `TeacherLoginLog_b376980e` (`city_uuid`),
  KEY `TeacherLoginLog_d860be3c` (`country_uuid`),
  KEY `TeacherLoginLog_850831a2` (`town_uuid`),
  KEY `TeacherLoginLog_abbc0ae2` (`school_uuid`),
  KEY `TeacherLoginLog_22e62ab6` (`term_uuid`),
  KEY `TeacherLoginLog_d91b8533` (`grade_uuid`),
  KEY `TeacherLoginLog_6a845960` (`class_uuid`),
  KEY `TeacherLoginLog_31010cd6` (`lesson_period_uuid`),
  KEY `TeacherLoginLog_0daf5bdd` (`lesson_teacher_uuid`),
  KEY `TeacherLoginLog_term_school_year_538bbd54e7068ec4` (`term_school_year`,`term_type`,`town_name`,`school_name`,`grade_name`,`class_name`,`lesson_name`,`teacher_name`,`lesson_period_sequence`),
  KEY `TeacherLoginLog_created_at_70612eb63b24d4f6` (`created_at`,`town_name`,`school_name`,`grade_name`,`class_name`,`lesson_name`,`teacher_name`,`lesson_period_sequence`),
  KEY `TeacherLoginLog_created_at_6e5bdc58c20ff848` (`created_at`,`grade_name`,`class_name`,`lesson_name`,`teacher_name`,`lesson_period_sequence`),
  KEY `TeacherLoginLog_term_school_year_d268f3340db21c6` (`term_school_year`,`term_type`,`grade_name`,`class_name`,`lesson_name`,`teacher_name`,`lesson_period_sequence`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8
PARTITION BY LIST COLUMNS(`term_school_year`)
(
    PARTITION P20132014 VALUES IN ('2013-2014'),
    PARTITION P20142015 VALUES IN ('2014-2015'),
    PARTITION P20152016 VALUES IN ('2015-2016'),
    PARTITION P20162017 VALUES IN ('2016-2017'),
    PARTITION P20172018 VALUES IN ('2017-2018'),
    PARTITION P20182019 VALUES IN ('2018-2019'),
    PARTITION P20192020 VALUES IN ('2019-2020'),
    PARTITION P20202021 VALUES IN ('2020-2021'),
    PARTITION P20212022 VALUES IN ('2021-2022'),
    PARTITION P20222023 VALUES IN ('2022-2023'),
    PARTITION P20232024 VALUES IN ('2023-2024'),
    PARTITION Pnull VALUES IN ('', NULL)
);""")

    def parti_activeteachers(self):
        '''
            处理 db_activeteachers
        '''
        self.cursor.execute('DROP TABLE IF EXISTS `db_activeteachers`')

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS `db_activeteachers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `teacher_uuid` varchar(40) NOT NULL,
  `active_date` date NOT NULL,
  `country_name` varchar(100) NOT NULL,
  `town_name` varchar(100) NOT NULL,
  `school_name` varchar(100) NOT NULL,
  `school_year` varchar(20) NOT NULL,
  `term_type` varchar(20) NOT NULL,
  `lesson_name` varchar(20) NOT NULL,
  `grade_name` varchar(20) NOT NULL,
  PRIMARY KEY (`id`,`school_year`),
  KEY `db_activeteachers_c12e9d48` (`teacher_uuid`),
  KEY `db_activeteachers_active_date_4fab03be19f0b4ee` (`active_date`,`town_name`,`school_name`,`grade_name`),
  KEY `db_activeteachers_school_year_1e6bd04f27a86cc` (`school_year`,`term_type`,`town_name`,`school_name`,`lesson_name`),
  KEY `db_activeteachers_school_year_2d6d7e1fc132a630` (`school_year`,`term_type`,`lesson_name`,`grade_name`),
  KEY `db_activeteachers_active_date_6c551b5036f4ab0e` (`active_date`,`lesson_name`,`grade_name`),
  KEY `db_activeteachers_school_year_59738905a240aa08` (`school_year`,`term_type`,`town_name`,`school_name`,`grade_name`),
  KEY `db_activeteachers_active_date_2bbb4a429026842a` (`active_date`,`town_name`,`school_name`,`lesson_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8
PARTITION BY LIST COLUMNS(`school_year`)
(
    PARTITION P20132014 VALUES IN ('2013-2014'),
    PARTITION P20142015 VALUES IN ('2014-2015'),
    PARTITION P20152016 VALUES IN ('2015-2016'),
    PARTITION P20162017 VALUES IN ('2016-2017'),
    PARTITION P20172018 VALUES IN ('2017-2018'),
    PARTITION P20182019 VALUES IN ('2018-2019'),
    PARTITION P20192020 VALUES IN ('2019-2020'),
    PARTITION P20202021 VALUES IN ('2020-2021'),
    PARTITION P20212022 VALUES IN ('2021-2022'),
    PARTITION P20222023 VALUES IN ('2022-2023'),
    PARTITION P20232024 VALUES IN ('2023-2024'),
    PARTITION Pnull VALUES IN ('', NULL)
);""")

    def parti_machinetimeused(self):
        '''
            处理 machine_time_used_machinetimeused
        '''
        self.cursor.execute('DROP TABLE IF EXISTS `machine_time_used_machinetimeused`')

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS `machine_time_used_machinetimeused` (
  `uuid` bigint(20) NOT NULL,
  `term_school_year` varchar(20) NOT NULL,
  `term_type` varchar(20) NOT NULL,
  `province_name` varchar(100) NOT NULL,
  `city_name` varchar(100) NOT NULL,
  `country_name` varchar(100) NOT NULL,
  `town_name` varchar(100) NOT NULL,
  `school_name` varchar(100) NOT NULL,
  `grade_name` varchar(20) NOT NULL,
  `class_name` varchar(20) NOT NULL,
  `create_time` datetime NOT NULL,
  `use_time` int(11) NOT NULL,
  `use_count` int(11) NOT NULL,
  `mac` varchar(20) NOT NULL,
  `school_uuid` varchar(40),
  PRIMARY KEY (`uuid`,`term_school_year`),
  KEY `machine_time_used_machinetimeused_abbc0ae2` (`school_uuid`),
  KEY `machine_time_used_machinetime_term_school_year_77eb484d992d7dba` (`term_school_year`,`term_type`,`grade_name`,`class_name`),
  KEY `machine_time_used_machinetimeused_create_time_633607ef299eb97d` (`create_time`,`town_name`,`school_name`,`grade_name`,`class_name`),
  KEY `machine_time_used_machinetime_term_school_year_55ef439d0e228e74` (`term_school_year`,`term_type`,`town_name`,`school_name`,`grade_name`,`class_name`),
  KEY `machine_time_used_machinetimeused_create_time_2d53704a0673c723` (`create_time`,`grade_name`,`class_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8
PARTITION BY LIST COLUMNS(`term_school_year`)
(
    PARTITION P20132014 VALUES IN ('2013-2014'),
    PARTITION P20142015 VALUES IN ('2014-2015'),
    PARTITION P20152016 VALUES IN ('2015-2016'),
    PARTITION P20162017 VALUES IN ('2016-2017'),
    PARTITION P20172018 VALUES IN ('2017-2018'),
    PARTITION P20182019 VALUES IN ('2018-2019'),
    PARTITION P20192020 VALUES IN ('2019-2020'),
    PARTITION P20202021 VALUES IN ('2020-2021'),
    PARTITION P20212022 VALUES IN ('2021-2022'),
    PARTITION P20222023 VALUES IN ('2022-2023'),
    PARTITION P20232024 VALUES IN ('2023-2024'),
    PARTITION Pnull VALUES IN ('', NULL)
);""")

    def parti_teacherabsentlog(self):
        '''
            处理 TeacherAbsentLog
        '''
        self.cursor.execute('DROP TABLE IF EXISTS `TeacherAbsentLog`')

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS `TeacherAbsentLog` (
  `uuid` varchar(40) NOT NULL,
  `teacher_name` varchar(100) NOT NULL,
  `lesson_name` varchar(20) NOT NULL,
  `province_name` varchar(100) NOT NULL,
  `city_name` varchar(100) NOT NULL,
  `country_name` varchar(100) NOT NULL,
  `town_name` varchar(100) NOT NULL,
  `school_name` varchar(100) NOT NULL,
  `term_school_year` varchar(20) NOT NULL,
  `term_type` varchar(20) NOT NULL,
  `term_start_date` date NOT NULL,
  `term_end_date` date NOT NULL,
  `grade_name` varchar(20) NOT NULL,
  `class_name` varchar(20) NOT NULL,
  `lesson_period_sequence` int(11) NOT NULL,
  `lesson_period_start_time` time NOT NULL,
  `lesson_period_end_time` time NOT NULL,
  `weekday` varchar(10) NOT NULL,
  `teacher_uuid` varchar(40) DEFAULT NULL,
  `province_uuid` varchar(40) NOT NULL,
  `city_uuid` varchar(40) NOT NULL,
  `country_uuid` varchar(40) DEFAULT NULL,
  `town_uuid` varchar(40) DEFAULT NULL,
  `school_uuid` varchar(40) NOT NULL,
  `term_uuid` varchar(40) DEFAULT NULL,
  `grade_uuid` varchar(40) DEFAULT NULL,
  `class_uuid` varchar(40) DEFAULT NULL,
  `lesson_period_uuid` varchar(40) DEFAULT NULL,
  `lesson_teacher_uuid` varchar(40) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`uuid`,`term_school_year`),
  KEY `TeacherAbsentLog_c12e9d48` (`teacher_uuid`),
  KEY `TeacherAbsentLog_35b8c010` (`province_uuid`),
  KEY `TeacherAbsentLog_b376980e` (`city_uuid`),
  KEY `TeacherAbsentLog_d860be3c` (`country_uuid`),
  KEY `TeacherAbsentLog_850831a2` (`town_uuid`),
  KEY `TeacherAbsentLog_abbc0ae2` (`school_uuid`),
  KEY `TeacherAbsentLog_22e62ab6` (`term_uuid`),
  KEY `TeacherAbsentLog_d91b8533` (`grade_uuid`),
  KEY `TeacherAbsentLog_6a845960` (`class_uuid`),
  KEY `TeacherAbsentLog_31010cd6` (`lesson_period_uuid`),
  KEY `TeacherAbsentLog_0daf5bdd` (`lesson_teacher_uuid`),
  KEY `TeacherAbsentLog_term_school_year_793a45964ea1c3fb` (`term_school_year`,`term_type`,`town_name`,`school_name`,`grade_name`,`class_name`,`lesson_name`,`teacher_name`,`lesson_period_sequence`),
  KEY `TeacherAbsentLog_created_at_732226dfa86b618f` (`created_at`,`town_name`,`school_name`,`grade_name`,`class_name`,`lesson_name`,`teacher_name`,`lesson_period_sequence`),
  KEY `TeacherAbsentLog_created_at_61f40855f043de81` (`created_at`,`grade_name`,`class_name`,`lesson_name`,`teacher_name`,`lesson_period_sequence`),
  KEY `TeacherAbsentLog_term_school_year_3aa972cabf861f41` (`term_school_year`,`term_type`,`grade_name`,`class_name`,`lesson_name`,`teacher_name`,`lesson_period_sequence`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8
PARTITION BY LIST COLUMNS(`term_school_year`)
(
    PARTITION P20132014 VALUES IN ('2013-2014'),
    PARTITION P20142015 VALUES IN ('2014-2015'),
    PARTITION P20152016 VALUES IN ('2015-2016'),
    PARTITION P20162017 VALUES IN ('2016-2017'),
    PARTITION P20172018 VALUES IN ('2017-2018'),
    PARTITION P20182019 VALUES IN ('2018-2019'),
    PARTITION P20192020 VALUES IN ('2019-2020'),
    PARTITION P20202021 VALUES IN ('2020-2021'),
    PARTITION P20212022 VALUES IN ('2021-2022'),
    PARTITION P20222023 VALUES IN ('2022-2023'),
    PARTITION P20232024 VALUES IN ('2023-2024'),
    PARTITION Pnull VALUES IN ('', NULL)
);""")

    def parti_synclog(self):
        '''
            处理 SyncLog
        '''
        self.cursor.execute('DROP TABLE IF EXISTS `synclog`')
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS `synclog` (
            `created_at` bigint(20) NOT NULL AUTO_INCREMENT,
            `operation_type` varchar(10) NOT NULL,
            `operation_content` longtext NOT NULL,
            PRIMARY KEY (`created_at`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8 partition by range(`created_at`) (
            PARTITION p1 VALUES LESS THAN (2000000),
            PARTITION p2 VALUES LESS THAN (4000000),
            PARTITION p3 VALUES LESS THAN (6000000),
            PARTITION p4 VALUES LESS THAN (8000000),
            PARTITION p5 VALUES LESS THAN (10000000),
            PARTITION p6 VALUES LESS THAN (12000000),
            PARTITION p7 VALUES LESS THAN (14000000),
            PARTITION p8 VALUES LESS THAN (16000000),
            PARTITION p9 VALUES LESS THAN (18000000),
            PARTITION p10 VALUES LESS THAN (20000000),
            PARTITION pmax VALUES LESS THAN MAXVALUE
        );""")

    def parti_statistic(self):
        '''
            处理db_statistic
        '''
        self.cursor.execute('DROP TABLE IF EXISTS `db_statistic`')
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS `db_statistic` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `term` varchar(40),
  `parent_id` int(11) DEFAULT NULL,
  `key` varchar(400) NOT NULL,
  `name` varchar(100) NOT NULL,
  `type` varchar(20) NOT NULL,
  `school_year` varchar(20) NOT NULL,
  `term_type` varchar(20) NOT NULL,
  `class_count` int(11) NOT NULL,
  `teach_count` int(11) NOT NULL,
  `teach_time` int(11) NOT NULL,
  `teacher_num` int(11) NOT NULL,
  `last_update_count` datetime NOT NULL,
  `last_update_time` datetime NOT NULL,
  `last_update_num` datetime NOT NULL,
  `create_time` datetime NOT NULL,
  PRIMARY KEY (`id`,`school_year`),
  KEY `db_statistic_410d0aac` (`parent_id`),
  KEY `db_statistic_4da47e07` (`name`),
  KEY `db_statistic_403d8ff3` (`type`),
  KEY `db_statistic_0a0dd6b6` (`school_year`),
  KEY `db_statistic_af17dbbf` (`term_type`),
  KEY `db_statistic_school_year_16ae208f96cde00e` (`school_year`,`term_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8
PARTITION BY LIST COLUMNS(`school_year`)
(
    PARTITION P20132014 VALUES IN ('2013-2014'),
    PARTITION P20142015 VALUES IN ('2014-2015'),
    PARTITION P20152016 VALUES IN ('2015-2016'),
    PARTITION P20162017 VALUES IN ('2016-2017'),
    PARTITION P20172018 VALUES IN ('2017-2018'),
    PARTITION P20182019 VALUES IN ('2018-2019'),
    PARTITION P20192020 VALUES IN ('2019-2020'),
    PARTITION P20202021 VALUES IN ('2020-2021'),
    PARTITION P20212022 VALUES IN ('2021-2022'),
    PARTITION P20222023 VALUES IN ('2022-2023'),
    PARTITION P20232024 VALUES IN ('2023-2024'),
    PARTITION Pnull VALUES IN ('', NULL)
);""")

    def parti_teacherlogintimecache(self):
        '''
            处理 db_teacherlogintimecache
            UNIQUE KEY `teacherlogintime_id` (`teacherlogintime_id`)
            替换成
            KEY `teacherlogintime_id` (`teacherlogintime_id`),
        '''
        self.cursor.execute('DROP TABLE IF EXISTS `db_teacherlogintimecache`')
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS `db_teacherlogintimecache` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `town_uuid` varchar(40) NOT NULL,
  `school_uuid` varchar(40) NOT NULL,
  `grade_uuid` varchar(40) NOT NULL,
  `class_uuid` varchar(40) NOT NULL,
  `teacher_uuid` varchar(40) NOT NULL,
  `lesson_name` varchar(20) NOT NULL,
  `teacherlogintime_id` varchar(40) NOT NULL,
  `school_year` varchar(20),
  `term_type` varchar(20),
  PRIMARY KEY (`id`,`school_year`),
  KEY `teacherlogintime_id` (`teacherlogintime_id`),
  KEY `db_teacherlogintimecache_850831a2` (`town_uuid`),
  KEY `db_teacherlogintimecache_abbc0ae2` (`school_uuid`),
  KEY `db_teacherlogintimecache_d91b8533` (`grade_uuid`),
  KEY `db_teacherlogintimecache_6a845960` (`class_uuid`),
  KEY `db_teacherlogintimecache_c12e9d48` (`teacher_uuid`),
  KEY `db_teacherlogintimecache_5909220d` (`lesson_name`),
  KEY `db_teacherlogintimecache_school_year_3e6e4ad773a068a4` (`school_year`,`term_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8
PARTITION BY LIST COLUMNS(`school_year`)
(
    PARTITION P20132014 VALUES IN ('2013-2014'),
    PARTITION P20142015 VALUES IN ('2014-2015'),
    PARTITION P20152016 VALUES IN ('2015-2016'),
    PARTITION P20162017 VALUES IN ('2016-2017'),
    PARTITION P20172018 VALUES IN ('2017-2018'),
    PARTITION P20182019 VALUES IN ('2018-2019'),
    PARTITION P20192020 VALUES IN ('2019-2020'),
    PARTITION P20202021 VALUES IN ('2020-2021'),
    PARTITION P20212022 VALUES IN ('2021-2022'),
    PARTITION P20222023 VALUES IN ('2022-2023'),
    PARTITION P20232024 VALUES IN ('2023-2024'),
    PARTITION Pnull VALUES IN ('', NULL)
);""")

    def parti_teacherlogintime(self):
        '''
            处理db_teacherlogintime
        '''
        self.cursor.execute('DROP TABLE IF EXISTS `db_teacherlogintime`')
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS `db_teacherlogintime` (
  `uuid` varchar(40) NOT NULL,
  `teacherloginlog_id` varchar(40) NOT NULL,
  `login_time` int(11) NOT NULL,
  `school_year` varchar(20),
  `term_type` varchar(20),
  PRIMARY KEY (`uuid`,`school_year`),
  KEY `teacherloginlog_id` (`teacherloginlog_id`),
  KEY `db_teacherlogintime_school_year_24dfcecdd5ed4f51` (`school_year`,`term_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8
PARTITION BY LIST COLUMNS(`school_year`)
(
    PARTITION P20132014 VALUES IN ('2013-2014'),
    PARTITION P20142015 VALUES IN ('2014-2015'),
    PARTITION P20152016 VALUES IN ('2015-2016'),
    PARTITION P20162017 VALUES IN ('2016-2017'),
    PARTITION P20172018 VALUES IN ('2017-2018'),
    PARTITION P20182019 VALUES IN ('2018-2019'),
    PARTITION P20192020 VALUES IN ('2019-2020'),
    PARTITION P20202021 VALUES IN ('2020-2021'),
    PARTITION P20212022 VALUES IN ('2021-2022'),
    PARTITION P20222023 VALUES IN ('2022-2023'),
    PARTITION P20232024 VALUES IN ('2023-2024'),
    PARTITION Pnull VALUES IN ('', NULL)
);""")

    def parti_desktoppicinfo(self):
        '''
            处理 db_desktoppicinfo
        '''
        self.cursor.execute('DROP TABLE IF EXISTS `db_desktoppicinfo`')
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS `db_desktoppicinfo` (
  `uuid` varchar(40) NOT NULL,
  `school_uuid` varchar(40) NOT NULL,
  `grade_uuid` varchar(40) NOT NULL,
  `grade_number` int(11) NOT NULL,
  `class_uuid` varchar(40) NOT NULL,
  `class_number` int(11) NOT NULL,
  `lesson_name` varchar(20) NOT NULL,
  `teacher_name` varchar(100) NOT NULL,
  `lesson_period_sequence` int(11) NOT NULL,
  `url` varchar(180) NOT NULL,
  `created_at` datetime NOT NULL,
  `host` varchar(180) NOT NULL,
  `school_year` varchar(20),
  `term_type` varchar(20),
  PRIMARY KEY (`uuid`,`school_year`),
  KEY `db_desktoppicinfo_abbc0ae2` (`school_uuid`),
  KEY `db_desktoppicinfo_d91b8533` (`grade_uuid`),
  KEY `db_desktoppicinfo_6a845960` (`class_uuid`),
  KEY `db_desktoppicinfo_class_uuid_77e9bf5c8c8a0654` (`class_uuid`,`school_uuid`,`lesson_period_sequence`),
  KEY `db_desktoppicinfo_class_uuid_4bb73d6b9a1b936f` (`class_uuid`,`created_at`,`lesson_period_sequence`),
  KEY `db_desktoppicinfo_school_year_3c53253ac0cf0f03` (`school_year`,`term_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8
PARTITION BY LIST COLUMNS(`school_year`)
(
    PARTITION P20132014 VALUES IN ('2013-2014'),
    PARTITION P20142015 VALUES IN ('2014-2015'),
    PARTITION P20152016 VALUES IN ('2015-2016'),
    PARTITION P20162017 VALUES IN ('2016-2017'),
    PARTITION P20172018 VALUES IN ('2017-2018'),
    PARTITION P20182019 VALUES IN ('2018-2019'),
    PARTITION P20192020 VALUES IN ('2019-2020'),
    PARTITION P20202021 VALUES IN ('2020-2021'),
    PARTITION P20212022 VALUES IN ('2021-2022'),
    PARTITION P20222023 VALUES IN ('2022-2023'),
    PARTITION P20232024 VALUES IN ('2023-2024'),
    PARTITION Pnull VALUES IN ('', NULL)
);""")

    def parti_teacherloginlogcourseware(self):
        '''
            处理 teacherloginlogcourseware
        '''
        self.cursor.execute('DROP TABLE IF EXISTS `teacherloginlogcourseware`')
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS `teacherloginlogcourseware` (
  `uuid` varchar(40) NOT NULL,
  `courseware_uuid` varchar(40) NOT NULL,
  `teacherloginlog_uuid` varchar(40) NOT NULL,
  `school_year` varchar(20),
  `term_type` varchar(20),
  PRIMARY KEY (`uuid`,`school_year`),
  KEY `TeacherLoginLogCourseWare_a0135362` (`courseware_uuid`),
  KEY `TeacherLoginLogCourseWare_65a31c80` (`teacherloginlog_uuid`),
  KEY `TeacherLoginLogCourseWare_school_year_40ab1b3e045e5e91` (`school_year`,`term_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8
PARTITION BY LIST COLUMNS(`school_year`)
(
    PARTITION P20132014 VALUES IN ('2013-2014'),
    PARTITION P20142015 VALUES IN ('2014-2015'),
    PARTITION P20152016 VALUES IN ('2015-2016'),
    PARTITION P20162017 VALUES IN ('2016-2017'),
    PARTITION P20172018 VALUES IN ('2017-2018'),
    PARTITION P20182019 VALUES IN ('2018-2019'),
    PARTITION P20192020 VALUES IN ('2019-2020'),
    PARTITION P20202021 VALUES IN ('2020-2021'),
    PARTITION P20212022 VALUES IN ('2021-2022'),
    PARTITION P20222023 VALUES IN ('2022-2023'),
    PARTITION P20232024 VALUES IN ('2023-2024'),
    PARTITION Pnull VALUES IN ('', NULL)
);""")

    def parti_teacherloginloglessoncontent(self):
        '''
            处理 teacherloginloglessoncontent
        '''
        self.cursor.execute('DROP TABLE IF EXISTS `teacherloginloglessoncontent`')
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS `teacherloginloglessoncontent` (
  `uuid` varchar(40) NOT NULL,
  `teacherloginlog_uuid` varchar(40) NOT NULL,
  `title` varchar(100) DEFAULT NULL,
  `lessoncontent_id` int(11) DEFAULT NULL,
  `school_year` varchar(20),
  `term_type` varchar(20),
  PRIMARY KEY (`uuid`, `school_year`),
  KEY `teacherloginlog_uuid` (`teacherloginlog_uuid`),
  KEY `TeacherLoginLogLessonContent_c914553e` (`lessoncontent_id`),
  KEY `TeacherLoginLogLessonContent_school_year_62939c642e6bf9e3` (`school_year`,`term_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8
PARTITION BY LIST COLUMNS(`school_year`)
(
    PARTITION P20132014 VALUES IN ('2013-2014'),
    PARTITION P20142015 VALUES IN ('2014-2015'),
    PARTITION P20152016 VALUES IN ('2015-2016'),
    PARTITION P20162017 VALUES IN ('2016-2017'),
    PARTITION P20172018 VALUES IN ('2017-2018'),
    PARTITION P20182019 VALUES IN ('2018-2019'),
    PARTITION P20192020 VALUES IN ('2019-2020'),
    PARTITION P20202021 VALUES IN ('2020-2021'),
    PARTITION P20212022 VALUES IN ('2021-2022'),
    PARTITION P20222023 VALUES IN ('2022-2023'),
    PARTITION P20232024 VALUES IN ('2023-2024'),
    PARTITION Pnull VALUES IN ('', NULL)
);""")

    def parti_teacherlogintimeweekly(self):
        '''
            处理 db_teacherlogintimeweekly
        '''
        self.cursor.execute('DROP TABLE IF EXISTS `db_teacherlogintimeweekly`')
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS `db_teacherlogintimeweekly` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `town_name` varchar(100) NOT NULL,
  `school_name` varchar(100) NOT NULL,
  `term_uuid` varchar(40) NOT NULL,
  `grade_name` varchar(20) NOT NULL,
  `class_name` varchar(20) NOT NULL,
  `week` int(11) NOT NULL,
  `total_time` int(11) NOT NULL,
  `school_year` varchar(20),
  `term_type` varchar(20),
  PRIMARY KEY (`id`,`school_year`),
  KEY `db_teacherlogintimeweekly_a5b9273f` (`town_name`),
  KEY `db_teacherlogintimeweekly_56ac288e` (`school_name`),
  KEY `db_teacherlogintimeweekly_22e62ab6` (`term_uuid`),
  KEY `db_teacherlogintimeweekly_8a60ca00` (`grade_name`),
  KEY `db_teacherlogintimeweekly_6151272e` (`class_name`),
  KEY `db_teacherlogintimeweekly_9136095f` (`week`),
  KEY `db_teacherlogintimeweekly_town_name_5ca5b229ee657a21` (`town_name`,`school_name`,`grade_name`,`class_name`,`week`),
  KEY `db_teacherlogintimeweekly_school_year_43961d9fc9f0cdd2` (`school_year`,`term_type`,`town_name`,`school_name`,`grade_name`,`class_name`,`week`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8
PARTITION BY LIST COLUMNS(`school_year`)
(
    PARTITION P20132014 VALUES IN ('2013-2014'),
    PARTITION P20142015 VALUES IN ('2014-2015'),
    PARTITION P20152016 VALUES IN ('2015-2016'),
    PARTITION P20162017 VALUES IN ('2016-2017'),
    PARTITION P20172018 VALUES IN ('2017-2018'),
    PARTITION P20182019 VALUES IN ('2018-2019'),
    PARTITION P20192020 VALUES IN ('2019-2020'),
    PARTITION P20202021 VALUES IN ('2020-2021'),
    PARTITION P20212022 VALUES IN ('2021-2022'),
    PARTITION P20222023 VALUES IN ('2022-2023'),
    PARTITION P20232024 VALUES IN ('2023-2024'),
    PARTITION Pnull VALUES IN ('', NULL)
);""")

    def parti_teacherlogincountweekly(self):
        '''
            处理 db_teacherlogincountweekly
        '''
        self.cursor.execute('DROP TABLE IF EXISTS `db_teacherlogincountweekly`')
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS `db_teacherlogincountweekly` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `town_name` varchar(100) NOT NULL,
  `school_name` varchar(100) NOT NULL,
  `term_uuid` varchar(40) NOT NULL,
  `grade_name` varchar(20) NOT NULL,
  `class_name` varchar(20) NOT NULL,
  `week` int(11) NOT NULL,
  `lesson_count` int(11) NOT NULL,
  `school_year` varchar(20),
  `term_type` varchar(20),
  PRIMARY KEY (`id`, `school_year`),
  KEY `db_teacherlogincountweekly_a5b9273f` (`town_name`),
  KEY `db_teacherlogincountweekly_56ac288e` (`school_name`),
  KEY `db_teacherlogincountweekly_22e62ab6` (`term_uuid`),
  KEY `db_teacherlogincountweekly_8a60ca00` (`grade_name`),
  KEY `db_teacherlogincountweekly_6151272e` (`class_name`),
  KEY `db_teacherlogincountweekly_9136095f` (`week`),
  KEY `db_teacherlogincountweekly_town_name_392a418dc9d117f4` (`town_name`,`school_name`,`grade_name`,`class_name`,`week`),
  KEY `db_teacherlogincountweekly_school_year_75a8ba1caf804fff` (`school_year`,`term_type`,`town_name`,`school_name`,`grade_name`,`class_name`,`week`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8
PARTITION BY LIST COLUMNS(`school_year`)
(
    PARTITION P20132014 VALUES IN ('2013-2014'),
    PARTITION P20142015 VALUES IN ('2014-2015'),
    PARTITION P20152016 VALUES IN ('2015-2016'),
    PARTITION P20162017 VALUES IN ('2016-2017'),
    PARTITION P20172018 VALUES IN ('2017-2018'),
    PARTITION P20182019 VALUES IN ('2018-2019'),
    PARTITION P20192020 VALUES IN ('2019-2020'),
    PARTITION P20202021 VALUES IN ('2020-2021'),
    PARTITION P20212022 VALUES IN ('2021-2022'),
    PARTITION P20222023 VALUES IN ('2022-2023'),
    PARTITION P20232024 VALUES IN ('2023-2024'),
    PARTITION Pnull VALUES IN ('', NULL)
);""")

    def fix(self):
        '''
            进行大表partition分区处理
        '''
        # TeacherLoginLog
        self.parti_teacherloginlog()

        # TeacherAbsentLog
        self.parti_teacherabsentlog()

        # db_activeteachers
        self.parti_activeteachers()

        # SyncLog
        self.parti_synclog()

        # machine_time_used_machinetimeused
        self.parti_machinetimeused()

        # db_teacherlogintimecache
        self.parti_teacherlogintimecache()

        # db_teacherlogintime
        self.parti_teacherlogintime()

        # db_desktoppicinfo
        self.parti_desktoppicinfo()

        # TeacherLoginLogCourseWare
        self.parti_teacherloginlogcourseware()

        # TeacherLoginLogLessonContent
        self.parti_teacherloginloglessoncontent()

        # db_statistic
        self.parti_statistic()

        # db_teacherlogintimeweekly
        self.parti_teacherlogintimeweekly()

        # db_teacherlogincountweekly
        self.parti_teacherlogincountweekly()

    def handle(self, *args, **options):
        self.cursor.execute('SET unique_checks=0')
        self.cursor.execute('SET foreign_key_checks=0')

        self.fix()

        self.cursor.execute('SET unique_checks=1')
        self.cursor.execute('SET foreign_key_checks=1')
