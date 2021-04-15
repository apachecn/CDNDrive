from PIL import Image
import numpy as np
from io import BytesIO
import sys

class JpgCatEncoder:
    
    def __init__(self):
        pass
    
    def get_header(self):
        header = np.random.randint(0, 256, [100, 100], dtype=np.uint8)
        img = Image.fromarray(header, 'L')
        bio = BytesIO()
        img.save(bio, 'jpeg')
        return bio.getvalue()
    
    def encode(self, data):
        return self.get_header() + data
        
    def decode(self, img):
        pos = img.find(b'\xff\xd9')
        return b'' if pos == -1 else img[pos+2:]
        
if __name__ == '__main__':
    encoder = JpgCatEncoder()
    op = sys.argv[1]
    fname = sys.argv[2]
    data = open(fname, 'rb').read()
    if op == 'e':
        data = encoder.encode(data)
        open(fname + '.jpg', 'wb').write(data)
    elif op == 'd':
        data = encoder.decode(data)
        open(fname + '.data', 'wb').write(data)