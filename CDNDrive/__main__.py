#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-

import argparse
import hashlib
import json
import math
import os
import re
import requests
import shlex
import signal
import struct
import sys
import threading
import time
import traceback
import types
from concurrent.futures import ThreadPoolExecutor
from CDNDrive import __version__
from CDNDrive.bilibili import Bilibili
from CDNDrive.encoder import Encoder
from CDNDrive.util import *

encoder = Encoder()
api = Bilibili()

succ = True
nblocks = 0
lock = threading.Lock()

def fetch_meta(s):
    url = api.meta2real(s)
    if not url: return None
    full_meta = image_download(url)
    if not full_meta: return None
    meta_dict = json.loads(encoder.decode(full_meta).decode("utf-8"))
    return meta_dict

def login_handle(args):
    r = api.login(args.username, args.password)
    if r['code'] != 0:
        log(f"登录失败：{r['message']}")
        return
    info = api.get_user_info()
    if info: log(info)
    else: log("用户信息获取失败")

def cookies_handle(args):
    api.set_cookies(args.cookies)
    info = api.get_user_info()
    if info: log(info)
    else: log("用户信息获取失败")

def userinfo_handle(args):
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
            url = r['data']['image_url']
            block_dict.update({
                'url': url,
                'size': len(block),
                'sha1': calc_sha1(block),
            })
            log(f'分块{i + 1}/{nblocks}上传完毕')
            break
        else:
            log(f"分块{i + 1}/{nblocks}第{j + 1}次上传失败：{r.get('message')}")
            if j == 9: succ = False
    
def upload_handle(args):
    global succ
    global nblocks

    start_time = time.time()
    file_name = args.file
    if not os.path.exists(file_name):
        log(f"文件{file_name}不存在")
        return
    if os.path.isdir(file_name):
        log("暂不支持上传文件夹")
        return
    log(f"上传: {os.path.basename(file_name)} ({size_string(os.path.getsize(file_name))})")
    first_4mb_sha1 = calc_sha1(read_in_chunk(file_name, size=4 * 1024 * 1024, cnt=1))
    history = read_history()
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
    nblocks = math.ceil(os.path.getsize(file_name) / (args.block_size * 1024 * 1024))
    block_dicts = [{} for _ in range(nblocks)]
    trpool = ThreadPoolExecutor(args.thread)
    hdls = []
    
    blocks = read_in_chunk(file_name, size=args.block_size * 1024 * 1024)
    for i, block in enumerate(blocks):
        hdl = trpool.submit(tr_upload, i, block, block_dicts[i])
        hdls.append(hdl)
    for h in hdls: h.result()
    if not succ: return
    
    sha1 = calc_sha1(read_in_chunk(file_name))
    meta_dict = {
        'time': int(time.time()),
        'filename': os.path.basename(file_name),
        'size': os.path.getsize(file_name),
        'sha1': sha1,
        'block': block_dicts,
    }
    meta = json.dumps(meta_dict, ensure_ascii=False).encode("utf-8")
    full_meta = encoder.encode(meta)
    r = api.image_upload(full_meta)
    if r['code'] == 0:
        url = r['data']['image_url']
        log("元数据上传完毕")
        log(f"{meta_dict['filename']} ({size_string(meta_dict['size'])}) 上传完毕, 用时{time.time() - start_time:.1f}秒, 平均速度{size_string(meta_dict['size'] / (time.time() - start_time))}/s")
        log(f"META URL -> {api.real2meta(url)}")
        write_history(first_4mb_sha1, meta_dict, url)
        return url
    else:
        log(f"元数据上传失败：{r.get('message')}")
        return


def tr_download(i, block_dict, f, offset):
    global succ

    url = block_dict['url']
    for j in range(10):
        if not succ: break
        block = image_download(url)
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

    start_time = time.time()
    meta_dict = fetch_meta(args.meta)
    if not meta_dict:
        log("元数据解析失败")
        return

    file_name = args.file if args.file else meta_dict['filename']
    log(f"下载: {os.path.basename(file_name)} ({size_string(meta_dict['size'])}), 共有{len(meta_dict['block'])}个分块, 上传于{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(meta_dict['time']))}")

    if os.path.exists(file_name):
        if os.path.getsize(file_name) == meta_dict['size'] and calc_sha1(read_in_chunk(file_name)) == meta_dict['sha1']:
            log("文件已存在, 且与服务器端内容一致")
            return file_name
        if not args.force and not ask_overwrite():
            return

    log(f"线程数: {args.thread}")
    succ = True
    nblocks = len(meta_dict['block'])
    trpool = ThreadPoolExecutor(args.thread)
    hdls = []
    
    mode = "r+b" if os.path.exists(file_name) else "wb"
    with open(file_name, mode) as f:
        for i, block_dict in enumerate(meta_dict['block']):
            offset = block_offset(meta_dict, i)
            hdl = trpool.submit(tr_download, i, block_dict, f, offset)
            hdls.append(hdl)
        for h in hdls: h.result()
        if not succ: return
        f.truncate(meta_dict['size'])
    
    log(f"{os.path.basename(file_name)} ({size_string(meta_dict['size'])}) 下载完毕, 用时{time.time() - start_time:.1f}秒, 平均速度{size_string(meta_dict['size'] / (time.time() - start_time))}/s")
    sha1 = calc_sha1(read_in_chunk(file_name))
    if sha1 == meta_dict['sha1']:
        log("文件校验通过")
        return file_name
    else:
        log("文件校验未通过")
        return

def info_handle(args):
    meta_dict = fetch_meta(args.meta)
    if meta_dict:
        print_meta(meta_dict)
    else:
        log("元数据解析失败")

def history_handle(args):
    history = read_history()
    if history:
        for index, meta_dict in enumerate(history.values()):
            prefix = f"[{index + 1}]"
            print(f"{prefix} {meta_dict['filename']} ({size_string(meta_dict['size'])}), 共有{len(meta_dict['block'])}个分块, 上传于{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(meta_dict['time']))}")
            print(f"{' ' * len(prefix)} META URL -> {api.real2meta(meta_dict['url'])}")
    else:
        print(f"暂无历史记录")

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
    parser = argparse.ArgumentParser(prog="CDNDrive", description="Make Bilibili A Great Cloud Storage!", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-v", "--version", action="version", version=f"CDNDrive version: {__version__}")
    subparsers = parser.add_subparsers()
    
    login_parser = subparsers.add_parser("login", help="log in to bilibili")
    login_parser.add_argument("username", help="your bilibili username")
    login_parser.add_argument("password", help="your bilibili password")
    login_parser.set_defaults(func=login_handle)
    
    cookies_parser = subparsers.add_parser("cookies", help="set cookies to bilibili")
    cookies_parser.add_argument("cookies", help="your bilibili cookies")
    cookies_parser.set_defaults(func=cookies_handle)

    userinfo_parser = subparsers.add_parser("userinfo", help="get userinfo")
    userinfo_parser.set_defaults(func=userinfo_handle)
    
    upload_parser = subparsers.add_parser("upload", help="upload a file")
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
    
    info_parser = subparsers.add_parser("info", help="show meta info")
    info_parser.add_argument("meta", help="meta url")
    info_parser.set_defaults(func=info_handle)
    history_parser = subparsers.add_parser("history", help="show upload history")
    history_parser.set_defaults(func=history_handle)
    
    if len(sys.argv) != 1:
        args = parser.parse_args()
        args.func(args)
    else:
        interact_mode(parser, subparsers)

if __name__ == "__main__":
    main()
