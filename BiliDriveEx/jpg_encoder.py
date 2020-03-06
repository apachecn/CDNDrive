# coding: utf-8

import sys
import struct
import math
from PIL import Image
from io import BytesIO

class JpgEncoder:

    def __init__(self):
        self.minw = 10
        self.minh = 10
        self.dep = 3
        self.mode = 'RGB'

    @staticmethod
    def extend_byte(bt):
        if not (type(bt) is int and 0 <= bt <= 255 or \
                type(bt) is bytes and len(bt) == 1):
            return b''
    
        if type(bt) is bytes:
            bt = bt[0]
            
        res = bytes([bt // 2 ** i % 2 * 255 for i in range(8)])
        return res

    @staticmethod
    def recover_byte(bts):
        if not (type(bts) is bytes and len(bts) == 8):
            return b''
            
        res = sum([b // 128 * 2 ** i for i, b in enumerate(bts)])
        return bytes([res])
        
    def encode(self, data):
        minw = self.minw
        minh = self.minh
        dep = self.dep
        mode = self.mode
    
        data = struct.pack('<I', len(data)) + data
        data = b''.join([JpgEncoder.extend_byte(bt) for bt in data])
        
        minsz = minw * minh * dep
        if len(data) < minsz:
            data += b'\0' * (minsz - len(data))
        
        side = math.ceil(math.sqrt(len(data) / dep))
        total = side * side * dep
        if len(data) < total:
            data += b'\0' * (total - len(data))
        
        img = Image.frombytes(mode, (side, side), data)
        bio = BytesIO()
        img.save(bio, 'jpeg', quality=100, subsampling=0)
        return bio.getvalue()
        
        
    def decode(self, data):
        img = Image.open(BytesIO(data))
        data = img.tobytes()
        
        data = b''.join([
            JpgEncoder.recover_byte(data[i:i+8]) 
            for i in range(0, len(data), 8)
        ])
        
        sz = struct.unpack('<I', data[:4])[0]
        data = data[4:4+sz]
        return data

def main():
    op = sys.argv[1]
    if op not in ['d', 'e']: return
    fname = sys.argv[2]
    data = open(fname, 'rb').read()
    encoder = JpgEncoder()
    if op == 'e':
        data = encoder.encode(data)
        fname = fname + '.jpg'
    else:
        data = encoder.decode(data)
        fname = fname + '.data'
    
    with open(fname, 'wb') as f:
        f.write(data)
        
if __name__ == '__main__': main()