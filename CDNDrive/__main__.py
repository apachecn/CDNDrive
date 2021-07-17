#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-

import argparse
import hashlib
import json
import math
import os
from os import path
import re
import requests
import shlex
import signal
import struct
import shutil
import sys
import threading
import time
import traceback
import types
import zlib
from concurrent.futures import ThreadPoolExecutor
from . import __version__
from .drivers import *
from .encoders import *
from .util import *

encoder = None
api = None

succ = True
nblocks = 0
lock = threading.Lock()

def load_api_by_prefix(s):
    global api
    global encoder

    prefix = s.split('://')[0]
    if prefix not in prefixes:
        return False
    site = prefixes[prefix]
    api = drivers[site]
    encoder = encoders[site]
    return True

def fetch_meta(s):
    url = api.meta2real(s)
    if not url: return None
    full_meta = api.image_download(url)
    if not full_meta: return None
    meta_dict = json.loads(encoder.decode(full_meta).decode("utf-8"))
    return meta_dict

def login_handle(args):
    global api
    
    api = drivers[args.site]
    r = api.login(args.username, args.password)
    if r['code'] != 0:
        log(f"登录失败：{r['message']}")
        return
    info = api.get_user_info()
    if info: log(info)
    else: log("用户信息获取失败")

def cookies_handle(args):
    global api
    
    api = drivers[args.site]
    api.set_cookies(args.cookies)
    info = api.get_user_info()
    if info: log(info)
    else: log("用户信息获取失败")

def userinfo_handle(args):
    global api
    
    api = drivers[args.site]
    info = api.get_user_info()
    if info: log(info)
    else: log("用户未登录")
    
def tr_upload(i, block, block_dict):
    global succ

    enco_block = encoder.encode(block)
    for j in range(10):
        if not succ: break
        r = api.image_upload(enco_block)
        if r['code'] == 0:
            block_dict.update({
                'url': r['data'],
                'size': len(block),
                'sha1': calc_sha1(block),
            })
            log(f'分块{i + 1}/{nblocks}上传完毕')
            break
        else:
            log(f"分块{i + 1}/{nblocks}第{j + 1}次上传失败：{r.get('message')}")
            if j == 9: succ = False

def get_all_file(filepath):
    filelist=[]
    for root, dirnames, filenames in os.walk(filepath):
        for filename in filenames:
            filelist.append(os.path.join(root,filename))
    return filelist

def upload_handle(args):
    global api
    global encoder
    global succ
    global nblocks

    api = drivers[args.site]
    encoder = encoders[args.site]
    start_time = time.time()
    file_name = args.file
    
    if not path.exists(file_name):
        log(f"文件{file_name}不存在")
        return
    if path.isdir(file_name):
        log("正在测试支持上传文件夹")
        filelist = get_all_file(file_name)
        dir_file_date = {} # 用于存储文件夹信息
        for f in filelist:
            args.file = f
            f_url = upload_handle(args)
            dir_file_date[api.real2meta(f_url)] = f
        s = json.dumps(dir_file_date,ensure_ascii=False)   #将数据转化成字符串
        with open("../shareDir.json",'w') as sd:
            sd.write(s)
        log("文件夹上传成功")
        return
    log(f"上传: {path.basename(file_name)} ({size_string(path.getsize(file_name))})")
    first_4mb_sha1 = calc_sha1(read_in_chunk(file_name, size=4 * 1024 * 1024, cnt=1))
    history = read_history(args.site)
    if first_4mb_sha1 in history:
        url = history[first_4mb_sha1]['url']
        log(f"文件已于{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(history[first_4mb_sha1]['time']))}上传, 共有{len(history[first_4mb_sha1]['block'])}个分块")
        log(f"META URL -> {api.real2meta(url)}")
        return url

    if not api.get_user_info():
        log("账号未登录，请先登录")
        return
        
    log(f"线程数: {args.thread}")
    succ = True
    nblocks = math.ceil(path.getsize(file_name) / (args.block_size * 1024 * 1024))
    block_dicts = [{} for _ in range(nblocks)]
    trpool = ThreadPoolExecutor(args.thread)
    hdls = []
    
    blocks = read_in_chunk(file_name, size=args.block_size * 1024 * 1024)
    for i, block in enumerate(blocks):
        hdl = trpool.submit(tr_upload, i, block, block_dicts[i])
        hdls.append(hdl)
        # 及时清理队列中的任务
        if len(hdls) == args.thread:    
            for h in hdls: h.result()
            hdls = []
    for h in hdls: h.result()
    if not succ: return
    
    sha1 = calc_sha1(read_in_chunk(file_name))
    meta_dict = {
        'time': int(time.time()),
        'filename': path.basename(file_name),
        'size': path.getsize(file_name),
        'sha1': sha1,
        'block': block_dicts,
    }
    meta = json.dumps(meta_dict, ensure_ascii=False).encode("utf-8")
    full_meta = encoder.encode(meta)
    r = api.image_upload(full_meta)
    if r['code'] == 0:
        url = r['data']
        log("元数据上传完毕")
        log(f"{meta_dict['filename']} ({size_string(meta_dict['size'])}) 上传完毕, 用时{time.time() - start_time:.1f}秒, 平均速度{size_string(meta_dict['size'] / (time.time() - start_time))}/s")
        log(f"META URL -> {api.real2meta(url)}")
        write_history(first_4mb_sha1, meta_dict, args.site, url)
        return url
    else:
        log(f"元数据上传失败：{r.get('message')}")
        return


