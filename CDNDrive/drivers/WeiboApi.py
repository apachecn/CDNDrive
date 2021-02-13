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

class WeiboApi(BaseApi):

    default_url = lambda self, hash: f"https://wx1.sinaimg.cn/large/{hash}.gif"
    extract_hash = lambda self, s: re.findall(r"\w{32}", s)[0]    

    def __init__(self):
        super().__init__()
        self.cookies = load_cookies('weibo')
        
    def meta2real(self, url):
        if re.match(r"^wbdrive://\w{32}$", url):
            return self.default_url(self.extract_hash(url))
        else:
            return None
            
    def real2meta(self, url):
        return 'wbdrive://' + self.extract_hash(url)
        
    def set_cookies(self, cookie_str):
        self.cookies = parse_cookies(cookie_str)
        save_cookies('weibo', self.cookies)
        
    def image_download(self, url):
        url = re.sub(r'ws(\d).sinaimg.cn', r'wx\1.sinaimg.cn', url)
        return super().image_download(url)
        
    def image_upload(self, img):
            
        url = 'https://picupload.weibo.com/interface/pic_upload.php' + \
              '?ori=1&mime=image%2Fgif&data=base64&url=0&markpos=1' + \
              '&logo=&nick=0&marks=0&app=miniblog'
        data = {'b64_data': base64.b64encode(img)}
        try:
            jstr = request_retry(
                'POST', url, 
                data=data, 
                headers=WeiboApi.default_hdrs,
                cookies=self.cookies
            ).text
        except Exception as ex:
            return {'code': 114514, 'message': str(ex)}
        
        idx = jstr.find('{')
        if idx == -1:
            try:
                jstr = request_retry(
                    'POST', url, 
                    data=data, 
                    headers=WeiboApi.default_hdrs,
                    cookies=self.cookies
                ).text
            except Exception as ex:
                return {'code': 114514, 'message': str(ex)}
        idx = jstr.find('{')
        if idx == -1:
            return {'code': 114514, 'message': '未知错误'}
        j = json.loads(jstr[idx:])
        code = j['data']['pics']['pic_1']['ret']
        if code == 1:
            pid = j['data']['pics']['pic_1']['pid']
            return {
                'code': 0, 
                'data': self.default_url(pid)
            }
        else:
            return {'code': code, 'message': str(code)}
        
def main():
    op = sys.argv[1]
    if op not in ['cookies', 'upload']:
        return
        
    api = WeiboApi()
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