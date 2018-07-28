# coding=utf-8
import datetime
import logging
import json
import traceback
from django import forms
from BanBanTong.db import models
from BanBanTong.views.system.lesson_schedule import update_lessonschedule

logger = logging.getLogger(__name__)


def check_token(current_token):
    """
    客户端提前上课,那么需要通过token判断是否已经有客户端登录过该班级
    """
    # check_token会做下面几件事
    # 1.清除Token表中的脏数据(lesson_start)
    # 2.如果是重复提交,则更新当前班级的Token(电脑教室更换上课班级)
    # 3.判断欲上课的班级是否已经在异地登录
    models.Token.clean_bad_tokens()
    tokens = models.Token.objects.filter(token_type='lesson_start')
    if tokens.exists():
        for token in tokens:  # 遍历token
            early_token = json.loads(token.info)
            if early_token['class'] == current_token['class'] or \
                    early_token['teacher'] == current_token['teacher']:
                # 定位上课的班级 定位上课的教师
                uuid1 = early_token.get('token_created_at')
                uuid2 = current_token.get('token_created_at')
                if uuid1 and uuid2 and uuid1 != uuid2:
                    return False, early_token

            if early_token['token_created_at'] == current_token['token_created_at']:
                # 定位点击上课的客户端所在班级/电脑教室
                # 如果该客户端重新点击上课的 班级/授课教师/课程 有变化的话,
                # 那么删除旧的token,标记可以点击登录
                a = early_token['class']
                a1 = current_token['class']
                b = early_token['teacher']
                b1 = current_token['teacher']
                c = early_token['lesson_name']
                c1 = current_token['lesson_name']
                if not (a == a1 and b == b1 and c == c1):
                    token.delete()
                    return True, None

    return True, None


def check_loged_teacher(current_class_obj, teacher_uuid):
    """
        查询当前的教师是否已经在其他客户端登录上课
        如果已经登录, 那么当前的登录将会被限制多客户端登录
        return (can_login, another_class)
    """
    lp = models.LessonPeriod.get_current_or_next_period()
    if not lp:
        # return can_login, another_class
        return True, None
    today = datetime.datetime.now().date()
    s = datetime.datetime.combine(today, lp.start_time)
    e = datetime.datetime.combine(today, lp.end_time)
    log = models.TeacherLoginLog.objects.filter(
        teacher=teacher_uuid,
        lesson_period=lp,
        created_at__range=(s, e)
    )
    if log.exists():
        log = log[0]
        if current_class_obj.uuid != log.class_uuid:
            class_name = u'%s年级%s班' % (log.grade_name, log.class_name)
            return False, class_name
    return True, None


