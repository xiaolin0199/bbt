# coding=utf-8
import json
import uuid
import logging
import datetime
import traceback
# from decimal import Decimal
from django import http
from django.db.models.query import QuerySet
from django.db.models.manager import BaseManager
from django.utils.timezone import template_localtime
from django.utils.encoding import force_text
# from django.utils.functional import Promise
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings

logger = logging.getLogger(__name__)


class JSONEncoder(DjangoJSONEncoder):
    """
    DjangoJSONEncoder: datetime date time Decimal UUID Promise
    """

    def default(self, o):
        # See "Date Time String Format" in the ECMA-262 specification.
        if isinstance(o, datetime.datetime):
            t = template_localtime(o, settings.USE_TZ)
            r = t.strftime('%Y-%m-%d %H:%M:%S')
            return r

        elif hasattr(o, 'to_dict'):
            return o.to_dict()

        elif isinstance(o, QuerySet):
            return list(o)

        elif isinstance(o, uuid.UUID):
            return o.get_hex()

        elif isinstance(o, BaseManager):
            return list(o.all())

        else:
            try:
                return super(JSONEncoder, self).default(o)
            except Exception as e:
                logger.warning(
                    'JSONEncoder Warn: %s\n'
                    'format_exc=%s\n'
                    'type:%s\n'
                    'repr:%s',
                    e, traceback.format_exc(), type(o), repr(o)
                )
                return force_text(o)


class JsonResponse(http.HttpResponse):

    def __init__(self, data=None, encoder=JSONEncoder, safe=True, json_dumps_params=None, **kwargs):
        status = kwargs.get('status', 200)
        self.raw_data = data
        if not data:
            status = 204
            content = b''
        else:
            try:
                content = json.dumps(data, sort_keys=settings.DEBUG, cls=encoder)
            except Exception as e:
                logger.exception('JsonDumpError:%s, data=%s', e, data)
                content = json.dumps({'msg': traceback.format_exc()})
                status = 500

        kwargs.update({
            'content_type': kwargs.get('content_type', 'application/json'),
            'status': status
        })
        super(JsonResponse, self).__init__(
            content=content,
            **kwargs
        )
