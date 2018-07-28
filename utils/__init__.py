# coding=utf-8


def _patch_request_query_dict():
    # 将request.GET, request.POST 和 request.body对象序列化后置于request.QueryDict中
    import json
    from django.http.request import HttpRequest

    def get_query_dict(request):
        data = {}
        for key in request.GET.keys():
            data[key] = request.GET.getlist(key)
        for key in request.POST.keys():
            data[key] = request.POST.getlist(key)
        for key in data.keys():
            if data[key] is []:
                data[key] = ''
            elif isinstance(data[key], list) and len(data[key]) == 1:
                data[key] = data[key][0]
        try:
            body_data = json.loads(request.body)
            if not isinstance(body_data, dict):
                body_data = {'#body': body_data}
            data.update(body_data)
        except:
            pass
        return data
    HttpRequest.QueryDict = property(get_query_dict)
    HttpRequest.REQUEST = property(get_query_dict)


def _patch_models_to_dict():
    """
    Add a `to_dict` method into every Model
    that inherit from `models.Model`
    """
    from django.utils.translation import ugettext_lazy as _
    from itertools import chain
    from django.db import models

    # django.forms.models.model_to_dict
    def model_to_dict(instance, fields=None, exclude=None, translate=None):
        # from django.contrib.contenttypes import fields as generic
        opts = instance._meta
        data = {}
        # for f in chain(opts.concrete_fields, opts.private_fields, opts.many_to_many):
        for f in chain(opts.concrete_fields, opts.private_fields):
            # if not getattr(f, 'editable', False):
            #     continue
            # if isinstance(f, generic.GenericForeignKey):
            #     continue
            if fields and f.name not in fields:
                continue
            if exclude and f.name in exclude:
                continue
            data[f.name] = f.value_from_object(instance)

        assert translate is None or isinstance(translate, dict), _(
            'Bad argument type `translate`(%(translate)s), which should be a dict.' % {
                'translate': translate
            })
        if translate:
            for k, v in translate.items():
                if k not in fields or k not in data:
                    continue
                data[v] = data.pop(k)
        return data

    def to_dict(instance, *args, **kw):
        return models.Model._to_dict(instance, *args, **kw)

    models.Model._to_dict = model_to_dict
    models.Model.to_dict = to_dict


def _patch_model_field_neq():
    from django.db.models import Lookup
    from django.db.models.fields import Field

    @Field.register_lookup
    class NotEqual(Lookup):
        lookup_name = 'neq'

        def as_sql(self, compiler, connection):
            lhs, lhs_params = self.process_lhs(compiler, connection)
            rhs, rhs_params = self.process_rhs(compiler, connection)
            params = lhs_params + rhs_params
            return '%s <> %s' % (lhs, rhs), params


def _patch_forms_field():
    # 自定义form错误信息
    from django.forms import Field
    max_length_msg = u'该字段超过%(limit_value)d字符（已输入%(show_value)d字符）'
    min_length_msg = u'该字段不足%(limit_value)d字符（已输入%(show_value)d字符）'
    custom_error_messages = {
        'invalid': u'无效的输入值',
        'invalid_choice': u'错误的输入值，%(value)s不在选项内',
        'max_length': max_length_msg,
        'min_length': min_length_msg,
        'max_value': u'该字段不能大于%(limit_value)s',
        'min_value': u'该字段不能小于%(limit_value)s',
        'required': u'该字段为必填项',
    }
    Field.default_error_messages.update(custom_error_messages)


def _patch_pymysql_as_mysqldb():
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        pass


def patch_technical_500_response(DEBUG=True):
    from django.views import debug

    def technical_500_response(request, exc_type, exc_value, tb, status_code=500):
        """
        Create a technical server error response. The last three arguments are
        the values returned from sys.exc_info() and friends.
        """
        reporter = debug.ExceptionReporter(request, exc_type, exc_value, tb)
        html = reporter.get_traceback_html()
        return debug.HttpResponse(html, status=status_code, content_type='text/html')

        # if request.is_ajax():
        #     text = reporter.get_traceback_text()
        #     return HttpResponse(text, status=status_code, content_type='text/plain')
        # else:
        #     html = reporter.get_traceback_html()
        #     return HttpResponse(html, status=status_code, content_type='text/html')

    if DEBUG:
        debug.technical_500_response = technical_500_response


def monkey_patch():
    _patch_pymysql_as_mysqldb()
    _patch_models_to_dict()
    # _patch_auto_gen_field()
    _patch_request_query_dict()
    _patch_model_field_neq()
    _patch_forms_field()


def add_apps_into_sys_path(base_dir):
    """Add apps into sys.path"""
    import os
    import sys
    apps_dir = os.path.join(base_dir, 'apps')
    if not apps_dir in sys.path:
        sys.path.insert(1, apps_dir)


def setup_logger(installed_apps, logging, log_path, debug):
    import os
    FILTERS = {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    }
    if not logging.has_key('filters'):
        logging['filters'] = {}
    logging['filters'].update(FILTERS)

    FORMATTERS = {
        'file': {
            'format': '%(asctime)s %(levelname)-8s@'
                      '%(name)s.%(funcName)s:%(lineno)-4d'
                      '%(message)s'
        },
        'console': {
            '()': 'utils.logger.ColorFormatter',
            'format': '%(asctime)s %(levelname)-8s@%(name)s.%(funcName)s:%(lineno)-4d\n'
                      '%(message)s'
        }
    }

    logging['formatters'].update(FORMATTERS)

    HANDLERS = {level: {
        'level': level.upper(),
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': os.path.join(log_path, '%s.log' % level),
        'maxBytes': 5242880,
        'backupCount': 5,
        'formatter': 'file',
    } for level in ['debug', 'info', 'warning', 'error']}

    HANDLERS.update({
        'console': {
            'level': debug and 'DEBUG' or 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        }
    })
    logging['handlers'].update(HANDLERS)

    DEFAULT_APP_HANDER = {
        'handlers': ['debug', 'warning', 'error', 'console'],
        'level': debug and 'DEBUG' or 'WARNING',
        'propagate': False,
    }
    LOGGERS = {}
    for app in installed_apps:
        if app.startswith('django'):
            continue
        key = app.split('.')[0]
        if key:
            LOGGERS[key] = DEFAULT_APP_HANDER
    logging['loggers'].update(LOGGERS)
