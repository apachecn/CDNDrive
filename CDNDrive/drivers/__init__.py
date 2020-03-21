from .BiliApi import BiliApi
from .BaijiaApi import BaijiaApi
from .CsdnApi import CsdnApi

drivers = {
    'bili': BiliApi(),
    'baijia': BaijiaApi(),
    'csdn': CsdnApi(),
}

prefixes = {
    'bdrive': 'bili',
    'bdex': 'bili',
    'bjdrive': 'baijia',
    'csdrive': 'csdn',
}