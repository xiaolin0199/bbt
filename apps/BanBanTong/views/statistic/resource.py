# coding=utf-8
'''统计分析->授课资源使用统计'''
import cPickle as pickle

from django.core.cache import cache
from django.db.models import Count
from django.db.models import Q
from BanBanTong.db.models import Setting, Group, Grade
from BanBanTong.db.models import TeacherLoginLog, Term
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import create_success_dict
from BanBanTong.utils.get_cache_timeout import get_timeout


def _get_top(logs, node_type):
    '''
        选择节点的目标子单位前10数据
    '''
    if node_type == 'grade':
        logs = logs.values('class_name').annotate(count=Count('pk', distinct=True))
        suffix = u'班'
    elif node_type == 'school':
        logs = logs.values('grade_name').annotate(count=Count('pk', distinct=True))
        suffix = u'年级'
    elif node_type == 'town':
        logs = logs.values('school_name').annotate(count=Count('pk', distinct=True))
        suffix = u''
    elif node_type == 'country':
        logs = logs.values('town_name').annotate(count=Count('pk', distinct=True))
        suffix = u''
    elif node_type == 'city':
        logs = logs.values('country_name').annotate(count=Count('pk', distinct=True))
        suffix = u''
    elif node_type == 'province':
        logs = logs.values('city_name').annotate(count=Count('pk', distinct=True))
        suffix = u''
    else:
        return []

    # 按从大到小的count排序
    logs = sorted(logs, lambda x, y: cmp(x['count'], y['count']), reverse=True)
    logs = logs[:10]

    ret = []
    for log in logs:
        d = {}
        for k, v in log.iteritems():
            if k in ['class_name', 'grade_name', 'school_name', 'town_name', 'country_name', 'city_name']:
                d['name'] = v + suffix
            else:
                d[k] = v
        ret.append(d)

    return ret


def _get_from_top(all_resource_from):
    records = []
    # 详细
    details = all_resource_from.values('resource_from').annotate(count=Count('pk', distinct=True))
    # 按最多排序
    details = sorted(details, key=lambda x: (x['count']), reverse=True)

    # 每个种类的详细情况
    if len(details) <= 9:
        records = details
    else:
        records = details[:9]
        # 余下的全部整个'其他'
        other_from_count = reduce(lambda x, y: x + y, map(lambda x: x['count'], details[9:]))

        records.append({'resource_from': u'其他', 'count': other_from_count})

    return records


def _get_type_top(all_resource_type):
    records = []
    # 详细
    details = all_resource_type.values('resource_type').annotate(count=Count('pk', distinct=True))
    # 按最多排序
    details = sorted(details, key=lambda x: (x['count']), reverse=True)

    # 每个种类的详细情况
    if len(details) <= 9:
        records = details
    else:
        records = details[:9]
        # 余下的全部整个'其他'
        other_type_count = reduce(lambda x, y: x + y, map(lambda x: x['count'], details[9:]))

        records.append({'resource_type': u'其他', 'count': other_type_count})

    return records


def _match(logs, node_type):
    '''
        按要求格式化数据
    '''

    data = {
        'resource_from': {'sum': 0, 'records': []},
        'resource_type': {'sum': 0, 'records': []},
        'top': []
    }

    # 二个饼图数据
    #all_resource_from = logs.filter(resource_from__isnull=False).distinct()
    all_resource_from = logs.exclude(Q(resource_from__isnull=True) | Q(resource_from='')).distinct()
    all_resource_type = logs.exclude(Q(resource_type__isnull=True) | Q(resource_type='')).distinct()

    data['resource_from']['sum'] = all_resource_from.count()
    data['resource_type']['sum'] = all_resource_type.count()
    # 上方饼图只取前十，十之后用'其他'代替
    data['resource_from']['records'] = _get_from_top(all_resource_from)
    data['resource_type']['records'] = _get_type_top(all_resource_type)
    # 下方柱图Top10数据
    top_data = _get_top(logs, node_type)
    # 整合输出
    data['top'] = top_data

    return data


def _get_data(node_uuid, node_type, school_year, term_type):
    '''
        从流水log中分析资源
    '''
    #current_term_list = Term.get_current_term_list()

    # 仅获取当前学期流水

    #logs = TeacherLoginLog.objects.filter(term__in=current_term_list)
    logs = TeacherLoginLog.objects.filter(term_school_year=school_year, term_type=term_type)

    if node_type == 'grade':
        logs = logs.filter(grade__uuid=node_uuid)
    elif node_type == 'school':
        logs = logs.filter(school__uuid=node_uuid)
    elif node_type == 'town':
        logs = logs.filter(town__uuid=node_uuid)
    elif node_type == 'country':
        #logs = logs.filter(country__uuid=node_uuid)
        # 如果是查看区县的统计， 不用上面的过滤，可以用一个比较快的索引
        pass
    elif node_type == 'city':
        logs = logs.filter(city__uuid=node_uuid)
    elif node_type == 'province':
        logs = logs.filter(province__uuid=node_uuid)

    data = _match(logs, node_type)

    return data


