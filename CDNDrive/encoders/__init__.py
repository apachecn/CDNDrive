from .PngEncoder import PngEncoder
from .GifEncoder import GifEncoder
from .JpgCatEncoder import JpgCatEncoder

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
    'autohome': JpgCatEncoder(),
    'chaoxing': PngEncoder(),
}
