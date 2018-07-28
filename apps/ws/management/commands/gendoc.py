# coding=utf-8
import os
import logging
from django.core.management.base import BaseCommand, CommandParser
from django.conf import settings
from django.apps import apps
from django.utils.translation.trans_real import translation
from prettytable import PrettyTable, ALL, FRAME, NONE

logger = logging.getLogger(__name__)

TRANS = translation(settings.LANGUAGE_CODE)

BASE_DIR = os.path.join(settings.BASE_DIR, 'doc', 'source')
AUTHOR_NAME = os.popen("git config --global --get user.name").read().strip()
AUTHOR_EMAIL = os.popen("git config --global --get user.email").read().strip()

FILE_MAP = {
    'REF': '/rst/api/%(app_name)s/ref.%(out_put)s.rst',
    'RST_I': '/rst/api/%(app_name)s/%(model_name)s.dbinfo.rst',
    'RST_C': '/rst/api/%(app_name)s/%(target)s.create.rst',
    'RST_L': '/rst/api/%(app_name)s/%(target)s.list.rst',
    'RST_R': '/rst/api/%(app_name)s/%(target)s.detail.rst',
    'RST_U': '/rst/api/%(app_name)s/%(target)s.update.rst',
    'RST_A': '/rst/api/%(app_name)s/%(target)s.action.rst',
    'RST_D': '/rst/api/%(app_name)s/%(target)s.delete.rst',

    'JSON_L': '/static/json/api/%(app_name)s/%(target)s.list.json',
    'JSON_C': '/static/json/api/%(app_name)s/%(target)s.create.json',
    'JSON_R': '/static/json/api/%(app_name)s/%(target)s.detail.json',
    'JSON_U': '/static/json/api/%(app_name)s/%(target)s.update.json',
    'JSON_A': '/static/json/api/%(app_name)s/%(target)s.action.json',
}

META_MAP = {
    'I': u"字段说明\n\n--------\n\n",
    'C': u".. literalinclude:: %(JSON_C)s\n    :language: json\n\n后端回应:\n\n.. literalinclude:: %(JSON_R)s\n    :language: json\n",
    'U': u".. literalinclude:: %(JSON_U)s\n    :language: json\n\n后端回应:\n\n.. literalinclude:: %(JSON_R)s\n    :language: json\n",
    'A': u".. include:: %(JSON_A)s\n\n后端回应:\n\n.. literalinclude:: %(JSON_A)s\n    :language: json\n",
    'L': u"后端回应:\n\n.. literalinclude:: %(JSON_L)s\n    :language: json\n",
    'R': u"后端回应:\n\n.. literalinclude:: %(JSON_R)s\n    :language: json\n",
    'D': u"后端回应::\n\n    HTTP 204\n",

    'REF_HEADER': '%(title_wrap)s\n%(title)s\n%(title_wrap)s\n\n%(sign_info)s',

    'REQ_C': u"新建%(target_trans)s\n----%(app_trans_len)s\n\n前端请求: ``%(post)s %(url_prefix)s/%(target)s/``\n\n",
    'REQ_L': u"%(target_trans)s列表\n----%(app_trans_len)s\n\n前端请求: ``%(get)s %(url_prefix)s/%(target)s/``\n\n",
    'REQ_R': u"%(target_trans)s详情\n----%(app_trans_len)s\n\n前端请求: ``%(get)s %(url_prefix)s/%(target)s/{object_id}/``\n\n",
    'REQ_U': u"编辑%(target_trans)s\n----%(app_trans_len)s\n\n前端请求: ``%(put)s %(url_prefix)s/%(target)s/{object_id}/``\n\n",
    'REQ_A': u"操作%(target_trans)s\n----%(app_trans_len)s\n\n前端请求: ``%(put)s %(url_prefix)s/%(target)s/{object_id}/{action}/``\n\n",
    'REQ_D': u"删除%(target_trans)s\n----%(app_trans_len)s\n\n前端请求: ``%(delete)s %(url_prefix)s/%(target)s/{object_id}/``\n\n",

    'RET_I': u".. include:: %(RST_I)s\n\n",
    'RET_C': u".. include:: %(RST_C)s\n\n",
    'RET_U': u".. include:: %(RST_U)s\n\n",
    'RET_A': u".. include:: %(RST_A)s\n\n",
    'RET_L': u".. include:: %(RST_L)s\n\n",
    'RET_R': u".. include:: %(RST_R)s\n\n",
    'RET_D': u".. include:: %(RST_D)s\n\n",
}


