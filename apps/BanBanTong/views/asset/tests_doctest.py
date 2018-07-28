# coding=utf-8
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

# from django.test import TestCase
# from django.test.client import Client

# import unittest
import doctest


# views for doctest
# 该模块下的所有views函数
list_of_doctests = [
    'asset_type',
    'asset',
    'asset_log',
    'asset_repair'
]

# class SimpleTest(TestCase):
#    def test_basic_addition(self):
#        """
#        Tests that 1 + 1 always equals 2.
#        """
#        self.assertEqual(1 + 1, 2)


def load_tests(loader, tests, ignore):

    # 检测views函数的doctests
    for t in list_of_doctests:
        tests.addTests(doctest.DocTestSuite(
            __import__(t, globals(), locals(), fromlist=["*"])
        ))
    return tests
