# coding: utf-8

import sys
import base64
import hashlib
import random
import requests
import rsa
import time
import re
from urllib.parse import unquote
from CDNDrive.util import *
from .BaseApi import BaseApi

class SogouApi(BaseApi):

    default_hdrs = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
    }

    default_url = lambda self, hash: f"http://img01.sogoucdn.com/app/a/{hash}"
    extract_hash = lambda self, s: re.findall(r"\d+/[A-Za-z0-9]{32}", s)[0]    

    def __init__(self):
        super().__init__()
        self.cookies = load_cookies('sogou')
        
    def meta2real(self, url):
        if re.match(r"^sgdrive://\d+/[A-Za-z0-9]{32}$", url):
            return self.default_url(self.extract_hash(url))
        else:
            return None
            
    def real2meta(self, url):
        return 'sgdrive://' + self.extract_hash(url)
        
    def login(self, un, pw):
        return {
            'code': 0,
            'message': '该 API 无需登录'
        }
        
    def set_cookies(self, cookie_str):
        self.cookies = parse_cookies(cookie_str)
        save_cookies('sogou', self.cookies)
        
    def get_user_info(self, fmt=True):
        return '该 API 无需登录'
        
    def image_upload(self, img):
            
        url = 'https://pic.sogou.com/ris_upload'
        files = {'file': (f"{time.time()}.png", img, 'image/png')}
        try:
            r = request_retry(
                'POST', url, 
                files=files, 
                headers=SogouApi.default_hdrs,
                cookies=self.cookies,
                allow_redirects=False
            )
        except Exception as ex:
            return {'code': 114514, 'message': str(ex)}
        
        loc = r.headers.get('Location', '')
        m = re.search(r'query=([^&]+)', loc)
        if not m:
            return {'code': 114514, 'message': '未找到 URL'}
        pic = unquote(m.group(1))
        return {'code': 0, 'data': pic}
        
def main():
    op = sys.argv[1]
    if op not in ['cookies', 'upload']:
        return
        
    api = SogouApi()
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