def stringify_header(self, options):

    bits = []
    lpad, rpad = self._get_padding_widths(options)
    if options["border"]:
        if options["hrules"] in (ALL, FRAME):
            bits.append(self._hrule)
            bits.append("\n")
        if options["vrules"] in (ALL, FRAME):
            bits.append(options["vertical_char"])
        else:
            bits.append(" ")
    if not self._field_names:
        if options["vrules"] in (ALL, FRAME):
            bits.append(options["vertical_char"])
        else:
            bits.append(" ")
    for field, width, in zip(self._field_names, self._widths):
        if options["fields"] and field not in options["fields"]:
            continue
        if self._header_style == "cap":
            fieldname = field.capitalize()
        elif self._header_style == "title":
            fieldname = field.title()
        elif self._header_style == "upper":
            fieldname = field.upper()
        elif self._header_style == "lower":
            fieldname = field.lower()
        else:
            fieldname = field
        bits.append(" " * lpad + self._justify(fieldname, width, self._align[field]) + " " * rpad)
        if options["border"]:
            if options["vrules"] == ALL:
                bits.append(options["vertical_char"])
            else:
                bits.append(" ")
    if options["border"] and options["vrules"] == FRAME:
        bits.pop()
        bits.append(options["vertical_char"])
    if options["border"] and options["hrules"] != NONE:
        bits.append("\n")
        bits.append(self._hrule.replace('-', '='))
    return "".join(bits)


def get_string(tb, **kwargs):
    options = tb._get_options(kwargs)
    lines = []
    if tb.rowcount == 0 and (not options["print_empty"] or not options["border"]):
        return ""

    rows = tb._get_rows(options)
    formatted_rows = tb._format_rows(rows, options)
    tb._compute_widths(formatted_rows, options)
    tb._hrule = tb._stringify_hrule(options)
    if options["header"]:
        lines.append(tb._stringify_header(options))
    elif options["border"] and options["hrules"] in (ALL, FRAME):
        lines.append(tb._hrule)
    for row in formatted_rows:
        lines.append(tb._stringify_row(row, options))
        if options["border"] and options["hrules"] in (ALL, FRAME):
            lines.append(tb._hrule)
    # if options["border"] and options["hrules"] == FRAME:
    #     lines.append(tb._hrule)
    return tb._unicode("\n").join(lines)


PrettyTable.get_string = get_string
PrettyTable._stringify_header = stringify_header


