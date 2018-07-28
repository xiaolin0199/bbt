# coding=utf-8
# rebuild_synclog
from django.db import connection
from django.core.management.base import BaseCommand
from BanBanTong.db import models as m1
from machine_time_used import models as m2

N = 0


class Command(BaseCommand):
    '''
        重建SyncLog表
    '''

    def add_synclog(self, obj, operation_type='add'):
        global N
        m1.SyncLog.add_log(obj, operation_type)
        N += 1
        if N % 1000 == 0:
            print N

    def fix_info(self):
        term = m1.Term.get_current_term_list()[0]
        teacherlogintime = m1.TeacherLoginTime.objects.filter(school_year=term.school_year, term_type=term.term_type)
        for obj in teacherlogintime:
            if obj.login_time != obj.teacherloginlog.login_time:
                obj.teacherloginlog.login_time = obj.login_time
                obj.teacherloginlog.save()

    def run(self):

        term = m1.Term.get_current_term_list()[0]
        self.add_synclog(term, 'update')

        school = m1.Group.objects.get(group_type='school')
        self.add_synclog(school, 'update')

        lessons = m1.LessonName.objects.filter(school=school)
        for obj in lessons:
            self.add_synclog(obj, 'update')

        teachers = m1.Teacher.objects.filter(school=school)
        for obj in teachers:
            self.add_synclog(obj, 'update')

        grades = m1.Grade.objects.filter(term=term)
        for obj in grades:
            self.add_synclog(obj, 'update')

        classes = m1.Class.objects.filter(grade__in=grades)
        for obj in classes:
            self.add_synclog(obj, 'update')

        macs = m1.ClassMacV2.objects.filter(class_uuid__in=classes)
        for obj in macs:
            self.add_synclog(obj, 'update')

        classtimes = m1.ClassTime.objects.filter(class_uuid__in=classes)
        for obj in classtimes:
            self.add_synclog(obj, 'update')

        computerclasses = m1.ComputerClass.objects.filter(class_bind_to__in=classes)
        for obj in computerclasses:
            self.add_synclog(obj, 'update')

        computerclass_lessonranges = m1.ComputerClassLessonRange.objects.filter(computerclass__in=computerclasses)
        for obj in computerclass_lessonranges:
            self.add_synclog(obj, 'update')

        lessonperiod = m1.LessonPeriod.objects.filter(term=term)
        for obj in lessonperiod:
            self.add_synclog(obj, 'update')
        lessonschedule = m1.LessonSchedule.objects.filter(class_uuid__in=classes)
        for obj in lessonschedule:
            self.add_synclog(obj, 'update')
        lessonteacher = m1.LessonTeacher.objects.filter(class_uuid__in=classes)
        for obj in lessonteacher:
            self.add_synclog(obj, 'update')

        teacherloginlog = m1.TeacherLoginLog.objects.filter(term=term)
        for obj in teacherloginlog:
            self.add_synclog(obj)

        teacherlogintime = m1.TeacherLoginTime.objects.filter(school_year=term.school_year, term_type=term.term_type)
        for obj in teacherlogintime:
            self.add_synclog(obj)

        # courseware = m1.CourseWare.objects.filter(teacherloginlog__school_year=term.school_year, teacherloginlog__term_type=term.term_type)
        # for obj in courseware:
        #     self.add_synclog(obj)

        teacherloginlogtag = m1.TeacherLoginLogTag.objects.filter(created_at__in=classes)
        for obj in teacherloginlogtag:
            self.add_synclog(obj)

        teacherloginlogcourseware = m1.TeacherLoginLogCourseWare.objects.filter(school_year=term.school_year, term_type=term.term_type)
        for obj in teacherloginlogcourseware:
            self.add_synclog(obj.courseware)
            self.add_synclog(obj)

        desktoppicinfo = m1.DesktopPicInfo.objects.filter(school_year=term.school_year, term_type=term.term_type)
        for obj in desktoppicinfo:
            self.add_synclog(obj)

        desktoppicinfotag = m1.DesktopPicInfoTag.objects.filter(created_by__in=classes)
        for obj in desktoppicinfotag:
            self.add_synclog(obj)

        machinetimeused = m2.MachineTimeUsed.objects.filter(term_school_year=term.school_year, term_type=term.term_type)
        for obj in machinetimeused:
            self.add_synclog(obj)

    # def run(self):
    #     objs = [
    #         # m1.Setting,
    #         # m1.Group,
    #         #,
    #         m1.NewLessonName,
    #         m1.NewLessonType,
    #         m1.NewLessonNameType,
    #         m1.NewTerm,
    #         #,
    #         m1.AssetType,
    #         m1.Asset,
    #         m1.AssetLog,
    #         m1.AssetRepairLog,
    #         #,
    #         m1.Role,
    #         m1.RolePrivilege,
    #         m1.User,
    #         m1.UserPermittedGroup,
    #         #,
    #         # m1.Term,
    #         # m1.LessonName,
    #         # m1.Teacher,
    #         #,
    #         # m1.Grade,
    #         #,
    #         # m1.Class,
    #         # m1.ClassMacV2,
    #         # m1.ClassTime,
    #         # m1.ComputerClass,
    #         # m1.ComputerClassLessonRange,
    #         #,
    #         # m1.LessonPeriod,
    #         # m1.LessonSchedule,
    #         # m1.LessonTeacher,
    #         #,
    #         # m1.DesktopPicInfo,
    #         # m1.DesktopPicInfoTag,
    #         # m1.DesktopGlobalPreview,
    #         # m1.DesktopGlobalPreviewTag,
    #         #,
    #         # m1.Resource,
    #         # m1.ResourceFrom,
    #         # m1.ResourceType,
    #         #,
    #         # m1.TeacherLoginLog,
    #         # m1.TeacherLoginTime,
    #         # m1.CourseWare,
    #         # m1.TeacherLoginLogTag,
    #         # m1.TeacherLoginLogCourseWare,
    #         #,
    #         m1.SyllabusGrade,
    #         m1.SyllabusGradeLesson,
    #         m1.SyllabusGradeLessonContent,
    #         m1.TeacherLoginLogLessonContent,
    #         #,
    #         m2.MachineTimeUsed
    #     ]
    #     for obj in objs:
    #         for o in obj.objects.all():
    #             self.add_synclog(o)

    def handle(self, *args, **options):
        self.fix_info()
        cursor = connection.cursor()
        cursor.execute('TRUNCATE TABLE synclog')
        self.run()