def resource_global(request):
    '''
        资源使用综合分析
        1. 选择区县，乡镇街道，其结点单位为学校
        2. 选择学校，其结点为年级
        3. 选择年级，其结点为班级
        4. 右侧上左饼图为资源来源的百分比图，右侧上右饼图为资源类型的百分比图
        5. 右侧下方柱状图为TOP10的学校或是年级或是班级的上课次数
    '''
    # TODO 2015-03-23
    # 添加查询条件
    # 查询条件：学年：（当前学年（默认）、动态获取学校所有的学年信息），
    # 学期：（当前学期（默认）、动态获取学校所选学年的所有学期）；
    # 各分类数值统计将按序排列；当统计类型超过10种时，第10种及以上合并为其他；

    # 其他需求(前端修改?)
    # 右侧使用饼状图显示当前学校所查询学期的相关数据：资源来源分类统计，
    # 各分类总数与百分比；资源类型分类统计，各分类总数与百分比；右侧使用柱状图
    # 显示当前学校所查询学期的相关数据：各班级资源使用次数前十名。

    node_uuid = request.GET.get('uuid', '')
    node_type = request.GET.get('type', 'school')
    school_year = request.GET.get('school_year', '')
    term_type = request.GET.get('term_type', '')

    if not school_year and not term_type:
        terms = Term.get_current_term_list()
        if terms:
            school_year = terms[0].school_year
            term_type = terms[0].term_type

    if not node_type:
        node_type = 'school'

    if not node_uuid:
        # 只有type没有uuid，是默认界面的url
        if Setting.getvalue('server_type') != node_type:
            return create_failure_dict(msg=u'错误的node_type %s' % node_type)
        try:
            obj = Group.objects.get(group_type=node_type)
        except:
            return create_failure_dict(msg=u'查找服务器节点时出错')
        node_uuid = obj.uuid
    else:
        # 既有type又有uuid，需要验证数据合法性
        if node_type in ('province', 'city', 'country', 'town', 'school'):
            try:
                obj = Group.objects.get(group_type=node_type, uuid=node_uuid)
            except:
                return create_failure_dict(msg=u'错误的node_type和uuid')
        elif node_type == 'grade':
            try:
                obj = Grade.objects.get(uuid=node_uuid)
            except:
                return create_failure_dict(msg=u'错误的年级uuid')
        else:
            return create_failure_dict(msg=u'错误的node_type')

    k = u'resource-analysis-for-node-%s-%s-%s' % (node_uuid, school_year, term_type)

    v = cache.get(k)
    if v:
        data = pickle.loads(v)
    else:
        data = _get_data(node_uuid, node_type, school_year, term_type)
        cache.set(k, pickle.dumps(data), get_timeout(k, 60 * 10))

    return create_success_dict(data=data)


