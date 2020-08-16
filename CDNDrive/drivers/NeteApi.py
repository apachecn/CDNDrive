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

class NeteApi(BaseApi):

    default_url = lambda self, hash: f"http://dingyue.ws.126.net/{hash}.png"
    extract_hash = lambda self, s: re.findall(r"\d{4}/\d{4}/\w{32}", s)[0]    

    def __init__(self):
        super().__init__()
        self.cookies = load_cookies('163')
        
    def meta2real(self, url):
        if re.match(r"^nedrive://\d{4}/\d{4}/\w{32}$", url):
            return self.default_url(self.extract_hash(url))
        else:
            return None
            
    def real2meta(self, url):
        return 'nedrive://' + self.extract_hash(url)
        
    def set_cookies(self, cookie_str):
        self.cookies = parse_cookies(cookie_str)
        save_cookies('163', self.cookies)
        
    def image_upload(self, img):
            
        url = 'http://upload.buzz.163.com/picupload'
        data = {'from': 'neteasecode_mp'}
        files = {'file': (f"{time.time()}.png", img, 'image/png')}
        try:
            j = request_retry(
                'POST', url, 
                data=data,
                files=files, 
                headers=NeteApi.default_hdrs,
                cookies=self.cookies
            ).json()
        except Exception as ex:
            return {'code': 114514, 'message': str(ex)}
        
        j['message'] = j['msg']
        if j['code'] == 200:
            j['code'] = 0
            j['data'] = j['data']['url']
        return j
        
def main():
    op = sys.argv[1]
    if op not in ['cookies', 'upload']:
        return
        
    api = NeteApi()
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