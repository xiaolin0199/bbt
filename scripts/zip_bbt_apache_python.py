# coding=utf-8
import compileall
import uuid
import os
import shutil
import tarfile


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
PROJECT_NAME = os.path.basename(PROJECT_DIR)
BUILD_DIR = os.path.abspath(os.path.join(PROJECT_DIR, '..', '%s' % str(uuid.uuid1()).split('-')[0]))
VERSION = raw_input('VERSION:')
VERSION = VERSION or PROJECT_NAME


def ignore_pyc(currdir, files):
    if currdir.count(os.sep) <= 5:
        print currdir
    ret = []
    for i in files:
        f = os.path.join(currdir, i)
        if os.path.isfile(f) and f.endswith('.pyc'):
            ret.append(i)
    return ret


def delete_py_log(path):
    for dirpath, dirnames, filenames in os.walk(path):
        if dirpath.endswith(os.path.join('management', 'commands')) or dirpath.endswith('migrations'):
            # management commands和south migrations需要.py文件
            for i in filenames:
                if i.endswith('.pyc') or i.endswith('.log'):
                    f = os.path.join(dirpath, i)
                    os.remove(f)
        else:
            for i in filenames:
                if i.endswith('.py') or i.endswith('.log'):
                    f = os.path.join(dirpath, i)
                    if os.path.isfile(f):
                        if f.endswith('wsgi.py'):  # wsgi.py不能删
                            continue
                        os.remove(f)


def compress_folder(path):
    basename = os.path.basename(path)
    tar = tarfile.open(os.path.join(BUILD_DIR, basename, '.tar.gz'), 'w:gz')
    tar.add(path, arcname=basename)
    tar.close()


def job(path):
    basename = os.path.basename(path)
    basename = path.split(PROJECT_DIR)[-1]
    src = os.path.join(os.curdir, path)
    if os.path.isfile(src):
        print os.path.basename(path)
        # compileall.compile_file(src)
        return src
    if not os.path.isdir(src):
        return
    dst = os.path.join(BUILD_DIR, basename)
    shutil.copytree(src, dst, ignore=ignore_pyc)
    if not basename == 'ipython':
        compileall.compile_dir(dst, quiet=True)
        delete_py_log(dst)
    # compress_folder(dst)
    return dst

path_indludes = (
    (PROJECT_DIR, 'apps', 'activation'),
    (PROJECT_DIR, 'apps', 'BanBanTong'),
    (PROJECT_DIR, 'apps', 'edu_point'),
    (PROJECT_DIR, 'apps', 'machine_time_used'),
    (PROJECT_DIR, 'apps', 'ws'),
    (PROJECT_DIR, 'utils'),
    (PROJECT_DIR, 'files'),
    # (PROJECT_DIR, 'south'),
    ('banbantong-apache-win', 'Apache24'),
    ('banbantong-python', 'Python27'),

    (PROJECT_DIR, 'manage.py'),
    (PROJECT_DIR, 'wsgi.py'),
    (PROJECT_DIR, 'conf.py'),
    (PROJECT_DIR, 'settings.py'),
    (PROJECT_DIR, 'urls.py'),
    (PROJECT_DIR, 'settings.sample.ini'),
    (PROJECT_DIR, 'requirements.txt'),
)


if __name__ == '__main__':
    print 'BASE_DIR:    ', BASE_DIR
    print 'PROJECT_DIR: ', PROJECT_DIR
    print 'PROJECT_NAME:', PROJECT_NAME
    print 'BUILD_DIR:   ', BUILD_DIR
    os.mkdir(BUILD_DIR)

    tar = tarfile.open(os.path.join(BUILD_DIR, '..', '%s.tar.gz' % VERSION), 'w:gz')
    for args in path_indludes:
        path = job(os.path.join(*args))
        if path:
            basename = os.path.basename(path)
            basename = path.split(PROJECT_DIR)[-1]
            tar.add(path, arcname=basename)
            shutil.rmtree(path, True)
    tar.close()
    shutil.rmtree(BUILD_DIR, True)
