# coding=utf-8
import os
import mimetypes
from wsgiref.util import FileWrapper
from django.http import Http404, HttpResponse, HttpResponseNotModified
from django.utils.http import http_date
from django.views import static as django_static
from BanBanTong import constants


def serve_software_edufiles(request, *args, **kwargs):
    static_file = kwargs.get('static_file')
    if static_file:
        static_file = static_file.strip('/')
        update_file = os.path.join(constants.EDU_UPDATES_PATH, static_file)

        if os.path.exists(update_file):
            file_stat = os.stat(update_file)

            if not django_static.was_modified_since(request.META.get('HTTP_IF_MODIFIED_SINCE'), file_stat.st_mtime, file_stat.st_size):
                return HttpResponseNotModified()

            mime_type = mimetypes.guess_type(static_file)

            response = HttpResponse(FileWrapper(open(update_file, 'rb')), mime_type[0])
            response["Last-Modified"] = http_date(file_stat.st_mtime)
            return response

    raise Http404()


def serve_software_update(request, *args, **kwargs):
    static_file = kwargs.get('static_file')

    if static_file:
        static_file = static_file.strip('/')
        update_file = os.path.join(constants.UPDATES_PATH, static_file)

        if os.path.exists(update_file):
            file_stat = os.stat(update_file)

            if not django_static.was_modified_since(request.META.get('HTTP_IF_MODIFIED_SINCE'), file_stat.st_mtime, file_stat.st_size):
                return HttpResponseNotModified()

            mime_type = mimetypes.guess_type(static_file)

            response = HttpResponse(FileWrapper(open(update_file, 'rb')), mime_type[0])
            response["Last-Modified"] = http_date(file_stat.st_mtime)
            return response

    raise Http404()
