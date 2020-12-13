# coding: utf-8

import os
from os import path
import tempfile
import sys
import shutil

SRC = os.environ.get('SRC', "").strip()
DST = os.environ.get('DST', 'all').strip()
COOKIES = os.environ.get('COOKIES')
ALL_DRIVERS = ['bili', 'baijia', 'jian', 'csdn', 'sohu', 'ali', 'weibo']

def safe_mkdir(dir):
    try: os.mkdir(dir)
    except: pass
    
def safe_rmdir(dir):
    try: shutil.rmtree(dir)
    except: pass

def main():
    
    # 设置 Cookie
    if COOKIES:
        fname = path.join(tempfile.gettempdir(), 'cdrive_cookies.json')
        with open(fname, 'w') as f:
            f.write(COOKIES)
            
    # 下载
    if SRC.startswith('http'):
        urls = SRC.split(';')
        safe_rmdir('src')
        safe_mkdir('src')
        os.chdir('src')
        for url in urls:
            os.system(f'wget {url}')
        os.chdir('..')
    elif SRC.startswith('git+'):
        url = SRC[4:]
        safe_rmdir('src')
        os.system(f'git clone {url} src')
    elif SRC.startswith('cdrive+'):
        urls = SRC[7:].split(';')
        safe_rmdir('src')
        safe_mkdir('src')
        os.chdir('src')
        for url in urls:
            os.system(f'cdrive download {url}')
        os.chdir('..')
    else:
        print('未知来源')
        sys.exit()

    # 上传
    if DST.lower() == 'all':
        dst = ALL_DRIVERS
    else:
        dst = DST.split(':')
    
    files = os.listdir('src')
    
    for d in dst:
        for f in files:
            os.system(f'cdrive upload {d} "src/{f}" | tee -a log.txt')
            
if __name__ == '__main__': main()