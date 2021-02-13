<h1 align="center">CDNDrive = BiliDrive + SuperBed</h1>

<h4 align="center">☁️ 废墟之上，重建辉煌！ ☁️</h4>
<h4 align="center">☁️ 支持任意文件的全速上传与下载 ☁️</h4>

## Fork版本声明

- 仅做个人习惯方面的适配和修改，不处理任何issue

## 特色

- 轻量：无复杂依赖，资源占用少
- 自由：无文件格式与大小限制，无容量限制
- 安全：上传的文件需要通过生成的 META URL 才能访问，他人无法随意查看
- 稳定：带有分块校验与超时重试机制，在较差的网络环境中依然能确保文件的完整性
- 快速：支持多线程传输与断点续传，同时借助各个站点的 CDN 资源，能最大化地利用网络环境进行上传与下载

## 使用指南

### 安装

从源码安装：

```
pip install git+https://github.com/power12317/CDNDrive
```

### 登录

```
cdrive login [-h] site username password

site: 站点名称（见 -h）
username: 用户名
password: 密码
```

> 运行 cdrive 报错

```
$ cdrive
-bash: cdrive: command not found
```

解决方案: https://github.com/apachecn/CDNDrive/issues/7

### 设置 Cookie

```
cdrive cookies [-h] site cookies

site: 站点名称（见 -h）
cookies: Cookie
```

### 查看登录状态

```
cdrive userinfo [-h] site

site: 站点名称（见 -h）
```

### 上传

```
cdrive upload [-h] [-b BLOCK_SIZE] [-t THREAD] site file

site: 站点名称（见 -h）
file: 待上传的文件路径

-b BLOCK_SIZE: 分块大小(MB), 默认值为4
-t THREAD: 上传线程数, 默认值为4
```

上传完毕后，终端会打印一串 META URL 用于下载或分享，请妥善保管

### 下载

```
cdrive download [-h] [-f] [-t THREAD] meta [file]

meta: META URL (通常以 cdrive:// 开头)
file: 另存为新的文件名, 不指定则保存为上传时的文件名

-f: 覆盖已有文件
-t THREAD: 下载线程数, 默认值为8
```

下载完毕后会自动进行文件完整性校验，对于大文件该过程可能需要较长时间，若不愿等待可直接退出

### 查看文件元数据

```
cdrive info [-h] meta

meta: META URL
```

### 查看历史记录

```
cdrive history [-h]
```

## 技术实现

将任意文件分块编码为图片后上传至各个站点，对该操作逆序即可下载并还原文件

## 性能指标

### 测试文件

文件名：[Vmoe]Hatsune Miku「Magical Mirai 2017」[BDrip][1920x1080p][HEVC_YUV420p10_60fps_2FLAC_5.1ch&2.0ch_Chapter][Effect Subtitles].mkv

大小：14.5 GB (14918.37 MB)

分块：10 MB * 1492

META URL：`bdrive://d28784bff1086450a6c331fb322accccd382228e`

### 上传

地理位置：四川成都

运营商：教育网

上行速率：20 Mbps

用时：02:16:39

平均速度：1.82 MB/s

### 下载

### 测试点1

地理位置：福建福州

运营商：中国电信

下行速率：100 Mbps

用时：00:18:15

平均速度：13.62 MB/s

### 测试点2

地理位置：上海

运营商：中国电信

下行速率：1 Gbps

用时：00:02:22

平均速度：104.97 MB/s

## 历史记录

[见这里](history.md)。

## 免责声明

+   请自行对重要文件做好本地备份。
+   请不要上传含有个人隐私的文件，因为无法删除。
+   请勿使用本项目上传不符合社会主义核心价值观的文件。
+   请合理使用本项目，避免对哔哩哔哩的存储与带宽资源造成无意义的浪费。
+   sogou有效期仅24小时，请勿上传用于长期储存的文件。
+   该项目仅用于学习和技术交流，开发者不承担任何由使用者的行为带来的法律责任。

## 协议

本项目基于 SATA 协议发布。

您有义务为此开源项目点赞，并考虑额外给予作者适当的奖励。

## 致谢

本项目基于 [Hsury](https://github.com/Hsury) 的 [BiliDrive](https://github.com/Hsury/BiliDrive)，在此表示感谢。

同时感谢 [goocarder](https://v2ex.com/t/618064) 提供的思路。

## 赞助我们

![](https://home.apachecn.org/img/about/donate.jpg)

## 另见

+   [ApacheCN 学习资源](https://docs.apachecn.org/)
+   [计算机电子书](http://it-ebooks.flygon.net)
+   [布客新知](http://flygon.net/ixinzhi/)
