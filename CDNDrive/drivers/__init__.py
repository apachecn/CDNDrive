from .BiliApi import BiliApi
from .BaijiaApi import BaijiaApi
from .CsdnApi import CsdnApi
from .SohuApi import SohuApi
from .JianApi import JianApi
from .WeiboApi import WeiboApi
from .AliApi import AliApi
from .NeteApi import NeteApi
from .OscApi import OscApi

drivers = {
    'bili': BiliApi(),
    'baijia': BaijiaApi(),
    'csdn': CsdnApi(),
    'sohu': SohuApi(),
    'jian': JianApi(),
    'weibo': WeiboApi(),
    'ali': AliApi(),
    '163': NeteApi(),
    'osc': OscApi(),
}

prefixes = {
    'bdrive': 'bili',
    'bdex': 'bili',
    'bjdrive': 'baijia',
    'csdrive': 'csdn',
    'shdrive': 'sohu',
    'jsdrive': 'jian',
    'wbdrive': 'weibo',
    'aldrive': 'ali',
    'nedrive': '163',
    'osdrive': 'osc',
}