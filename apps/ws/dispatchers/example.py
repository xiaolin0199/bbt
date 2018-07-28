# coding=utf-8
from ws.dispatchers import DISPATCHERS, DispatcherBase


@DISPATCHERS.register
class ExampleDispather(DispatcherBase):
    name = 'ExampleDispather'
    slug = '/ws/example'
    allowed_server_types = ['school', 'country', 'city', 'province']
    allowed_categories = ['test']

    def dispatch(self, connect, CONNECTS, server, msgdict):
        if 'operation' not in msgdict:
            return {'ret': 1001, 'msg': u'错误的指令格式'}

        dispatch_func = None
        if msgdict['operation'] == 'echo':
            dispatch_func = self.process_echo

        if dispatch_func:
            return dispatch_func(connect, server, msgdict)

    def consume(self, protocol, client, msgdict):
        protocol.factory.log.debug('ExampleDispather.consume:protocol=%s, msgdict=%s', protocol, msgdict)

    def process_echo(self, connect, server, msgdict):
        return {
            'ret': 0,
            'slug': self.slug,
            'operation': msgdict['operation'],
            'data': "Hello Word!"
        }