def tr_download(i, block_dict, f, offset):
    global succ

    url = block_dict['url']
    for j in range(10):
        if not succ: break
        block = api.image_download(url)
        if not block:
            log(f"分块{i + 1}/{nblocks}第{j + 1}次下载失败")
            if j == 9: succ = False
            continue
        block = encoder.decode(block)
        if calc_sha1(block) == block_dict['sha1']:
            with lock:
                f.seek(offset)
                f.write(block)
            log(f"分块{i + 1}/{nblocks}下载完毕")
            break
        else:
            log(f"分块{i + 1}/{nblocks}校验未通过")
            if j == 9: succ = False
            

def download_handle(args):
    global succ
    global nblocks

    if not load_api_by_prefix(args.meta):
        log("元数据解析失败")
        return
    start_time = time.time()
    meta_dict = fetch_meta(args.meta)
    if not meta_dict:
        log("元数据解析失败")
        return

    file_name = args.file if args.file else meta_dict['filename']
    log(f"下载: {path.basename(file_name)} ({size_string(meta_dict['size'])}), 共有{len(meta_dict['block'])}个分块, 上传于{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(meta_dict['time']))}")

    if path.exists(file_name):
        if path.getsize(file_name) == meta_dict['size'] and calc_sha1(read_in_chunk(file_name)) == meta_dict['sha1']:
            log("文件已存在, 且与服务器端内容一致")
            return file_name
        if not args.force and not ask_overwrite():
            return

    log(f"线程数: {args.thread}")
    succ = True
    nblocks = len(meta_dict['block'])
    trpool = ThreadPoolExecutor(args.thread)
    hdls = []
    
    mode = "r+b" if path.exists(file_name) else "wb"
    with open(file_name, mode) as f:
        for i, block_dict in enumerate(meta_dict['block']):
            offset = block_offset(meta_dict, i)
            hdl = trpool.submit(tr_download, i, block_dict, f, offset)
            hdls.append(hdl)
            # 及时清理队列中的任务
            if len(hdls) == args.thread:    
                for h in hdls: h.result()
                hdls = []
        for h in hdls: h.result()
        if not succ: return
        f.truncate(meta_dict['size'])
    
    log(f"{path.basename(file_name)} ({size_string(meta_dict['size'])}) 下载完毕, 用时{time.time() - start_time:.1f}秒, 平均速度{size_string(meta_dict['size'] / (time.time() - start_time))}/s")
    sha1 = calc_sha1(read_in_chunk(file_name))
    if sha1 == meta_dict['sha1']:
        log("文件校验通过")
        return file_name
    else:
        log("文件校验未通过")
        return


def dir_file_download_handle(args):
    with open("./shareDir.txt",'r') as sd:
        data = json.loads(sd.read())
    for i in data:
        args.meta = i
        filepath = os.path.dirname(data[i])
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        download_handle(args)
        try:
            shutil.move(os.path.basename(data[i]), filepath)
        except:
            log("未找到该文件")

    pass


