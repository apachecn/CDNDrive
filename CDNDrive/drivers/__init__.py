from .BiliApi import BiliApi
from .BaijiaApi import BaijiaApi
from .CsdnApi import CsdnApi
from .SohuApi import SohuApi
from .JianApi import JianApi

drivers = {
    'bili': BiliApi(),
    'baijia': BaijiaApi(),
    'csdn': CsdnApi(),
    'sohu': SohuApi(),
    'jian': JianApi(),
}

prefixes = {
    'bdrive': 'bili',
    'bdex': 'bili',
    'bjdrive': 'baijia',
    'csdrive': 'csdn',
    'shdrive': 'sohu',
    'jsdrive': 'jian',
}