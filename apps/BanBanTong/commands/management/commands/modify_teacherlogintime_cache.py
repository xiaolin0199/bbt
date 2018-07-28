#coding=utf-8
import datetime
import logging
import traceback
from django.core.management.base import BaseCommand
from BanBanTong.db import models
from django.conf import settings
from django.db import connection
from django.db.models import F


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''
        手动更新 TeacherLoginTime 和 TeacherLoginTimeCache
        原则:
            根据这二张表添加二个字段,school_year , term_type
    '''
    cursor = connection.cursor()
    
    def modify_teacherlogintime(self, term):
        school_year = term.school_year
        term_type = term.term_type
        models.TeacherLoginTime.objects.filter(teacherloginlog__term=term, school_year='').update(school_year=school_year, term_type=term_type)

    
    def modify_teacherlogintimecache(self, term):
        # Django不支持这种写法，update里的F函数只能是本表字段，不能外键延伸，但如果是filter可以
#models.TeacherLoginTimeCache.objects.filter(teacherlogintime__teacherloginlog__term=term).update(school_year=F('teacherlogintime__teacherloginlog__term_school_year'), term_type=F('teacherlogintime__teacherloginlog__term_type'))
        school_year = term.school_year
        term_type = term.term_type        
        models.TeacherLoginTimeCache.objects.filter(teacherlogintime__teacherloginlog__term=term, school_year='').update(school_year=school_year, term_type=term_type)
        
    
    def modify_desktoppicinfo(self, term):
        school_year = term.school_year
        term_type = term.term_type 
        models.DesktopPicInfo.objects.filter(grade__term=term, school_year='').update(school_year=school_year, term_type=term_type)
        
    def modify_teacherloginlogcourseware(self, term):
        school_year = term.school_year
        term_type = term.term_type 
        models.TeacherLoginLogCourseWare.objects.filter(teacherloginlog__term=term, school_year='').update(school_year=school_year, term_type=term_type)  
        
    def modify_teacherloginloglessoncontent(self, term):
        school_year = term.school_year
        term_type = term.term_type 
        models.TeacherLoginLogLessonContent.objects.filter(teacherloginlog__term=term, school_year='').update(school_year=school_year, term_type=term_type)   
        
    def modify_teacherlogintimeweekly(self, term):
        school_year = term.school_year
        term_type = term.term_type 
        models.TeacherLoginTimeWeekly.objects.filter(term=term, school_year='').update(school_year=school_year, term_type=term_type)
        
    def modify_teacherlogincountweekly(self, term):
        school_year = term.school_year
        term_type = term.term_type 
        models.TeacherLoginCountWeekly.objects.filter(term=term, school_year='').update(school_year=school_year, term_type=term_type)    
        

    def modify_teacherloginlog_logintime(self, term):   
        #error = 0     
        objs = models.TeacherLoginTime.objects.filter(teacherloginlog__term=term)
        for obj in objs:
            try:
                #obj.teacherloginlog.login_time = obj.login_time
                #obj.teacherloginlog.save()
                models.TeacherLoginLog.objects.filter(teacherlogintime=obj).update(login_time=obj.login_time)
            except:
                #error += 1
                pass
            
        #print error
        #objs = models.TeacherLoginLog.objects.filter(term=term).update(login_time=F('teacherlogintime__login_time'))

    def handle(self, *args, **options):

        self.cursor.execute('SET unique_checks=0')
        self.cursor.execute('SET foreign_key_checks=0')    
        
        terms = models.Term.objects.all()    
            
        # 先db_teacherlogintime
        for term in terms:
            print '1.Time: ' , term.school_year , term.term_type , term.school.name
            self.modify_teacherlogintime(term)
        print 'start OPTIMIZE TABLE `db_teacherlogintime`'
        self.cursor.execute('OPTIMIZE TABLE `db_teacherlogintime`')
        
        # 再db_teacherlogintimecache, 用到了teacherlogintime先生成的school_year, term_type数据
        for term in terms:
            print '2.Time Cache: ' , term.school_year , term.term_type , term.school.name
            self.modify_teacherlogintimecache(term)
        print 'start OPTIMIZE TABLE `db_teacherlogintimecache`'
        self.cursor.execute('OPTIMIZE TABLE `db_teacherlogintimecache`')
            
        # 接着处理 db_desktoppicinfo
        for term in terms:
            print '3.Pic Info: ' , term.school_year , term.term_type , term.school.name
            self.modify_desktoppicinfo(term)
        print 'start OPTIMIZE TABLE `db_desktoppicinfo`'
        self.cursor.execute('OPTIMIZE TABLE `db_desktoppicinfo`')
            
        # 然后 teacherloginlogcourseware
        for term in terms:
            print '4.CourseWare: ' , term.school_year , term.term_type , term.school.name
            self.modify_teacherloginlogcourseware(term)
        print 'start OPTIMIZE TABLE `teacherloginlogcourseware`'
        self.cursor.execute('OPTIMIZE TABLE `teacherloginlogcourseware`')
            
        # 处理 teacherloginloglessoncontent
        for term in terms:
            print '5.Lesson Content: ' , term.school_year , term.term_type , term.school.name
            self.modify_teacherloginloglessoncontent(term) 
        print 'start OPTIMIZE TABLE `teacherloginloglessoncontent`'
        self.cursor.execute('OPTIMIZE TABLE `teacherloginloglessoncontent`')
            
        # 处理 db_teacherlogintimeweekly
        for term in terms:
            print '6.Login Time Weekly: ' , term.school_year , term.term_type , term.school.name
            self.modify_teacherlogintimeweekly(term)
        print 'start OPTIMIZE TABLE `db_teacherlogintimeweekly`'
        self.cursor.execute('OPTIMIZE TABLE `db_teacherlogintimeweekly`')
        
        # 处理 db_teacherlogincountweekly
        for term in terms:
            print '7.Login Count Weekly: ' , term.school_year , term.term_type , term.school.name
            self.modify_teacherlogincountweekly(term)  
        print 'start OPTIMIZE TABLE `db_teacherlogincountweekly`'
        self.cursor.execute('OPTIMIZE TABLE `db_teacherlogincountweekly`')
        
        # 处理teacherloginlog中的login_time字段
        for term in terms:
            print '8. update teacherloginlog login time: ' , term.school_year , term.term_type , term.school.name
            self.modify_teacherloginlog_logintime(term)

        self.cursor.execute('SET unique_checks=1')
        self.cursor.execute('SET foreign_key_checks=1')        