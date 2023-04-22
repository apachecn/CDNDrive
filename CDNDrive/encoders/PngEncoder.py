import sys
import struct
import math
from PIL import Image
from io import BytesIO

class PngEncoder:

    def __init__(self):
        self.minw = 20
        self.minh = 20
        self.dep = 3
        self.mode = 'RGB'

    @staticmethod
    def bmp_header(data):
        return b"BM" \
            + struct.pack("<l", 14 + 40 + 8 + len(data)) \
            + b"\x00\x00" \
            + b"\x00\x00" \
            + b"\x3e\x00\x00\x00" \
            + b"\x28\x00\x00\x00" \
            + struct.pack("<l", len(data)) \
            + b"\x01\x00\x00\x00" \
            + b"\x01\x00" \
            + b"\x01\x00" \
            + b"\x00\x00\x00\x00" \
            + struct.pack("<l", math.ceil(len(data) / 8)) \
            + b"\x00\x00\x00\x00" \
            + b"\x00\x00\x00\x00" \
            + b"\x00\x00\x00\x00" \
            + b"\x00\x00\x00\x00" \
            + b"\x00\x00\x00\x00\xff\xff\xff\x00"

    def encode_bmp(self, data):
        return PngEncoder.bmp_header(data) + data
        
        
    def decode_bmp(self, data):
        return data[62:]
        
    
    def encode_png(self, data):    
        data = struct.pack('<I', len(data)) + data
        
        minsz = self.minw * self.minh * self.dep
        if len(data) < minsz:
            data += b'\0' * (minsz - len(data))
        
        side = math.ceil(math.sqrt(len(data) / self.dep))
        total = side * side * self.dep
        if len(data) < total:
            data += b'\0' * (total - len(data))
        
        img = Image.frombytes(self.mode, (side, side), data)
        bio = BytesIO()
        img.save(bio, 'png')
        return bio.getvalue()
    
    def decode_png(self, data):
        img = Image.open(BytesIO(data))
        data = img.tobytes()
        
        sz = struct.unpack('<I', data[:4])[0]
        data = data[4:4+sz]
        return data
    
    encode = encode_png
    
    def decode(self, data):
        if data[:4] == b'\x89PNG':
            return self.decode_png(data)
        elif data[:2] == b'BM':
            return self.decode_bmp(data)
        else: raise ValueError('unknown format')
    

def main():
    op = sys.argv[1]
    if op not in ['d', 'e']: return
    fname = sys.argv[2]
    data = open(fname, 'rb').read()
    encoder = PngEncoder()
    if op == 'e':
        data = encoder.encode(data)
        fname = fname + '.png'
    else:
        data = encoder.decode(data)
        fname = fname + '.data'
    
    with open(fname, 'wb') as f:
        f.write(data)
        
if __name__ == '__main__': main()