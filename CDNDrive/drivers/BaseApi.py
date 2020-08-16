# coding: utf-8

from CDNDrive.util import *

class BaseApi:

    default_hdrs = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
    }
    
    def login(self, un, pw):
        return {
            'code': 114514,
            'message': '功能尚未实现，请使用 Cookie 登录'
        }
        
    def get_user_info(self, fmt=True):
        return '获取用户信息功能尚未实现'
        
    def image_download(self, url):
        return image_download(url)
        
    