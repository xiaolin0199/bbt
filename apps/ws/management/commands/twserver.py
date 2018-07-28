# coding=utf-8
from django.core.management.base import BaseCommand
import ws.networking


class Command(BaseCommand):

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--config-file', dest='config-file', default=None,
            help='Command line config file.',
        )

    def handle(self, *args, **options):
        ws.networking.start_server()
