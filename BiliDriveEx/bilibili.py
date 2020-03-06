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

    default_hdrs = {'User-Agent': "Mozilla/5.0 BiliDroid/5.51.1 (bbcallen@gmail.com)"}
    
    default_url = lambda self, sha1: f"http://i0.hdslb.com/bfs/album/{sha1}.png"
    meta_string = lambda self, url: ("bdex://" + re.findall(r"[a-fA-F0-9]{40}", url)[0]) if re.match(r"^http(s?)://i0.hdslb.com/bfs/album/[a-fA-F0-9]{40}.png$", url) else url
    
    get_cookies = lambda self: self.cookies
    
    def __init__(self):
        self.cookies = {}
        self.load_cookies()

    def set_cookies(self, cookie_str):
        self.cookies = {}
        for kv in cookie_str.split('; '):
            kv = kv.split('=')
            if len(kv) != 2: continue
            self.cookies[kv[0]] = kv[1]
        self.save_cookies()
            
        
    def _solve_captcha(self, image):
        url = "https://bili.dev:2233/captcha"
        payload = {'image': base64.b64encode(image).decode("utf-8")}
        try:
            j = request_retry("post", url, 
                headers=Bilibili.default_hdrs,
                json=payload
            ).json()
        except:
            return None
        return j['message'] if j['code'] == 0 else None

    @staticmethod
    def calc_sign(param):
        salt = "560c52ccd288fed045859ed18bffd973"
        sign_hash = hashlib.md5()
        sign_hash.update(f"{param}{salt}".encode())
        return sign_hash.hexdigest()

        
    def _get_key(self):
        url = f"https://passport.bilibili.com/api/oauth2/getKey"
        payload = {
            'appkey': Bilibili.app_key,
            'sign': self.calc_sign(f"appkey={Bilibili.app_key}"),
        }
        try:
            r = request_retry("post", url, data=payload, 
                headers=Bilibili.default_hdrs,
                cookies=self.cookies, retry=999999
            )
        except:
            return None
        for k, v in r.cookies.items(): self.cookies[k] = v
        j = r.json()
        if j['code'] == 0:
            return {
                'key_hash': j['data']['hash'],
                'pub_key': rsa.PublicKey.load_pkcs1_openssl_pem(j['data']['key'].encode()),
            }
        else:
            return None
        
    def _login_once(self, username, password, captcha=None):
        key = self._get_key()
        if not key: return {'code': 114514, 'message': 'key 获取失败'}
        key_hash, pub_key = key['key_hash'], key['pub_key']
        
        username = parse.quote_plus(username)
        password = parse.quote_plus(base64.b64encode(rsa.encrypt(f'{key_hash}{password}'.encode(), pub_key)))
        
        url = f"https://passport.bilibili.com/api/v2/oauth2/login"
        param = f"appkey={Bilibili.app_key}"
        if captcha: param += f'&captcha={captcha}'
        param += f"&password={password}&username={username}"
        payload = f"{param}&sign={self.calc_sign(param)}"
        headers = Bilibili.default_hdrs.copy()
        headers.update({'Content-type': "application/x-www-form-urlencoded"})
        
        try:
            j = request_retry("POST", url, data=payload, 
                headers=headers, 
                cookies=self.cookies
            ).json()
        except Exception as ex:
            return {'code': 114514, 'message': str(ex)}
        return j
        
    def _get_captcha(self):
        url = f"https://passport.bilibili.com/captcha"
        try:
            img = request_retry('GET', url, 
                headers=Bilibili.default_hdrs, 
                cookies=self.cookies
            ).content
        except:
            return None
        return img
        
    # 登录
    def login(self, username, password):

        captcha = None
        while True:
            j = self._login_once(username, password, captcha)
            
            if 'code' not in j:
                log(f"当前IP登录过于频繁, 1分钟后重试")
                time.sleep(60)
                continue
                
            if j['code'] == -105:
                img = self._get_captcha()
                if not img:
                    log(f"验证码获取失败")
                    time.sleep(1)
                    continue
                captcha = self._solve_captcha(img)
                if captcha:
                    log(f"登录验证码识别结果: {captcha}")
                else:
                    log(f"登录验证码识别服务暂时不可用, 10秒后重试")
                    time.sleep(10)
                continue
                
            if j['code'] == -449:
                time.sleep(1)
                continue
            
            if j['code'] == 0 and j['data']['status'] == 0:
                self.cookies = {}
                for cookie in j['data']['cookie_info']['cookies']:
                    self.cookies[cookie['name']] = cookie['value']
                log("登录成功")
                self.save_cookies()
                return True
            
            log(f"登录失败 {j['message']}")
            return False


    # 获取用户信息
    def get_user_info(self, fmt=True):
        url = f"https://api.bilibili.com/x/space/myinfo"
        headers = Bilibili.default_hdrs.copy()
        headers.update({
            'Referer': f"https://space.bilibili.com",
        })
        
        try:
            j = request_retry("get", url, 
                headers=headers, 
                cookies=self.cookies
            ).json()
        except:
            return
        
        if j['code'] != 0: return
        
        info = {
            'ban': False,
            'coins': 0,
            'experience': {
                'current': 0,
                'next': 0,
            },
            'face': "",
            'level': 0,
            'nickname': "",
            'uid': 0,
        }
        info['ban'] = bool(j['data']['silence'])
        info['coins'] = j['data']['coins']
        info['experience']['current'] = j['data']['level_exp']['current_exp']
        info['experience']['next'] = j['data']['level_exp']['next_exp']
        info['face'] = j['data']['face']
        info['level'] = j['data']['level']
        info['nickname'] = j['data']['name']
        info['uid'] = j['data']['mid']
        
        if fmt:
            return f"{info['nickname']}(UID={info['uid']}), Lv.{info['level']}({info['experience']['current']}/{info['experience']['next']}), 拥有{info['coins']}枚硬币, 账号{'状态正常' if not info['ban'] else '被封禁'}"
        else:
            return info
            
    def save_cookies(self):
        with open(os.path.join(bundle_dir, "cookies.json"), "w", encoding="utf-8") as f:
            f.write(json.dumps(self.cookies, ensure_ascii=False, indent=2))
            
    def load_cookies(self):
        try:
            with open(os.path.join(bundle_dir, "cookies.json"), "r", encoding="utf-8") as f:
                self.cookies = json.loads(f.read())
        except:
            pass
            
    def exist(self, sha1):
        url = self.default_url(sha1)
        try:
            r = request_retry('HEAD', url, headers=Bilibili.default_hdrs)
        except:
            return
        return url if r.status_code == 200 else None
        
    def image_upload(self, data):
        sha1 = calc_sha1(data)
        url = self.exist(sha1)
        if url: return {'code': 0, 'data': {'image_url': url}}
        
        url = "https://api.vc.bilibili.com/api/v1/drawImage/upload"
        headers = Bilibili.default_hdrs.copy()
        headers.update({
            'Origin': "https://t.bilibili.com",
            'Referer': "https://t.bilibili.com/",
        })
        files = {
            'file_up': (f"{int(time.time() * 1000)}.png", data),
        }
        data = {
            'biz': "draw",
            'category': "daily",
        }
        try:
            r = requests.post(url, data=data, 
                headers=headers, 
                cookies=self.cookies, 
                files=files, timeout=300
            )
        except Exception as ex:
            return {'code': 114514, 'message': str(ex)}
            
        if r.status_code != 200:
            return {'code': r.status_code, 'message': r.text}
        return r.json()