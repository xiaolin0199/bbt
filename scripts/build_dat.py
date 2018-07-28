#!/usr/bin/env python
# coding=utf-8
'''
    打包lib文件。
    Windows下需要安装GnuWin32的zip；Linux下需要安装zip命令。
'''
import compileall
import os
import platform
import shutil
import subprocess
import sys
import traceback

platform_system = platform.system()
if platform_system == 'Windows':
    ZIP_EXE = os.path.join('C:\\', 'Program Files', 'GnuWin32', 'bin',
                           'zip.exe')
    if not os.path.isfile(ZIP_EXE):
        print 'zip not installed'
        sys.exit(1)
else:
    ZIP_EXE = '/usr/bin/zip'

DISTPATH = 'dist_new'
PACKAGEPATH = 'package_new'
RESOURCEPATH = 'resource_new'
INIT_PY = os.path.join(os.path.dirname(__file__), '__init__.py')

# create directories for packaging
os.chdir(os.path.join('..', 'Build'))
if os.path.exists(DISTPATH):
    shutil.rmtree(DISTPATH)
os.mkdir(DISTPATH)
if os.path.exists(RESOURCEPATH):
    shutil.rmtree(RESOURCEPATH)
os.mkdir(RESOURCEPATH)


def pack_zip(path):
    compile_flag = True
    if '/' in path:
        zipname = path.split('/')[-1][:3].upper()
    else:
        zipname = path[:3].upper()
    print 'packaging %s to %s.dat' % (path, zipname)
    if os.path.exists(PACKAGEPATH):
        shutil.rmtree(PACKAGEPATH)
    os.mkdir(PACKAGEPATH)
    currdir = os.getcwd()
    if path == 'BanBanTong':
        os.chdir(PACKAGEPATH)
        shutil.copytree(os.path.join('..', '..', 'BanBanTong'), 'BanBanTong')
        os.chdir('BanBanTong')
        shutil.rmtree('logs', True)
        shutil.rmtree('public', True)
        shutil.rmtree('templates', True)
        shutil.rmtree('tests', True)
        shutil.rmtree('tmp', True)
        os.chdir(os.path.join('..', '..'))
    elif path == 'MySQLdb':
        shutil.copy(os.path.join('python_site_packages',
                                 'MySQL-python-1.2.5',
                                 '_mysql_exceptions.py'),
                    PACKAGEPATH)
        shutil.copytree(os.path.join('python_site_packages',
                                     'MySQL-python-1.2.5',
                                     'MySQLdb'),
                        os.path.join(PACKAGEPATH, 'MySQLdb'))
        # shutil.copy(INIT_PY, PACKAGEPATH)
    else:
        if path == 'python_libs':
            srcdir = os.path.join('Python-2.7.6', 'Lib')
            # shutil.copy(INIT_PY, PACKAGEPATH)
            compile_flag = False
        else:
            l = path.split('/')
            srcdir = os.path.join(l[0], l[1], l[2])
        if os.path.isfile(srcdir):
            shutil.copy(srcdir, PACKAGEPATH)
            # shutil.copy(INIT_PY, PACKAGEPATH)
        else:
            for f in os.listdir(srcdir):
                src = os.path.join(currdir, srcdir, f)
                if os.path.isfile(src):
                    shutil.copy(src, PACKAGEPATH)
                elif os.path.isdir(src):
                    shutil.copytree(src, os.path.join(PACKAGEPATH, f))
                else:
                    print 'unrecognized file', src
    if compile_flag:
        # compile code
        compileall.compile_dir(os.path.join(currdir, PACKAGEPATH), force=True,
                               quiet=True)
        # remove non-compiled files
        files = [i for i in os.walk(PACKAGEPATH)]
        for l in files:
            for filename in l[2]:
                dst = os.path.join(l[0], filename)
                if os.path.splitext(dst)[1] != '.pyc':
                    os.remove(dst)
    # pack code
    os.chdir(PACKAGEPATH)
    dst = os.path.join('..', DISTPATH, '%s.dat' % zipname)
    command = '%s -q -r "%s" .' % (ZIP_EXE, dst)
    print command
    subprocess.call(command)
    os.chdir('..')
    shutil.rmtree(PACKAGEPATH)

pack_zip('BanBanTong')
pack_zip('python_libs')
pack_zip('MySQLdb')
pack_zip('python_site_packages/certifi-14.05.14/certifi')
pack_zip('python_site_packages/CherryPy-3.3.0/cherrypy')
pack_zip('python_site_packages/Django-1.6.4/django')
pack_zip('python_site_packages/jieba-0.32/jieba')
pack_zip('python_site_packages/ntplib-0.3.2/ntplib.py')
pack_zip('python_site_packages/python-memcached-1.53/memcache.py')
pack_zip('python_site_packages/pypinyin-0.5.1/pypinyin')
pack_zip('python_site_packages/qiniu-6.1.6/qiniu')
pack_zip('python_site_packages/requests-2.4.0/requests')
pack_zip('python_site_packages/South-0.8.4/south')
pack_zip('python_site_packages/upyun-2.2.0/upyun')

print 'packaging resource files'
os.chdir(RESOURCEPATH)
shutil.copytree(os.path.join('..', '..', 'BanBanTong', 'templates'), 'templates')
shutil.copytree(os.path.join('..', '..', 'BanBanTong', 'public', 'js'), 'js')
shutil.copytree(os.path.join('..', '..', 'BanBanTong', 'public', 'images'), 'images')
dst = os.path.join('..', DISTPATH, 'resources.dll')
command = '%s -q -r -Poseasy_resource_password_5e98sw "%s" .' % (ZIP_EXE, dst)
print command
subprocess.call(command)
os.chdir('..')
print os.getcwd()

shutil.rmtree(RESOURCEPATH)
