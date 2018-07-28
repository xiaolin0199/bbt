# coding=utf-8
import logging
from django.core.management.color import color_style


class RequireLevelMachedFilter(logging.Filter):

    def filter(self, record):
        return record.levelname == self.require_level


class ColorFormatter(logging.StreamHandler):

    def __init__(self, *args, **kwargs):
        """
        style 中的默认方法:
        ERROR
        ERROR_OUTPUT
        HTTP_BAD_REQUEST
        HTTP_INFO
        HTTP_NOT_FOUND
        HTTP_NOT_MODIFIED
        HTTP_REDIRECT
        HTTP_SERVER_ERROR
        HTTP_SUCCESS
        MIGRATE_HEADING
        MIGRATE_LABEL
        NOTICE
        SQL_COLTYPE
        SQL_FIELD
        SQL_KEYWORD
        SQL_TABLE
        SUCCESS
        WARNING
        """
        self.style = color_style()
        setattr(self.style, 'DEBUG', self.style.SUCCESS)
        setattr(self.style, 'INFO', self.style.HTTP_INFO)
        setattr(self.style, 'MESSAGE', self.style.HTTP_NOT_MODIFIED)
        super(ColorFormatter, self).__init__(*args, **kwargs)

    def emit(self, record):
        colorize = getattr(self.style, record.levelname, None)
        if colorize:
            record.levelname = colorize(record.levelname)
        record.msg = self.style.MESSAGE(record.msg)
        return super(ColorFormatter, self).emit(record)


if __name__ == '__main__':
    import platform
    if platform.system() == 'Windows':
        import colorama
        from django.core.management import color
        colorama.init()
        color.supports_color = lambda: True

    style = color_style()
    for func in dir(style):
        if func.startswith('__'):
            continue
        print getattr(style, func)(func)
