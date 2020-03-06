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
from BiliDriveEx import __version__
from BiliDriveEx.bilibili import Bilibili
from BiliDriveEx.encoder import Encoder
from BiliDriveEx.util import *

encoder = Encoder()
api = Bilibili()

def fetch_meta(s):
    if re.match(r"^bdex://[a-fA-F0-9]{40}$", s):
        full_meta = image_download(api.default_url(re.findall(r"[a-fA-F0-9]{40}", s)[0]))
    elif re.match(r"^bdrive://[a-fA-F0-9]{40}$", s):
        full_meta = image_download(
            api.default_url(re.findall(r"[a-fA-F0-9]{40}", s)[0]).replace('png', 'x-ms-bmp')
        )
    elif s.startswith("http://") or s.startswith("https://"):
        full_meta = image_download(s)
    else:
        return
    try:
        meta_dict = json.loads(encoder.decode(full_meta).decode("utf-8"))
        return meta_dict
    except:
        return


def login_handle(args):
    if api.login(username=args.username, password=args.password):
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

def upload_handle(args):
    def core(index, block):
        try:
            block_sha1 = calc_sha1(block)
            full_block = encoder.encode(block)
            full_block_sha1 = calc_sha1(full_block)
            url = api.exist(full_block_sha1)
            if url:
                log(f"分块{index + 1}/{block_num}上传完毕")
                block_dict[index] = {
                    'url': url,
                    'size': len(block),
                    'sha1': block_sha1,
                }
            else:
                # log(f"分块{index + 1}/{block_num}开始上传")
                for _ in range(10):
                    if terminate_flag.is_set():
                        return
                    response = api.image_upload(full_block)
                    if response:
                        if response['code'] == 0:
                            url = response['data']['image_url']
                            log(f"分块{index + 1}/{block_num}上传完毕")
                            block_dict[index] = {
                                'url': url,
                                'size': len(block),
                                'sha1': block_sha1,
                            }
                            return
                        elif response['code'] == -4:
                            terminate_flag.set()
                            log(f"分块{index + 1}/{block_num}第{_ + 1}次上传失败, 请重新登录")
                            return
                    log(f"分块{index + 1}/{block_num}第{_ + 1}次上传失败")
                else:
                    terminate_flag.set()
        except:
            terminate_flag.set()
            traceback.print_exc()
        finally:
            done_flag.release()

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
        log(f"META URL -> {api.meta_string(url)}")
        return url

    if not api.get_user_info():
        log("账号未登录，请先登录")
        return
        
    log(f"线程数: {args.thread}")
    done_flag = threading.Semaphore(0)
    terminate_flag = threading.Event()
    thread_pool = []
    block_dict = {}
    block_num = math.ceil(os.path.getsize(file_name) / (args.block_size * 1024 * 1024))
    for index, block in enumerate(read_in_chunk(file_name, size=args.block_size * 1024 * 1024)):
        if len(thread_pool) >= args.thread:
            done_flag.acquire()
        if not terminate_flag.is_set():
            thread_pool.append(threading.Thread(target=core, args=(index, block)))
            thread_pool[-1].start()
        else:
            log("已终止上传, 等待线程回收")
            break
    for thread in thread_pool:
        thread.join()
    if terminate_flag.is_set():
        return
    sha1 = calc_sha1(read_in_chunk(file_name))
    meta_dict = {
        'time': int(time.time()),
        'filename': os.path.basename(file_name),
        'size': os.path.getsize(file_name),
        'sha1': sha1,
        'block': [block_dict[i] for i in range(len(block_dict))],
    }
    meta = json.dumps(meta_dict, ensure_ascii=False).encode("utf-8")
    full_meta = encoder.encode(meta)
    for _ in range(10):
        response = api.image_upload(full_meta)
        if response and response['code'] == 0:
            url = response['data']['image_url']
            log("元数据上传完毕")
            log(f"{meta_dict['filename']} ({size_string(meta_dict['size'])}) 上传完毕, 用时{time.time() - start_time:.1f}秒, 平均速度{size_string(meta_dict['size'] / (time.time() - start_time))}/s")
            log(f"META URL -> {api.meta_string(url)}")
            write_history(first_4mb_sha1, meta_dict, url)
            return url
        log(f"元数据第{_ + 1}次上传失败")
    else:
        return

