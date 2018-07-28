# coding=utf-8
from django.core.management.base import BaseCommand
from ws.dispatchers.sync import rebuild_synclog


class Command(BaseCommand):

    def handle(self, *args, **options):
        rebuild_synclog()
