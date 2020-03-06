#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-

import base64
import hashlib
import random
import requests
import rsa
import time
import re
from urllib import parse
from BiliDriveEx.util import *

class Bilibili:
    app_key = "1d8b6e7d45233436"

    
    default_url = lambda self, sha1: f"http://i0.hdslb.com/bfs/album/{sha1}.png"
    meta_string = lambda self, url: ("bdex://" + re.findall(r"[a-fA-F0-9]{40}", url)[0]) if re.match(r"^http(s?)://i0.hdslb.com/bfs/album/[a-fA-F0-9]{40}.png$", url) else url
    
    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({'User-Agent': "Mozilla/5.0 BiliDroid/5.51.1 (bbcallen@gmail.com)"})
        self.get_cookies = lambda: self._session.cookies.get_dict(domain=".bilibili.com")
        self.get_uid = lambda: self.get_cookies().get("DedeUserID", "")
        self.username = ""
        self.password = ""
        self.info = {
            'ban': False,
            'coins': 0,
            'experience': {
                'current': 0,
                'next': 0,
            },
            'face': "",
            'level': 0,
            'nickname': "",
        }



    def _requests(self, method, url, decode_level=2, retry=0, timeout=10, **kwargs):
        if method in ["get", "post"]:
            for _ in range(retry + 1):
                try:
                    response = getattr(self._session, method)(url, timeout=timeout, **kwargs)
                    return response.json() if decode_level == 2 else response.content if decode_level == 1 else response
                except:
                    pass
        return None

    def _solve_captcha(self, image):
        url = "https://bili.dev:2233/captcha"
        payload = {'image': base64.b64encode(image).decode("utf-8")}
        response = self._requests("post", url, json=payload)
        return response['message'] if response and response.get("code") == 0 else None

    @staticmethod
    def calc_sign(param):
        salt = "560c52ccd288fed045859ed18bffd973"
        sign_hash = hashlib.md5()
        sign_hash.update(f"{param}{salt}".encode())
        return sign_hash.hexdigest()

    # 登录
    def login(self, username, password):
        def get_key():
            url = f"https://passport.bilibili.com/api/oauth2/getKey"
            payload = {
                'appkey': Bilibili.app_key,
                'sign': self.calc_sign(f"appkey={Bilibili.app_key}"),
            }
            while True:
                response = self._requests("post", url, data=payload)
                if response and response.get("code") == 0:
                    return {
                        'key_hash': response['data']['hash'],
                        'pub_key': rsa.PublicKey.load_pkcs1_openssl_pem(response['data']['key'].encode()),
                    }
                else:
                    time.sleep(1)

        self.username = username
        self.password = password

        while True:
            key = get_key()
            key_hash, pub_key = key['key_hash'], key['pub_key']
            url = f"https://passport.bilibili.com/api/v2/oauth2/login"
            param = f"appkey={Bilibili.app_key}&password={parse.quote_plus(base64.b64encode(rsa.encrypt(f'{key_hash}{self.password}'.encode(), pub_key)))}&username={parse.quote_plus(self.username)}"
            payload = f"{param}&sign={self.calc_sign(param)}"
            headers = {'Content-type': "application/x-www-form-urlencoded"}
            response = self._requests("post", url, data=payload, headers=headers)
            while True:
                if response and response.get("code") is not None:
                    if response['code'] == -105:
                        url = f"https://passport.bilibili.com/captcha"
                        headers = {'Host': "passport.bilibili.com"}
                        response = self._requests("get", url, headers=headers, decode_level=1)
                        captcha = self._solve_captcha(response)
                        if captcha:
                            log(f"登录验证码识别结果: {captcha}")
                            key = get_key()
                            key_hash, pub_key = key['key_hash'], key['pub_key']
                            url = f"https://passport.bilibili.com/api/v2/oauth2/login"
                            param = f"appkey={Bilibili.app_key}&captcha={captcha}&password={parse.quote_plus(base64.b64encode(rsa.encrypt(f'{key_hash}{self.password}'.encode(), pub_key)))}&username={parse.quote_plus(self.username)}"
                            payload = f"{param}&sign={self.calc_sign(param)}"
                            headers = {'Content-type': "application/x-www-form-urlencoded"}
                            response = self._requests("post", url, data=payload, headers=headers)
                        else:
                            log(f"登录验证码识别服务暂时不可用, 10秒后重试")
                            time.sleep(10)
                            break
                    elif response['code'] == -449:
                        time.sleep(1)
                        response = self._requests("post", url, data=payload, headers=headers)
                    elif response['code'] == 0 and response['data']['status'] == 0:
                        for cookie in response['data']['cookie_info']['cookies']:
                            self._session.cookies.set(cookie['name'], cookie['value'], domain=".bilibili.com")
                        log("登录成功")
                        return True
                    else:
                        log(f"登录失败 {response}")
                        return False
                else:
                    log(f"当前IP登录过于频繁, 1分钟后重试")
                    time.sleep(60)
                    break

    # 获取用户信息
    def get_user_info(self):
        url = f"https://api.bilibili.com/x/space/myinfo?jsonp=jsonp"
        headers = {
            'Host': "api.bilibili.com",
            'Referer': f"https://space.bilibili.com/{self.get_uid()}/",
        }
        response = self._requests("get", url, headers=headers)
        if response and response.get("code") == 0:
            self.info['ban'] = bool(response['data']['silence'])
            self.info['coins'] = response['data']['coins']
            self.info['experience']['current'] = response['data']['level_exp']['current_exp']
            self.info['experience']['next'] = response['data']['level_exp']['next_exp']
            self.info['face'] = response['data']['face']
            self.info['level'] = response['data']['level']
            self.info['nickname'] = response['data']['name']
            log(f"{self.info['nickname']}(UID={self.get_uid()}), Lv.{self.info['level']}({self.info['experience']['current']}/{self.info['experience']['next']}), 拥有{self.info['coins']}枚硬币, 账号{'状态正常' if not self.info['ban'] else '被封禁'}")
            return True
        else:
            log("用户信息获取失败")
            return False

            
    def exist(self, sha1):
        url = self.default_url(sha1)
        headers = {
            'Referer': "http://t.bilibili.com/",
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36",
        }
        for _ in range(5):
            try:
                response = requests.head(url, headers=headers, timeout=10)
                return url if response.status_code == 200 else None
            except:
                pass
        return None
        
        
    def image_upload(self, data, cookies):
        sha1 = calc_sha1(data)
        url = self.exist(sha1)
        if url: return {'code': 0, 'data': {'image_url': url}}
    
        url = "https://api.vc.bilibili.com/api/v1/drawImage/upload"
        headers = {
            'Origin': "https://t.bilibili.com",
            'Referer': "https://t.bilibili.com/",
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36",
        }
        files = {
            'file_up': (f"{int(time.time() * 1000)}.png", data),
        }
        data = {
            'biz': "draw",
            'category': "daily",
        }
        try:
            response = requests.post(url, data=data, headers=headers, cookies=cookies, files=files, timeout=300).json()
        except:
            response = None
        return response