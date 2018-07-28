# coding=utf-8
from django.core.management.commands.runserver import BaseRunserverCommand


class Command(BaseRunserverCommand):

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--config-file', dest='config-file', default=None,
            help='Command line config file.',
        )
