# coding=utf-8
import json
import logging
import traceback
from django.http.response import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from utils.http import JsonResponse, JSONEncoder

logger = logging.getLogger(__name__)


class JsonResponseMiddleware(MiddlewareMixin):

    def process_response(self, request, response):

        if isinstance(response, dict):
            try:
                data = json.dumps(response, cls=JSONEncoder)
            except Exception as e:
                logger.exception('JSONEncoder:%s' % str(e))
                response = JsonResponse({'msg': str(e), 'errors': traceback.format_exc()}, status=500)

            else:
                if 'callback' in request.GET or 'callback' in request.POST:
                    data = '%s(%s);' % (request.GET.get('callback', request.POST.get('callback')), data)
                response = HttpResponse(data, 'text/javascript')

        return response