def download_handle(args):
    def core(index, block_dict):
        try:
            # log(f"分块{index + 1}/{len(meta_dict['block'])}开始下载")
            for _ in range(10):
                if terminate_flag.is_set():
                    return
                block = image_download(block_dict['url'])
                if block:
                    block = encoder.decode(block)
                    if calc_sha1(block) == block_dict['sha1']:
                        file_lock.acquire()
                        f.seek(block_offset(index))
                        f.write(block)
                        file_lock.release()
                        log(f"分块{index + 1}/{len(meta_dict['block'])}下载完毕")
                        return
                    else:
                        log(f"分块{index + 1}/{len(meta_dict['block'])}校验未通过")
                else:
                    log(f"分块{index + 1}/{len(meta_dict['block'])}第{_ + 1}次下载失败")
            else:
                terminate_flag.set()
        except:
            terminate_flag.set()
            traceback.print_exc()
        finally:
            done_flag.release()

    def block_offset(index):
        return sum(meta_dict['block'][i]['size'] for i in range(index))

    def is_overwritable(file_name):
        if args.force:
            return True
        else:
            return (input("文件已存在, 是否覆盖? [y/N] ") in ["y", "Y"])

    start_time = time.time()
    meta_dict = fetch_meta(args.meta)
    if meta_dict:
        file_name = args.file if args.file else meta_dict['filename']
        log(f"下载: {os.path.basename(file_name)} ({size_string(meta_dict['size'])}), 共有{len(meta_dict['block'])}个分块, 上传于{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(meta_dict['time']))}")
    else:
        log("元数据解析失败")
        return
    log(f"线程数: {args.thread}")
    download_block_list = []
    if os.path.exists(file_name):
        if os.path.getsize(file_name) == meta_dict['size'] and calc_sha1(read_in_chunk(file_name)) == meta_dict['sha1']:
            log("文件已存在, 且与服务器端内容一致")
            return file_name
        elif is_overwritable(file_name):
            with open(file_name, "rb") as f:
                for index, block_dict in enumerate(meta_dict['block']):
                    f.seek(block_offset(index))
                    if calc_sha1(f.read(block_dict['size'])) == block_dict['sha1']:
                        # log(f"分块{index + 1}/{len(meta_dict['block'])}校验通过")
                        pass
                    else:
                        # log(f"分块{index + 1}/{len(meta_dict['block'])}校验未通过")
                        download_block_list.append(index)
            log(f"{len(download_block_list)}/{len(meta_dict['block'])}个分块待下载")
        else:
            return
    else:
        download_block_list = list(range(len(meta_dict['block'])))
    done_flag = threading.Semaphore(0)
    terminate_flag = threading.Event()
    file_lock = threading.Lock()
    thread_pool = []
    with open(file_name, "r+b" if os.path.exists(file_name) else "wb") as f:
        for index in download_block_list:
            if len(thread_pool) >= args.thread:
                done_flag.acquire()
            if not terminate_flag.is_set():
                thread_pool.append(threading.Thread(target=core, args=(index, meta_dict['block'][index])))
                thread_pool[-1].start()
            else:
                log("已终止下载, 等待线程回收")
                break
        for thread in thread_pool:
            thread.join()
        if terminate_flag.is_set():
            return
        f.truncate(sum(block['size'] for block in meta_dict['block']))
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
        print("元数据解析失败")

def history_handle(args):
    history = read_history()
    if history:
        for index, meta_dict in enumerate(history.values()):
            prefix = f"[{index + 1}]"
            print(f"{prefix} {meta_dict['filename']} ({size_string(meta_dict['size'])}), 共有{len(meta_dict['block'])}个分块, 上传于{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(meta_dict['time']))}")
            print(f"{' ' * len(prefix)} META URL -> {api.meta_string(meta_dict['url'])}")
    else:
        print(f"暂无历史记录")

def main():
    signal.signal(signal.SIGINT, lambda signum, frame: os.kill(os.getpid(), 9))
    parser = argparse.ArgumentParser(prog="BiliDriveEx", description="Make Bilibili A Great Cloud Storage!", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-v", "--version", action="version", version=f"BiliDriveEx version: {__version__}")
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
    shell = False
    while True:
        if shell:
            args = shlex.split(input("BiliDriveEx > "))
            try:
                args = parser.parse_args(args)
                args.func(args)
            except:
                pass
        else:
            args = parser.parse_args()
            try:
                args.func(args)
                break
            except AttributeError as ex:
                traceback.print_exc(file=sys.stdout)
                shell = True
                subparsers.add_parser("help", help="show this help message").set_defaults(func=lambda _: parser.parse_args(["--help"]).func())
                subparsers.add_parser("version", help="show program's version number").set_defaults(func=lambda _: parser.parse_args(["--version"]).func())
                subparsers.add_parser("exit", help="exit program").set_defaults(func=lambda _: os._exit(0))
                parser.print_help()

if __name__ == "__main__":
    main()
