#!/usr/bin/env python
# coding=utf-8
from django.http.response import HttpResponse
from django.template import loader


def index(request):
    template = loader.get_template('resource_collect.html')
    return HttpResponse(template.render({}))
