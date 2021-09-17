# coding: utf-8

import sys
import base64
import hashlib
import random
import requests
import rsa
import time
import re
from urllib import parse
from CDNDrive.util import *
from .BaseApi import BaseApi

class AutoHomeApi(BaseApi):

    default_url = lambda self, hash: f"https://club2.autoimg.cn/{hash}.jpg"
    extract_hash = lambda self, s: re.findall(r"\w{2}/\w{3}/\w{2}/\w{2}/\w{30}", s)[0]    

    def __init__(self):
        super().__init__()
        self.cookies = load_cookies('autohome')
        
    def meta2real(self, url):
        if re.match(r"^ahdrive://\w{2}/\w{3}/\w{2}/\w{2}/\w{30}$", url):
            return self.default_url(self.extract_hash(url))
        else:
            return None
            
    def real2meta(self, url):
        return 'ahdrive://' + self.extract_hash(url)
        
    def set_cookies(self, cookie_str):
        self.cookies = parse_cookies(cookie_str)
        save_cookies('autohome', self.cookies)
        
    def image_upload(self, img):
            
        url = 'https://clubajax.autohome.com.cn/Upload/UpImageOfBase64New?dir=image&cros=autohome.com.c'
        files = {'file': (f"{time.time()}.jpg", img, 'image/jpeg')}
        try:
            r = request_retry(
                'POST', url, 
                files=files, 
                headers=AutoHomeApi.default_hdrs,
                cookies=self.cookies
            )
        except Exception as ex:
            return {'code': 114514, 'message': str(ex)}
            
        if r.status_code != 200:
            return {
                'code': r.status_code, 
                'message': f'HTTP {r.status_code}'
            }
            
        j = r.json()
        j['code'] = j.get('error', 0)
        if j['code'] == 0:
            j['data'] = 'https://club2.autoimg.cn/' + \
                re.sub(r'userphotos/\d+/\d+/\d+/\d+/', '', j['file'])
        return j
        
def main():
    op = sys.argv[1]
    if op not in ['cookies', 'upload']:
        return
        
    api = AutoHomeApi()
    if op == 'cookies':
        cookies = sys.argv[2]
        api.set_cookies(cookies)
        print('已设置')
    else:
        fname = sys.argv[2]
        img = open(fname, 'rb').read()
        r = api.image_upload(img)
        if r['code'] == 0:
            print(r['data'])
        else:
            print('上传失败：' + r['message'])
    
if __name__ == '__main__': main()