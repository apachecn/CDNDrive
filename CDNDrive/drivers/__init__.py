from .BiliApi import BiliApi
from .BaijiaApi import BaijiaApi

drivers = {
    'bili': BiliApi(),
    'baijia': BaijiaApi(),
}

prefixes = {
    'bdrive': 'bili',
    'bdex': 'bili',
    'bjdrive': 'baijia',
}