class LessonStartForm(forms.Form):
    username = forms.CharField(max_length=40)
    password = forms.CharField(max_length=128)
    mac = forms.CharField()
    lesson_name = forms.CharField(max_length=40)
    resource_type = forms.CharField(max_length=20, required=False)
    resource_from = forms.CharField(max_length=50, required=False)
    lessoncontent = forms.IntegerField(required=False)

    def __init__(self, *args, **kwargs):
        super(LessonStartForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(LessonStartForm, self).clean()
        teacher_uuid = cleaned_data.get('username')
        password = cleaned_data.get('password')
        lesson_name = cleaned_data.get('lesson_name')
        mac = cleaned_data.get('mac')

        # 注意：考虑到调课的情况，username/password/lesson_name
        #       可能与LessonSchedule/LessonTeacher不匹配
        t = None  # teacher
        c = None  # class_uuid
        l = None  # lesson_name
        # ls = None  # LessonSchedule

        # 获取上课的班级
        try:
            term = models.Term.get_current_term_list()[0]
            try:
                # 多网卡的情况下,前端传入了多个MAC('mac1,mac2,..')
                macs = mac.split(',')
                c = models.Class.objects.get(
                    classmacv2__mac__in=macs,
                    grade__term=term
                )
            except:
                c = models.Class.objects.get(uuid=mac)
        except:
            if cleaned_data.has_key('mac'):
                del cleaned_data['mac']
            self._errors['mac'] = self.error_class(['服务器中未找到该班级'])

        # 限制同一个教师同一时刻只能在一个班级登录
        can_login, another_class = check_loged_teacher(c, teacher_uuid)
        if not can_login:
            if cleaned_data.has_key('username'):
                del cleaned_data['username']
            self._errors['username'] = self.error_class([u'已在[%s]登录上课' % another_class])

        # 检查username和password
        try:
            t = models.Teacher.objects.get(uuid=teacher_uuid, password=password)
            if t.deleted:
                if 'username' in cleaned_data:
                    del cleaned_data['username']
                self._errors['username'] = self.error_class(['该教师已删除'])
        except:
            if 'username' in cleaned_data:
                del cleaned_data['username']
            if 'password' in cleaned_data:
                del cleaned_data['password']
            self._errors['username'] = self.error_class(['用户名或密码错误'])

        # 检查lesson_name
        try:
            l = models.LessonName.objects.get(pk=lesson_name)
        except:
            traceback.print_exc()
            if cleaned_data.has_key('lesson_name'):
                del cleaned_data['lesson_name']
            self._errors['lesson_name'] = self.error_class(['错误的课程名'])

        lp = models.LessonPeriod.get_current_or_next_period()
        now = datetime.datetime.now()
        started = bool(lp.start_time <= now.time() <= lp.end_time)
        if not lp:
            del cleaned_data['mac']
            self._errors['mac'] = self.error_class(['今天的课程已经全部结束'])

        try:
            lt = models.LessonTeacher.objects.get(
                class_uuid=c,
                teacher=t,
                lesson_name=l
            )
        except:
            logger.debug(u'DEBUG 申报上课的教师并非计划内教师')
            lt = None

        self.c = c
        self.t = t
        self.l = l
        self.lp = lp
        self.lt = lt
        self.started = started
        return cleaned_data

    def save(self, computerclass=None):
        """
        如果当前已进入上课时间，就直接上课；如果未进入上课时间，就创建token
        """

        resource_from = self.cleaned_data['resource_from']
        resource_type = self.cleaned_data['resource_type']
        lessoncontent = self.cleaned_data['lessoncontent']
        now = datetime.datetime.now()
        if self.started:
            # 1.当前课程已经开始,那么写数据库教师登录记录
            try:
                log = None
                if self.lt:
                    self.lt.finished_time += 1
                    tips = None
                    try:
                        self.lt.save()
                    except Exception as e:
                        # LessonTeacher.calculate_total_teachers(lt_obj)
                        # 这里引起的异常导致登录失败
                        tips = str(e)
                        logger.exception('')

                    log = models.TeacherLoginLog.log_teacher('login',
                                                             teacher=self.lt.teacher,
                                                             lesson_name=self.l.name,
                                                             class_uuid=self.c,
                                                             lesson_period=self.lp,
                                                             resource_from=resource_from,
                                                             resource_type=resource_type,
                                                             lessoncontent=lessoncontent
                                                             )
                    # 更新课表 Newly updated: V4.3.0
                    update_lessonschedule(self.c, self.lp, self.l)
                return True, {
                    'started': True,
                    'server_time': now,
                    'time': self.lp.end_time,
                    'log': log,
                    '#debug0': tips and tips or 'success'
                }
            except Exception as e:
                logger.exception('')
                return False, {
                    'started': False,
                    'server_time': now,
                    'time': self.lp.end_time,
                    '#debug1': str(e)
                }
        else:
            # 2.当前课程已经尚未开始,那么创建Token
            lsn_title = u'其它'
            if lessoncontent > 0:
                try:
                    lsn_title = models.SyllabusGradeLessonContent.objects
                    lsn_title = lsn_title.get(id=lessoncontent).title
                except Exception as e:
                    #lsn_title = lessoncontent
                    pass

            info = {
                # fks
                'class': self.c.pk,
                'teacher': self.t.pk,
                'lesson_name': self.l.pk,
                'lesson_period': self.lp.pk,

                # info
                'teacher_name': self.t.name,
                'lesson_name__name': self.l.name,
                'sequence': self.lp.sequence,
                'start_time': self.lp.start_time.strftime('%H:%M:%S'),
                'end_time': self.lp.end_time.strftime('%H:%M:%S'),

                'resource_from': resource_from,
                'resource_type': resource_type,
                'lessoncontent_title': lsn_title,
                'lessoncontent': lessoncontent
            }
            if computerclass:
                # 标记token生成的客户端位置
                info['token_created_at'] = computerclass.uuid
                info['client_in'] = '%s' % computerclass  # 电脑教室
            else:
                info['token_created_at'] = self.c.uuid
                info['client_in'] = '%s年级%s班' % (self.c.grade, self.c)

            # 客户端取消登录的时候需要清除token,
            # 所以这里将token改成班级的uuid+创建地点的uuid
            # 方便在获取的时候定位
            # 但是这样也带来了一个小问题就是每次创建的时候得清除一下前一个token
            # token = '%s-%s' % ('lesson_start', str(now))
            # token = hashlib.sha1(token).hexdigest()
            uuid1 = info['token_created_at'].replace('-', '').lower()
            #uuid2 = info['class'].replace('-', '').lower()
            token = uuid1

            # 如果已经存在该班级的上课信息的token则进行比对
            can_create, early_token = check_token(info)
            if can_create:
                models.Token.objects.filter(
                    token_type='lesson_start',
                    value=token,
                ).delete()
                models.Token.objects.create(
                    token_type='lesson_start',
                    value=token,
                    info=json.dumps(info)
                )
                return False, {
                    'started': False,
                    'server_time': now,
                    'time': self.lp.start_time,
                    'token': token,
                    '#debug2': 'can_create create token'
                }

            # else:
            ret = {'started': False,
                   'server_time': now,
                   'time': self.lp.start_time,
                   'token': None,
                   'early_token': early_token,
                   '#debug3': 'already created login token'}
            return False, ret
