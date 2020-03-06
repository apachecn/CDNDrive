#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-

import setuptools
import BiliDriveEx

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    install_requires = fh.read().splitlines()

setuptools.setup(
    name="BiliDriveEx",
    version=BiliDriveEx.__version__,
    url="https://github.com/apachecn/BiliDriveEx",
    author=BiliDriveEx.__author__,
    author_email=BiliDriveEx.__email__,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: SATA License",
        "Natural Language :: Chinese (Simplified)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Communications :: File Sharing",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Utilities",
    ],
    description="☁️ 哔哩哔哩云 Ex，支持任意文件的全速上传与下载",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=[
        "bilibili",
        "cloud",
        "disk",
        "drive",
        "storage",
        "pan",
        "yun",
        "B站",
        "哔哩哔哩",
        "网盘",
        "云",
    ],
    install_requires=install_requires,
    python_requires=">=3.6",
    entry_points={
        'console_scripts': [
            "BiliDriveEx=BiliDriveEx.__main__:main",
            "bdex=BiliDriveEx.__main__:main",
        ],
    },
    packages=setuptools.find_packages(),
)
