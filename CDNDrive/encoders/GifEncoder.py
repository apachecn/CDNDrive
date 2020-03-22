import sys
import struct
import math
from PIL import Image
from io import BytesIO

class GifEncoder:

    def __init__(self):
        self.minw = 10
        self.minh = 10

    def encode(self, data):
        data = struct.pack('<I', len(data)) + data

        minsz = self.minw * self.minh
        if len(data) < minsz:
            data += b'\0' * (minsz - len(data))
            
        side = math.ceil(math.sqrt(len(data)))
        total = side * side
        if len(data) < total:
            data += b'\0' * (total - len(data))
            
        img = Image.frombytes('L', (side, side), data)
        bio = BytesIO()
        img.save(bio, 'gif', optimize=False)
        return bio.getvalue()

    def decode(self, data):
        img = Image.open(BytesIO(data))
        data = img.tobytes()
        
        sz = struct.unpack('<I', data[:4])[0]
        data = data[4:4+sz]
        return data

def main():
    op = sys.argv[1]
    if op not in ['d', 'e']: return
    fname = sys.argv[2]
    data = open(fname, 'rb').read()
    encoder = GifEncoder()
    if op == 'e':
        data = encoder.encode(data)
        fname = fname + '.gif'
    else:
        data = encoder.decode(data)
        fname = fname + '.data'
    
    with open(fname, 'wb') as f:
        f.write(data)
        
if __name__ == '__main__': main()