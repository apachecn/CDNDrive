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

class SohuApi:

    default_hdrs = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
    }

    default_url = lambda self, hash: f"http://5b0988e595225.cdn.sohucs.com/images/{hash}.png"
    extract_hash = lambda self, s: re.findall(r"\d{8}/[A-Fa-f0-9]{32}", s)[0]    

    def __init__(self):
        self.cookies = load_cookies('sohu')
        
    def meta2real(self, url):
        if re.match(r"^shdrive://\d{8}/[A-Fa-f0-9]{32}$", url):
            return self.default_url(self.extract_hash(url))
        else:
            return None
            
    def real2meta(self, url):
        return 'shdrive://' + self.extract_hash(url)
        
    def login(self, un, pw):
        return {
            'code': 114514,
            'message': '功能尚未实现，请使用 Cookie 登录'
        }
        
    def set_cookies(self, cookie_str):
        self.cookies = parse_cookies(cookie_str)
        save_cookies('sohu', self.cookies)
        
    def get_user_info(self, fmt=True):
        return '获取用户信息功能尚未实现'
        
    def image_upload(self, img):
            
        url = 'https://mp.sohu.com/commons/front/outerUpload/v2/file'
        files = {'file': (f"{time.time() * 1000}.png", img)}
        try:
            j = request_retry(
                'POST', url, 
                files=files, 
                headers=SohuApi.default_hdrs,
                cookies=self.cookies
            ).json()
        except Exception as ex:
            return {'code': 114514, 'message': str(ex)}
        
        if not j.get('url'):
            return {'code': 114514, 'message': '未知错误'}
        else:
            return {
                'code': 0, 
                'message': '',
                'data': 'http:' + j['url']
            }
        
def main():
    op = sys.argv[1]
    if op not in ['cookies', 'upload']:
        return
        
    api = SohuApi()
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