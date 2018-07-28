#!/usr/bin/env python
# coding=utf-8
import os
import shutil
import subprocess


command = 'taskkill /IM OEBBTServer.exe /F'
subprocess.call(command)

src = os.path.join('..', 'dist_console', 'OEBBTServer.exe')
dst = os.path.join('C:\\', 'Program Files', 'OsEasy', 'DADS', 'WebServer', 'DadsServer')
shutil.copy(src, dst)
for filename in ('BAN.dat', 'PYT.dat', 'MYS.dat', 'CHE.dat', 'DJA.dat',
                 'JIE.dat', 'NTP.dat', 'MEM.dat', 'PYP.dat', 'QIN.dat',
                 'SOU.dat', 'UPY.dat'):
    src = os.path.join('..', 'Build', 'dist_win', filename)
    shutil.copy(src, os.path.join(dst, 'BanBanTong'))
os.chdir(dst)
subprocess.call('OEBBTServer.exe')