def info_handle(args):
    if not load_api_by_prefix(args.meta):
        log("元数据解析失败")
        return
    meta_dict = fetch_meta(args.meta)
    if meta_dict:
        print_meta(meta_dict)
    else:
        log("元数据解析失败")

def history_handle(args):
    global api

    all_history = read_history()
    if len(all_history) == 0:
        print(f"暂无历史记录")
        return
    idx = 0
    for site, history in all_history.items():
        api = drivers[site]
        for meta_dict in history.values():
            prefix = f"[{idx + 1}] "
            meta_dict['url'] = api.real2meta(meta_dict['url'])
            print_history_meta(meta_dict, prefix)
            idx += 1

def interact_mode(parser, subparsers):
    subparsers.add_parser("help", help="show this help message").set_defaults(func=lambda _: parser.parse_args(["--help"]).func())
    subparsers.add_parser("version", help="show program's version number").set_defaults(func=lambda _: parser.parse_args(["--version"]).func())
    subparsers.add_parser("exit", help="exit program").set_defaults(func=lambda _: os._exit(0))
    parser.print_help()
    while True:
        try:
            args = shlex.split(input("CDNDrive > "))
            args = parser.parse_args(args)
            args.func(args)
        except:
            pass

def main():
    signal.signal(signal.SIGINT, lambda signum, frame: os.kill(os.getpid(), 9))
    parser = argparse.ArgumentParser(prog="CDNDrive", description="Make Picbeds Great Cloud Storages!", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-v", "--version", action="version", version=f"CDNDrive version: {__version__}")
    parser.set_defaults(func=lambda x: parser.print_help())
    subparsers = parser.add_subparsers()
    
    login_parser = subparsers.add_parser("login", help="log in to the site")
    login_parser.add_argument("site", help="site", choices=drivers.keys())
    login_parser.add_argument("username", help="username")
    login_parser.add_argument("password", help="password")
    login_parser.set_defaults(func=login_handle)
    
    cookies_parser = subparsers.add_parser("cookies", help="set cookies to the site")
    cookies_parser.add_argument("site", help="site", choices=drivers.keys())
    cookies_parser.add_argument("cookies", help="cookies")
    cookies_parser.set_defaults(func=cookies_handle)

    userinfo_parser = subparsers.add_parser("userinfo", help="get userinfo")
    userinfo_parser.add_argument("site", help="site", choices=drivers.keys())
    userinfo_parser.set_defaults(func=userinfo_handle)
    
    upload_parser = subparsers.add_parser("upload", help="upload a file")
    upload_parser.add_argument("site", help="site", choices=drivers.keys())
    upload_parser.add_argument("file", help="name of the file to upload")
    upload_parser.add_argument("-b", "--block-size", default=4, type=int, help="block size in MB")
    upload_parser.add_argument("-t", "--thread", default=4, type=int, help="upload thread number")
    upload_parser.set_defaults(func=upload_handle)
    
    download_parser = subparsers.add_parser("download", help="download a file")
    download_parser.add_argument("meta", help="meta url")
    download_parser.add_argument("file", nargs="?", default="", help="new file name")
    download_parser.add_argument("-f", "--force", action="store_true", help="force to overwrite if file exists")
    download_parser.add_argument("-t", "--thread", default=8, type=int, help="download thread number")
    download_parser.set_defaults(func=download_handle)

    downloadDir_parser = subparsers.add_parser("downloadDir", help="download some files")
    downloadDir_parser.add_argument("meta",  default="", help="meta url")
    downloadDir_parser.add_argument("share", default="./shareDir.txt", help="path")
    downloadDir_parser.add_argument("file", nargs="?", default="", help="new file name")
    downloadDir_parser.add_argument("-f", "--force", action="store_true", help="force to overwrite if file exists")
    downloadDir_parser.add_argument("-t", "--thread", default=8, type=int, help="download thread number")
    downloadDir_parser.set_defaults(func=dir_file_download_handle)

    info_parser = subparsers.add_parser("info", help="show meta info")
    info_parser.add_argument("meta", help="meta url")
    info_parser.set_defaults(func=info_handle)
    history_parser = subparsers.add_parser("history", help="show upload history")
    history_parser.set_defaults(func=history_handle)
    
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
