# -*- coding: utf-8 -*-

import os
import sys
from os import path
import hashlib
import types
import requests
import json
import time
import tempfile

bundle_dir = tempfile.gettempdir()
cookie_fname = 'cdrive_cookies'
history_dir = 'cdrive_history'

ONE_TB = 1 << 40
ONE_GB = 1 << 30
ONE_MB = 1 << 20
ONE_KB = 1 << 10

def size_string(byte):
    if byte >= ONE_TB:
        return f"{byte / ONE_TB:.2f} TB"
    elif byte >= ONE_GB:
        return f"{byte / ONE_GB:.2f} GB"
    elif byte >= ONE_MB:
        return f"{byte / ONE_MB:.2f} MB"
    elif byte >= ONE_KB:
        return f"{byte / ONE_KB:.2f} KB"
    else:
        return f"{int(byte)} B"

def calc_hash(data, algo, hex=True):
    hasher = getattr(hashlib, algo)()
    if hasattr(data, '__iter__') and \
       type(data) is not bytes:
        for chunk in data:
            hasher.update(chunk)
    else:
        hasher.update(data)
    return hasher.hexdigest() if hex else hasher.digest()
    
calc_sha1 = lambda data, hex=True: calc_hash(data, 'sha1', hex)
calc_md5 = lambda data, hex=True: calc_hash(data, 'md5', hex)
    
def image_download(url):
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36",
    }
    content = []
    last_chunk_time = None
    try:
        r = request_retry('GET', url, headers=headers, stream=True)
        for chunk in r.iter_content(128 * 1024):
            if last_chunk_time is not None and \
               time.time() - last_chunk_time > 5:
                return
            content.append(chunk)
            last_chunk_time = time.time()
    except:
        return
    return b"".join(content)
    

def safe_mkdir(dir):
    try: os.mkdir(dir)
    except: pass

def read_history_all(site=None):
    dir = path.join(bundle_dir, history_dir)
    if not path.isdir(dir):
        return {}
    res = {}
    fnames = os.listdir(dir)
    for fname in fnames:
        tmp = fname.replace('.json', '').split('-')
        if len(tmp) < 2: continue
        cur_site, f4m_sha1 = tmp[0], tmp[1]
        if site and cur_site != site: continue
        fname = path.join(dir, fname)
        try:
            cont = json.loads(open(fname, encoding="utf-8").read())
        except:
            continue
        res.setdefault(cur_site, {})
        res[cur_site][f4m_sha1] = cont
        
    if site:
        return res.get(site, {})
    else:
        return res

def read_history(site=None, f4m_sha1=None):
    if site is None or f4m_sha1 is None:
        return read_history_all(site)
    fname = path.join(bundle_dir, history_dir, f'{site}-{f4m_sha1}.json')
    if not path.isfile(fname):
        return None
    try:
        return json.loads(open(fname, encoding="utf-8").read())
    except:
        return None

def write_history(f4m_sha1, meta_dict, site, url):
    dir = path.join(bundle_dir, history_dir)
    safe_mkdir(dir)
    fname = path.join(dir, f'{site}-{f4m_sha1}.json')
    meta_dict['url'] = url
    open(fname, 'w', encoding='utf-8').write(
        json.dumps(meta_dict, ensure_ascii=False, indent=2))
    
def read_in_chunk(fname, size=4 * 1024 * 1024, cnt=-1):
    with open(fname, "rb") as f:
        idx = 0
        while True:
            data = f.read(size)
            if not data or (cnt != -1 and idx >= cnt):
                break
            yield data
            idx += 1
                
def log(message):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")
    
def request_retry(method, url, retry=10, **kwargs):
    kwargs.setdefault('timeout', 10)
    for i in range(retry):
        try:
            return requests.request(method, url, **kwargs)
        except Exception as ex:
            if i == retry - 1: raise ex
            
get_retry = lambda url, retry=10, **kwargs: request_retry('GET', url, retry, **kwargs)
post_retry = lambda url, retry=10, **kwargs: request_retry('POST', url, retry, **kwargs)

def print_meta(meta_dict, prefix=""):
    pad = ' ' * len(prefix)
    print(f"{prefix}文件名: {meta_dict['filename']}")
    print(f"{pad}大小: {size_string(meta_dict['size'])}")
    print(f"{pad}SHA-1: {meta_dict['sha1']}")
    print(f"{pad}上传时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(meta_dict['time']))}")
    print(f"{pad}分块数: {len(meta_dict['block'])}")
    for index, block_dict in enumerate(meta_dict['block']):
        print(f"{pad}分块{index + 1} ({size_string(block_dict['size'])}) URL: {block_dict['url']}")
        
def print_history_meta(meta_dict, prefix=""):
    print_meta(meta_dict, prefix)
    print(f"{' ' * len(prefix)}META URL: {meta_dict['url']}")
        
def block_offset(meta_dict, i):
    return sum(meta_dict['block'][j]['size'] for j in range(i))
    
def ask_overwrite():
    return (input(f"文件已存在, 是否覆盖? [y/N] ") in ["y", "Y"])
    
def load_cookies(site=None):
    fname = path.join(bundle_dir, cookie_fname)
    if not path.exists(fname):
        return {}
    with open(fname, encoding="utf-8") as f:
        cookies = json.loads(f.read())
    if not site: 
        return cookies
    else: 
        return cookies.get(site, {})

def save_cookies(site, cookies):
    full_cookies = load_cookies()
    full_cookies[site] = cookies
    fname = path.join(bundle_dir, cookie_fname)
    with open(fname, "w", encoding="utf-8") as f:
        f.write(json.dumps(full_cookies))
        
def parse_cookies(cookie_str):
    cookies = {}
    for kv in cookie_str.split('; '):
        kv = kv.split('=')
        if len(kv) != 2: continue
        cookies[kv[0]] = kv[1]
    return cookies