class Command(BaseCommand):

    def create_parser(self, prog_name, subcommand):
        parser = CommandParser(
            self,
            prog="%s %s" % (os.path.basename(prog_name), subcommand),
            description=u'API文档辅助生成脚本.',
            add_help=False
        )
        parser.set_defaults(**{'verbosity': 1, 'pythonpath': None, 'traceback': None, 'no_color': False, 'settings': None})
        parser._positionals = parser.add_argument_group(u'位置参数')
        parser._optionals = parser.add_argument_group(u'关键字参数')
        parser.add_argument('ref', nargs='?', help=u'引用的对象(eg. oeauth.User, commons.login, users)')
        parser.add_argument('-t', dest='target', help=u'请求的URL的对象(eg. users)')
        parser.add_argument('-p', dest='prefix', help=u'请求的URL的前缀(eg. auth)')
        parser.add_argument('-m', dest='mode', default='ILRCUAD', help=u'包含的模式(Info/Create/List/Get/Update/Delete, eg. iclruad)')
        parser.add_argument('-o', dest='output', help=u'保存文件名(allinone模式)')
        parser.add_argument('-u', '--update', dest='update', action='store_true', default=False, help=u'覆盖已经存在的文件(默认不覆盖)')
        parser.add_argument('-i', '--interactive', dest='interactive', action='store_true', default=False, help=u'覆盖前询问(默认不询问)')
        parser.add_argument('-s', '--sign', dest='sign', action='store_true', default=False, help=u'添加文档签名(默认不添加)')
        parser.add_argument('-a', '--allinone', dest='allinone', action='store_true', default=False, help=u'合并到单个rst文件中(默认不合并)')
        parser.add_argument('-f', '--form-request', dest='form_request', action='store_true', default=False, help=u'表单请求方式(URL请求只包含GET/POST)')
        parser.add_argument('-h', '--help', action='help', help=u'显示帮助信息')
        self.parser = parser
        return parser

    def create_file(self, fp, content='', mode='w'):
        full_path = os.path.abspath(BASE_DIR + fp)
        overwrite = None
        if not os.path.exists(os.path.dirname(full_path)):
            os.makedirs(os.path.dirname(full_path))
        if not os.path.isfile(full_path):
            with open(full_path, mode) as f:
                f.write(content)
            # print(u'创建文件: %s' % full_path)
        elif self.options['update'] or self.options['interactive']:
            if self.options['interactive'] and not self.options['update']:
                overwrite = raw_input(u'文件已经存在: %s\n是否覆盖? [y/N]:' % full_path)
            if overwrite in ('', 'Y', 'y', None) or self.options['update']:
                with open(full_path, mode) as f:
                    f.write(content)
                # print(u'更新文件: %s' % full_path)

    def create_model_table(self):
        dbinfo_content = []
        if 'I' in self.mode and self.model:
            tb_choices = PrettyTable(field_names=[u"键值", u"可选参数值"], align='l')
            field_choices = [f for f in self.model._meta.concrete_fields if f.choices]
            if field_choices:
                for f in field_choices:
                    tb_choices.add_row([f.name, ''.join(['%s:%s; ' % (k, v) for k, v in f.choices])])
                dbinfo_content.append(u'约束项:\n\n' + str(tb_choices) + u'\n\n字段详情:\n')

            tb = PrettyTable(field_names=[u"键值", u"类型", u"非空", u"默认值", u"长度", u"说明"], align='l')
            for field in self.model._meta.concrete_fields:
                verbose_name_trans = TRANS.gettext(field.verbose_name)
                tb.add_row([
                    field.name,
                    '%s%s' % (field.__class__.__name__, field.primary_key and '(PK)' or ''),
                    not (field.blank or field.null) and '√' or '',
                    not callable(field.default) and str(field.default).replace('django.db.models.fields.NOT_PROVIDED', '') or '',
                    getattr(field, 'max_length', '') or '',
                    verbose_name_trans != field.verbose_name and verbose_name_trans or ''
                ])
            dbinfo_content.append(str(tb) + '\n')
        return dbinfo_content

    def handle(self, **options):
        self.options = options
        self.model = None
        try:
            app_name, model_name = options.get('ref').split('.')[-2:]
            self.model = apps.get_model(app_name, model_name)
        except ValueError as e:
            logger.exception(e)
            app_name = options.get('ref')
            model_name = ''
        except LookupError as e:
            logger.exception(e)
        except AttributeError as e:
            return self.parser.print_help()
        self.mode = set(list(options.get('mode', '').upper())) & set(list('ICLRUAD'))
        if not os.path.exists(BASE_DIR):
            os.makedirs(BASE_DIR)

        url_prefix = options.get('prefix') and '/%s' % options['prefix'] or ''
        target = options.get('target') or model_name and model_name.lower()
        if not target:
            raise Exception('target')
        model_name_trans = TRANS.gettext(model_name)
        target_trans = TRANS.gettext(target)

        if target_trans == target and target.lower() == model_name.lower() and model_name_trans != model_name:
            target_trans = model_name_trans
        if model_name_trans == model_name and target.lower() == model_name.lower() and target_trans != target:
            model_name_trans = target_trans

        title = model_name_trans or target_trans or '%s:%s' % (app_name, model_name)
        ctx = {
            'title': title,
            'title_wrap': max([len(title), 4]) * '=',
            'app_name': app_name,
            'model_name': model_name.lower(),
            'model_name_trans': model_name_trans,
            'target_trans': target_trans,
            'app_trans_len': max([len(model_name_trans), len(target_trans), 4]) * '-',
            'url_prefix': url_prefix,
            'target': target,
            'out_put': options['allinone'] and options['output'] or model_name.lower(),
            'sign_info': options.get('sign') and '.. note::\n    | 本文档由 %s 创建\n    | 如果对文档存在疑问, 请当面咨询或者联系 `%s`\n\n\n' % (AUTHOR_NAME, AUTHOR_EMAIL) or '',
            'post': 'POST',
            'get': 'GET',
            'put': options['form_request'] and 'PUT' or 'POST',
            'delete': options['form_request'] and 'DELETE' or 'POST',
        }
        ctx.update({k: v % ctx for k, v in FILE_MAP.items()})
        ctx.update({k: v % ctx for k, v in META_MAP.items()})

        ref_content = []
        dbinfo_content = self.create_model_table()

        if options['allinone']:
            self.create_file(ctx['REF'], ctx['REF_HEADER'])

        for m in list('ILRCUAD'):
            if m in self.mode:
                if m == 'I' and dbinfo_content:
                    if options['allinone']:
                        self.create_file(ctx['REF'], ctx[m], 'a')
                        self.create_file(ctx['REF'], '\n'.join(dbinfo_content) + '\n\n', 'a')
                    else:
                        self.create_file(ctx['RST_%s' % m], '\n'.join(dbinfo_content))

                else:
                    if m not in ('I', 'D'):
                        self.create_file(ctx['JSON_%s' % m])
                    if m != 'I':
                        if options['allinone']:
                            self.create_file(ctx['REF'], ctx['REQ_%s' % m], 'a')
                            self.create_file(ctx['REF'], ctx[m] + '\n\n', 'a')

                        else:
                            # 写入单独rst文件
                            self.create_file(ctx['RST_%s' % m], ctx[m])

                if not options['allinone']:
                    ref_content.append(ctx['REQ_%s' % m])

        if ref_content and not options['allinone']:
            ref_content.insert(0, ctx['REF_HEADER'])
            self.create_file(ctx['REF'], '\n'.join(ref_content))
            print(u'REF: %s' % ctx['REF'])
