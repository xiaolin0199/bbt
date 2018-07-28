#coding=utf-8
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import doctest

from BanBanTong.db import models


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(models))

    return tests
