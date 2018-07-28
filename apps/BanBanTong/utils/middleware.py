#!/usr/bin/env python
# coding=utf-8
import json
from django.core.cache import cache
from django.http.response import HttpResponse
from BanBanTong.utils import create_failure_dict
from BanBanTong.utils import datetimeutil
from BanBanTong.utils import RevisedDjangoJSONEncoder
from django.utils.deprecation import MiddlewareMixin


class JsonResponseMiddleware(MiddlewareMixin):

    def process_response(self, request, response):
        if isinstance(response, dict):
            # MH 格式化response,方便开发过程中查看返回的json数据
            # 去掉返回的json中的空格,减少数据量
            data = json.dumps(response, indent=4, separators=(',', ': '), cls=RevisedDjangoJSONEncoder)
            # data = json.dumps(response, cls=RevisedDjangoJSONEncoder)
            if 'callback' in request.GET:
                data = '%s(%s);' % (request.GET['callback'], data)
                return HttpResponse(data, "text/javascript")
            # return HttpResponse(data, "application/json")
            # IE会对json response弹出下载文件框，所以不使用application/json
            return HttpResponse(data)
        else:
            return response


class MaintenanceModeMiddleware(MiddlewareMixin):
    '''如果服务器处于维护状态，不响应Web请求'''

    def process_request(self, request):
        if cache.get('MaintenanceMode') == 'True':
            return create_failure_dict(msg='系统处于维护状态，暂停服务，稍后自动恢复')


class ValidateDateRangeMiddleware(MiddlewareMixin):
    '''处理Request中的时间范围， '''

    # 需要检测的
    _check_path_filter = (
        '/activity/',  # 使用记录
        '/statistic/',  # 统计分析

        '/terminal/time-used/',  # 终端开机使用日志

        '/edu-unit/statistic/',  # 教学点教室使用统计、卫星资源接收、教学点终端开机统计
        '/edu-unit/resource-store/',  # 卫星资源接收日志
        '/edu-unit/terminal-boot/',  # 教学点终端开机日志
        '/edu-unit/terminal-use/',  # 教学点终端使用日志
    )
    # 需要排除的
    _check_path_exclude = (
        '/activity/desktop-preview/list-everyday/',  # 桌面使用日志,时间线
        '/edu-unit/screenshot/node-timeline/',  # 教学的桌面使用日志,时间线
    )

    def process_request(self, request):
        return
        if request.method != 'GET':
            return
        if 'start_date' not in request.GET and 'end_date' not in request.GET:
            return

        path = request.path
        for prefix in self._check_path_exclude:
            if path.startswith(prefix):
                del path
                return

        for prefix in self._check_path_filter:
            if path.startswith(prefix):
                ret = datetimeutil.check_date_range(request)
                if isinstance(ret, (str, unicode)):
                    del path
                    return create_failure_dict(msg=ret)

        else:
            del path
            return
