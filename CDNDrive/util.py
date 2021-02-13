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

#bundle_dir = tempfile.gettempdir()
bundle_dir = path.join(os.path.expanduser('~'),".config","cdrive")
if not path.exists(bundle_dir):
    os.makedirs(bundle_dir)
cookie_fname = 'cdrive_cookies.json'
history_fname = '.drive_history.json'

def size_string(byte):
    if byte > 1024 * 1024 * 1024:
        return f"{byte / 1024 / 1024 / 1024:.2f} GB"
    elif byte > 1024 * 1024:
        return f"{byte / 1024 / 1024:.2f} MB"
    elif byte > 1024:
        return f"{byte / 1024:.2f} KB"
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

'''
sha1 file with filename (SHA1)
'''
def SHA1FileWithName(fineName, block_size=64 * 1024):
  with open(fineName, 'rb') as f:
    sha1 = hashlib.sha1()
    while True:
      data = f.read(block_size)
      if not data:
        break
      sha1.update(data)
    retsha1 = sha1.hexdigest()
    return retsha1
 
'''
md5 file with filename (MD5)
'''
def MD5FileWithName(fineName, block_size=64 * 1024):
  with open(fineName, 'rb') as f:
    md5 = hashlib.md5()
    while True:
      data = f.read(block_size)
      if not data:
        break
      md5.update(data)
    retmd5 = md5.hexdigest()
    return retmd5
    

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
    

def read_history(site=None,file_name=None):
    if file_name:
        fname = path.join(bundle_dir, path.basename(file_name) + history_fname)
    else:
        fname = path.join(bundle_dir, history_fname)
    if not path.exists(fname):
        return {}
    with open(fname, encoding="utf-8") as f:
        history = json.loads(f.read())
    if not site:
        return history
    else:
        return history.get(site, {})

def write_history(first_4mb_sha1, meta_dict, site, url,file_name=None):
    history = read_history(site,file_name)
    history.setdefault(site, {})
    history[site][first_4mb_sha1] = meta_dict
    history[site][first_4mb_sha1]['url'] = url
    with open(path.join(bundle_dir, path.basename(file_name) + history_fname), "w", encoding="utf-8") as f:
        f.write(json.dumps(history, ensure_ascii=False, indent=2))
    
def read_in_chunk(fname, size=4 * 1024 * 1024, cnt=-1):
    with open(fname, "rb") as f:
        idx = 0
        while True:
            data = f.read(size)
            if not data or (cnt != -1 and idx >= cnt):
                break
            yield data
            idx += 1
                
'''
upload
'''
def upload_in_chunk(fname,thread,trpool,tr_upload,block_dicts,hdls,size=4 * 1024 * 1024):
    with open(fname, "rb") as f:
        idx = 0
        thread_pool = []
        while True:
            while len(thread_pool) >= thread :
                time.sleep(1)
                for h in thread_pool: 
                    if h.done():
                        thread_pool.remove(h)
            data = f.read(size)
            if not data:
                break
            hdl = trpool.submit(tr_upload, idx, data, block_dicts[idx])
            hdls.append(hdl)
            thread_pool.append(hdl)
            idx += 1
            
        
    
    
    
def log(message):
    message = message.encode('gbk', 'ignore').decode('gbk')
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")
    
def request_retry(method, url, retry=10, **kwargs):
    kwargs.setdefault('timeout', 120)
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