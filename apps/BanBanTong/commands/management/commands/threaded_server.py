#!/usr/bin/env python
# coding=utf-8
import cherrypy
import django
from optparse import make_option
import os
import signal
import sys

from django.core.management.base import BaseCommand, CommandError
from django.core.handlers.wsgi import WSGIHandler


def signal_handler(signal, frame):
    print 'Stopping http server!'
    cherrypy.engine.exit()
    print 'Quiting http server!'
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
os.environ['DJANGO_SETTINGS_MODULE'] = 'BanBanTong.settings'


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--noreload', action='store_false', dest='use_reloader', default=True,
                    help='Tells Django to NOT use the auto-reloader.'),
        make_option('--thread_pool_size', default=30,
                    help='Size of CherryPY thread pool.'),
    )
    help = "Starts a lightweight Web server for development."
    args = '[optional port number, or address:port]'

    # Validation is called explicitly each time the server is reloaded.
    requires_model_validation = False

    def handle(self, address_and_port='', *args, **options):
        if args:
            raise CommandError('Usage is threaded_server %s' % self.args)

        if not address_and_port:
            address = '0.0.0.0'
            port = '8000'

        else:
            try:
                address, port = address_and_port.split(':')
            except ValueError:
                address, port = '', address_and_port

        if not address:
            address = '0.0.0.0'

        if not port.isdigit():
            raise CommandError("%r is not a valid port number." % port)

        use_reloader = options.get('use_reloader', True)
        shutdown_message = options.get('shutdown_message', '')
        quit_command = (sys.platform == 'win32') and 'CTRL-BREAK' or 'CONTROL-C'

        def inner_run():
            from django.conf import settings
            from django.utils import translation
            print "\nValidating models..."
            self.validate(display_num_errors=True)

            print "\nDjango version %s, using settings %r" % (django.get_version(), settings.SETTINGS_MODULE)
            print "Development server is running at http://%s:%s/" % (address, port)
            print "Quit the server with %s." % quit_command

            # django.core.management.base forces the locale to en-us. We should
            # set it up correctly for the first request (particularly important
            # in the "--noreload" case).
            # print settings.LANGUAGE_CODE
            translation.activate(settings.LANGUAGE_CODE)

            try:
                cherrypy.config.update({
                    'server.socket_host': address,
                    'server.socket_port': int(port),
                    'engine.autoreload_on': use_reloader,
                    'server.thread_pool': int(options.get('thread_pool_size', 30)),
                    'server.socket_queue_size': 50,
                })

                cherrypy.tree.graft(WSGIHandler(), '/')

                cherrypy.engine.start()
                cherrypy.engine.block()
            finally:
                if shutdown_message:
                    print shutdown_message

                cherrypy.engine.exit()

        inner_run()
