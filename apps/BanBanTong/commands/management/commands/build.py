# coding=utf-8
import os
import shutil
import tarfile
import compileall
import logging
from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser

logger = logging.getLogger('cmd')

BASE_DIR = os.path.abspath(settings.BASE_DIR)
BRANCH = os.popen("git symbolic-ref --short HEAD").read().strip()
LAST_COMMIT = os.popen("git rev-parse HEAD").read().strip()
LAST_TAG_COMMIT = os.popen("git rev-list --tags --max-count=1").read().strip()
LAST_TAG = os.popen("git describe --tags %s" % LAST_TAG_COMMIT).read().strip()

FEATURE_MAP = {
    'master': 0,
    'v5': 0,
    'bbt-changsha': 1,
    'bbt-tianjin': 2,
    'bbt-jinzhou': 3
}
logger.debug('\nBRANCH:%s\nLAST_COMMIT:%s\nLAST_TAG_COMMIT:%s', BRANCH, LAST_COMMIT, LAST_TAG_COMMIT)


if LAST_COMMIT != LAST_TAG_COMMIT:
    BUILD_DIR = os.path.abspath(os.path.join(BASE_DIR, 'build', LAST_TAG))
    BUILD_TARBALL = os.path.abspath(os.path.join(BASE_DIR, 'build', LAST_TAG + '.tar.gz'))

else:
    try:
        feature = FEATURE_MAP.get(BRANCH)
        tag, _, svn = LAST_TAG.rsplit('.', 2)
        if feature is not None:
            LAST_TAG = '%s.%s.%s' % (tag, feature, int(svn) + 1)
        else:
            last_tag = u'%s.%s.%s' % (tag, 0, int(svn) + 1)
            LAST_TAG = raw_input(u'输入当前版本:')
            LAST_TAG = LAST_TAG or last_tag
    except:
        LAST_TAG = raw_input(u'输入当前版本:')

    BUILD_DIR = os.path.abspath(os.path.join(BASE_DIR, 'build', '%s.%s' % (LAST_TAG, LAST_COMMIT[:9])))
    BUILD_TARBALL = os.path.abspath(os.path.join(BASE_DIR, 'build', '%s.%s' % (LAST_TAG, LAST_COMMIT[:9]) + '.tar.gz'))

PY_MODULES = (
    (BASE_DIR, 'apps', 'activation'),
    (BASE_DIR, 'apps', 'BanBanTong'),
    (BASE_DIR, 'apps', 'edu_point'),
    (BASE_DIR, 'apps', 'machine_time_used'),
    (BASE_DIR, 'apps', 'cameraroom'),
    (BASE_DIR, 'apps', 'ws'),
    (BASE_DIR, 'conf'),
    (BASE_DIR, 'utils'),
    (BASE_DIR, 'manage.py'),
    (BASE_DIR, 'wsgi.py'),
    (BASE_DIR, 'settings.py'),
    (BASE_DIR, 'urls.py'),
)

LIB_SOURCES = (
    (BASE_DIR, 'locale'),
    (BASE_DIR, 'files'),
    (BASE_DIR, 'requirements.txt'),
    ('banbantong-apache-win', 'Apache24'),
    ('banbantong-python', 'Python27'),
)


def ignore_pyc(currdir, files):
    ret = []
    for i in files:
        f = os.path.join(currdir, i)
        if os.path.isfile(f) and f.endswith('.pyc'):
            ret.append(i)
    return ret


def delete_py_log(path):
    for dirpath, dirnames, filenames in os.walk(path):
        if dirpath.endswith('migrations'):
            # migrations下面需要保留.py文件
            for i in filenames:
                if i.endswith('.pyc'):
                    f = os.path.join(dirpath, i)
                    os.remove(f)
        elif dirpath.endswith('LC_MESSAGES'):
            # 删除po源文件
            for i in filenames:
                if i.endswith('.po'):
                    f = os.path.join(dirpath, i)
                    os.remove(f)
        else:
            for i in filenames:
                if i.endswith('.py') or i.endswith('.log'):
                    f = os.path.join(dirpath, i)
                    if os.path.isfile(f):
                        # wsgi.py不能删, Apache mod_wsgi使用
                        if f.endswith('wsgi.py'):
                            continue
                        os.remove(f)


