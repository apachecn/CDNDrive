from .PngEncoder import PngEncoder
from .GifEncoder import GifEncoder

encoders = {
    'bili': PngEncoder(),
    'baijia': PngEncoder(),
    'csdn': PngEncoder(),
    'sohu': PngEncoder(),
    'jian': PngEncoder(),
    'weibo': GifEncoder(),
    'ali': PngEncoder(),
    '163': PngEncoder(),
    'osc': PngEncoder(),
    'sogou': PngEncoder(),
}