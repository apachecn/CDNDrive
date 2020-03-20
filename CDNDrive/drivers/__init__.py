from .BiliApi import BiliApi

drivers = {
    'bili': BiliApi,
}

drivers_by_prefix = {
    'bdrive': BiliApi,
    'bdex': BiliApi,
}