def copytree_and_compile(path, compile_file=True):
    basename = os.path.basename(path)
    # basename = path.split(BASE_DIR)[-1][1:]
    src = os.path.abspath(path)
    dst = os.path.join(BUILD_DIR, basename)
    if not os.path.exists(src):
        return None, basename

    elif os.path.isfile(src):
        shutil.copyfile(src, dst)
        if basename in ('settings.py', 'conf.py', 'urls.py', 'manage.py'):
            compileall.compile_file(dst, quiet=True, ddir='.')
            os.remove(dst)
            basename = basename + 'c'
            dst = os.path.join(BUILD_DIR, basename)
        return dst, basename
    else:
        logger.debug('compile dir: %s', dst)
        shutil.copytree(src, dst, ignore=ignore_pyc)
        if compile_file:
            compileall.compile_dir(dst, quiet=True, ddir='.')
            delete_py_log(dst)
        return dst, basename


def create_settings_ini(build_dir):
    settings_ini = os.path.join(build_dir, 'settings.ini')
    with open(settings_ini, 'w') as f:
        f.write('[DEFAULT]\n')
        f.write('debug=false\n')
        f.write('\n[db]\n')
        # f.write('engine=django_mysqlpool.backends.mysqlpool\n')
        f.write('host=127.0.0.1\n')
        f.write('port=3100\n')
        f.write('name=banbantong\n')
        f.write('user=root\n')
        f.write('password=oseasydads_db\n')
        # f.write('\n[cache]\n')
        # f.write('backend=django.core.cache.backends.memcached.MemcachedCache\n')
        # f.write('location=127.0.0.1:11211\n')
        # f.write('options=\n')
    return settings_ini


def create_version_ini(build_dir):
    version_ini = os.path.join(build_dir, 'version.ini')
    tag, svn = LAST_TAG.rsplit('.', 1)
    with open(version_ini, 'w') as f:
        f.write('[Version]\n')
        f.write('Version number = V%s\n' % tag)
        f.write('svn=%s' % svn)
    return version_ini


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
        parser.add_argument('--no-static', dest='no_static_files', action='store_true', default=False, help=u'打包静态文件(默认添加)')
        parser.add_argument('--linux', dest='linux', action='store_true', default=False, help=u'打包Linux安装包')
        parser.add_argument('--debug', dest='debug', action='store_true', default=False, help=u'调试模式')
        parser.add_argument('-h', '--help', action='help', help=u'显示帮助信息')
        self.parser = parser
        return parser

    def handle(self, *args, **options):
        settings.DEBUG = options['debug']
        global BASE_DIR, BRANCH, LAST_COMMIT, LAST_TAG_COMMIT, LAST_TAG, FEATURE_MAP, BUILD_DIR, BUILD_TARBALL, LAST_TAG

        if options['linux']:
            BUILD_TARBALL = os.path.abspath(os.path.join(BASE_DIR, 'build', '%s-%s.%s' % (BRANCH, LAST_TAG, LAST_COMMIT[:9]) + '.tar.gz'))
        logger.debug('\n当前分支: %s\n当前版本: %s\n输出路径: %s', BRANCH, LAST_TAG, BUILD_TARBALL)

        shutil.rmtree(BUILD_DIR, True)
        if os.path.exists(BUILD_TARBALL):
            os.remove(BUILD_TARBALL)
        os.makedirs(BUILD_DIR)
        tar = tarfile.open(BUILD_TARBALL, 'w:gz')
        for args in PY_MODULES:
            path, basename = copytree_and_compile(os.path.join(*args))
            if path:
                tar.add(path, arcname=basename)
        if not options['no_static_files']:
            for args in LIB_SOURCES:
                path, basename = copytree_and_compile(os.path.join(*args), compile_file=False)
                if path:
                    tar.add(path, arcname=basename)

        settings_ini = create_settings_ini(BUILD_DIR)
        tar.add(settings_ini, arcname='settings.ini')
        version_ini = create_version_ini(BUILD_DIR)
        tar.add(version_ini, arcname='version.ini')
        # shutil.rmtree(BUILD_DIR, True)
        tar.close()
        if options['linux']:
            shutil.copyfile(os.path.join(BASE_DIR, 'scripts', 'setup.sh'), os.path.join(os.path.dirname(BUILD_TARBALL), 'setup.sh'))
            shutil.copyfile(os.path.join(BASE_DIR, 'apps/BanBanTong/db/fixtures', 'GroupTB.sql.gz'), os.path.join(os.path.dirname(BUILD_TARBALL), 'GroupTB.sql.gz'))
            with open(os.path.join(os.path.dirname(BUILD_TARBALL), 'setuprc'), 'w') as f:
                f.write('RELEASE=%s' % BRANCH)