"""

def resource_query(cond, excludes, current_user):
    school_year = cond.get('school_year')
    term_type = cond.get('term_type')
    start_date = cond.get('start_date')
    end_date = cond.get('end_date')
    country_name = cond.get('country_name')
    town_name = cond.get('town_name')
    school_name = cond.get('school_name')
    grade_name = cond.get('grade_name')
    class_name = cond.get('class_name')
    lesson_name = cond.get('lesson_name')
    resource_from = cond.get('resource_from')
    resource_type = cond.get('resource_type')
    teacher_name = cond.get('teacher_name')
    q = TeacherLoginLog.objects.exclude(**excludes)
    title = ''
    if start_date and end_date:
        s = parse_date(start_date)
        e = parse_date(end_date)
        s = datetime.datetime.combine(s, datetime.time.min)
        e = datetime.datetime.combine(e, datetime.time.max)
        q = q.filter(created_at__range=(s, e))
        title = '%s-%s' % (start_date.replace('-', ''),
                           end_date.replace('-', ''))
    else:
        if school_year:
            q = q.filter(term_school_year=school_year)
            title = school_year
        if term_type:
            q = q.filter(term_type=term_type)
            term = Term.objects.filter(school_year=school_year,
                                              term_type=term_type)
            if term.exists():
                term = term[0]
                title = '%s-%s' % (str(term.start_date).replace('-', ''),
                                   str(term.end_date).replace('-', ''))
    if country_name:
        q = q.filter(country_name=country_name)
    if town_name:
        q = q.filter(town_name=town_name)
    if school_name:
        q = q.filter(school_name=school_name)
    if grade_name:
        q = q.filter(grade_name=grade_name)
    if class_name:
        q = q.filter(class_name=class_name)
    if lesson_name:
        q = q.filter(lesson_name=lesson_name)
    if resource_from:
        q = q.filter(resource_from=resource_from)
    if resource_type:
        q = q.filter(resource_type=resource_type)
    if teacher_name:
        q = q.filter(teacher_name__contains=teacher_name)
    if not is_admin(current_user):
        permitted_groups = current_user.permitted_groups.all()
        uuids = [i.uuid for i in permitted_groups]
        q = q.filter(school__uuid__in=uuids)
    total = q.count()
    return q, total, title


def _result(request, cache_key, fields, excludes):
    page_info = get_page_info(request)

    cache.set(cache_key, json.dumps(request.GET), None)
    q, total, title = resource_query(request.GET, excludes,
                                     request.current_user)
    q = q.values(*fields)
    q = q.annotate(visit_count=Count('pk'))
    paginator = Paginator(q, page_info['page_size'])
    records = list(paginator.page(page_info['page_num']).object_list)
    return create_success_dict(data={
        'page': page_info['page_num'],
        'page_count': paginator.num_pages,
        'page_size': page_info['page_size'],
        'record_count': paginator.count,
        'records': records,
        'total': {
            'visit_count': total
        }
    })


def _export(cache_key, current_user, query_fields,
            excludes, excel_header, dict_keys):
    c = cache.get(cache_key)
    if not c:
        return create_failure_dict(msg='查询超时无法导出，请重新查询！')
    cond = json.loads(c)
    q, total, title = resource_query(cond, excludes, current_user)
    q = q.values(*query_fields)
    q = q.annotate(visit_count=Count('pk'))
    xls = xlwt.Workbook(encoding='utf8')
    if not title:
        title = u'授课资源使用统计'
    sheet = xls.add_sheet(title)
    for i in range(len(excel_header)):
        sheet.write(0, i, excel_header[i])
    row = 1
    for record in q:
        for i in range(len(dict_keys)):
            sheet.write(row, i, record[dict_keys[i]])
        try:
            percent = record['visit_count'] * 100.0 / total
        except:
            percent = 0.0
        percent = '%0.2f%%' % percent
        sheet.write(row, len(dict_keys), percent)
        row += 1
    sheet.write(row, len(dict_keys) - 1, '合计访问次数')
    sheet.write(row, len(dict_keys), total)
    cached_id = str(uuid.uuid1())
    tmp_file = os.path.join(constants.CACHE_TMP_ROOT, cached_id)
    xls.save(tmp_file)
    filename = u'授课资源使用统计_%s.xls' % title
    return create_success_dict(url=reverse('base:xls_download',
                                           kwargs={'cached_id': cached_id,
                                                   'name': filename}))


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('resource_statistic')
def lesson(request):
    cache_key = 'resource-lesson'
    fields = ('country_name', 'town_name', 'school_name', 'lesson_name')
    excludes = {'resource_from': '', 'resource_type': ''}
    ret = _result(request, cache_key, fields, excludes)
    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def lesson_export(request, *args, **kwargs):
    cache_key = 'resource-lesson'
    server_type = Setting.getvalue('server_type')
    g = Group.objects.get(group_type=server_type)
    if g.group_type != 'school':
        fields = ('country_name', 'town_name', 'school_name', 'lesson_name')
        excludes = {'resource_from': '', 'resource_type': ''}
        excel_header = ['区县市 ', '街道乡镇', '学校', '课程',
                        '访问次数', '访问次数占比（%）']
        dict_keys = ('country_name', 'town_name', 'school_name', 'lesson_name',
                     'visit_count')
    else:
        fields = ('town_name', 'school_name', 'lesson_name')
        excludes = {'country_name': '', 'resource_from': '', 'resource_type': ''}
        excel_header = ['街道乡镇', '学校', '课程',
                        '访问次数', '访问次数占比（%）']
        dict_keys = ('town_name', 'school_name', 'lesson_name', 'visit_count')
    fields = ('town_name', 'school_name', 'lesson_name')
    excludes = {'country_name': '', 'resource_from': '', 'resource_type': ''}
    excel_header = ['街道乡镇', '学校', '课程', '访问次数', '访问次数占比（%）']
    dict_keys = ('town_name', 'school_name', 'lesson_name', 'visit_count')
    ret = _export(cache_key, request.current_user, fields,
                  excludes, excel_header, dict_keys)
    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('resource_statistic')
def resource_from(request):
    cache_key = 'resource-from'
    server_type = Setting.getvalue('server_type')
    if server_type == 'school':
        fields = ('town_name', 'school_name', 'grade_name',
                  'class_name', 'resource_from')
    elif server_type == 'country':
        fields = ('town_name', 'school_name', 'resource_from')
    elif server_type == 'city':
        fields = ('country_name', 'town_name', 'school_name',
                  'resource_from')
    else:
        return create_failure_dict(msg='不支持这一级别的服务器')
    excludes = {'resource_from': ''}
    ret = _result(request, cache_key, fields, excludes)
    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def resource_from_export(request, *args, **kwargs):
    cache_key = 'resource-from'
    server_type = Setting.getvalue('server_type')
    if server_type == 'school':
        fields = ('town_name', 'school_name', 'grade_name',
                  'class_name', 'resource_from')
        excel_header = ['街道乡镇', '学校', '年级', '班级',
                        '资源来源', '访问次数', '访问次数占比（%）']
        dict_keys = ('town_name', 'school_name', 'grade_name',
                     'class_name', 'resource_from', 'visit_count')
    elif server_type == 'country':
        fields = ('town_name', 'school_name', 'resource_from')
        excel_header = ['街道乡镇', '学校', '资源来源',
                        '访问次数', '访问次数占比（%）']
        dict_keys = ('town_name', 'school_name', 'resource_from',
                     'visit_count')
    elif server_type == 'city':
        fields = ('country_name', 'town_name', 'school_name',
                  'resource_from')
        excel_header = ['区县市', '街道乡镇', '学校', '资源来源',
                        '访问次数', '访问次数占比（%）']
        dict_keys = ('country_name', 'town_name', 'school_name',
                     'resource_from', 'visit_count')
    else:
        return create_failure_dict(msg='不支持这一级别的服务器')
    excludes = {'resource_from': ''}
    ret = _export(cache_key, request.current_user, fields,
                  excludes, excel_header, dict_keys)
    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('resource_statistic')
def resource_type(request):
    cache_key = 'resource-type'
    server_type = Setting.getvalue('server_type')
    if server_type == 'school':
        fields = ('town_name', 'school_name', 'grade_name',
                  'class_name', 'resource_type')
    elif server_type == 'country':
        fields = ('town_name', 'school_name', 'resource_type')
    elif server_type == 'city':
        fields = ('country_name', 'town_name', 'school_name',
                  'resource_type')
    else:
        return create_failure_dict(msg='不支持这一级别的服务器')
    excludes = {'resource_type': ''}
    ret = _result(request, cache_key, fields, excludes)
    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def resource_type_export(request, *args, **kwargs):
    cache_key = 'resource-type'
    server_type = Setting.getvalue('server_type')
    if server_type == 'school':
        fields = ('town_name', 'school_name', 'grade_name',
                  'class_name', 'resource_type')
        excel_header = ['街道乡镇', '学校', '年级', '班级',
                        '资源类型', '访问次数', '访问次数占比（%）']
        dict_keys = ('town_name', 'school_name', 'grade_name',
                     'class_name', 'resource_type', 'visit_count')
    elif server_type == 'country':
        fields = ('town_name', 'school_name', 'resource_type')
        excel_header = ['街道乡镇', '学校', '资源类型',
                        '访问次数', '访问次数占比（%）']
        dict_keys = ('town_name', 'school_name', 'resource_type',
                     'visit_count')
    elif server_type == 'city':
        fields = ('country_name', 'town_name', 'school_name',
                  'resource_type')
        excel_header = ['区县市', '街道乡镇', '学校', '资源类型',
                        '访问次数', '访问次数占比（%）']
        dict_keys = ('country_name', 'town_name', 'school_name',
                     'resource_type', 'visit_count')
    else:
        return create_failure_dict(msg='不支持这一级别的服务器')
    excludes = {'resource_type': ''}
    ret = _export(cache_key, request.current_user, fields,
                  excludes, excel_header, dict_keys)
    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('resource_statistic')
def teacher(request):
    cache_key = 'resource-teacher'
    fields = ('town_name', 'school_name', 'teacher_name')
    excludes = {'resource_from': '', 'resource_type': ''}
    ret = _result(request, cache_key, fields, excludes)
    return ret


@decorator.authorized_user_with_redirect
@decorator.authorized_privilege('teacher_lesson_statistic')
def teacher_export(request, *args, **kwargs):
    cache_key = 'resource-teacher'
    fields = ('town_name', 'school_name', 'teacher_name')
    excludes = {'resource_from': '', 'resource_type': ''}
    excel_header = ['街道乡镇', '学校', '教师',
                    '访问次数', '访问次数占比（%）']
    dict_keys = ('town_name', 'school_name', 'teacher_name',
                 'visit_count')
    ret = _export(cache_key, request.current_user, fields,
                  excludes, excel_header, dict_keys)
    return ret
"""
