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

class JianApi(BaseApi):

    default_url = lambda self, hash: f"https://upload-images.jianshu.io/upload_images/{hash}.png"
    extract_hash = lambda self, s: re.findall(r"\d{6}-[A-Fa-f0-9]{16}", s)[0]    

    def __init__(self):
        super().__init__()
        self.cookies = load_cookies('jian')
        
    def meta2real(self, url):
        if re.match(r"^jsdrive://\d{6}-[A-Fa-f0-9]{16}$", url):
            return self.default_url(self.extract_hash(url))
        else:
            return None
            
    def real2meta(self, url):
        return 'jsdrive://' + self.extract_hash(url)
        
    def set_cookies(self, cookie_str):
        self.cookies = parse_cookies(cookie_str)
        save_cookies('jian', self.cookies)
        
    def image_upload(self, img):
        
        fname = f"{time.time() * 1000}.png"
        url = f'https://www.jianshu.com/upload_images/token.json?filename={fname}'
        try:
            j = request_retry(
                'GET', url, 
                headers=JianApi.default_hdrs,
                cookies=self.cookies
            ).json()
        except Exception as ex:
            return {'code': 114514, 'message': str(ex)}
            
        if 'error' in j:
            return {'code': 114514, 'message': j['error']}
        
        url = 'https://upload.qiniup.com/'
        files = {
            'file': (fname, img),
        }
        data = {
            'token': j['token'],
            'key': j['key'],
            'x:protocol': 'https'
        }
        try:
            j = request_retry(
                'POST', url, 
                data=data,
                files=files, 
                headers=JianApi.default_hdrs,
            ).json()
        except Exception as ex:
            return {'code': 114514, 'message': str(ex)}
        
        if not j.get('url'):
            return {'code': 114514, 'message': '未知错误'}
        else:
            return {
                'code': 0, 
                'message': '',
                'data': j['url']
            }
        
def main():
    op = sys.argv[1]
    if op not in ['cookies', 'upload']:
        return
        
    api = JianApi()
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