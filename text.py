import os
import zlib
import json


data = {}
def get_all_file(filepath):
    filelist=[]
    for root, dirnames, filenames in os.walk(filepath):
        for filename in filenames:
            filelist.append(os.path.join(root,filename))
            print(os.path.join(root,filename))
            data[os.path.join(root,filename)] = "233"
    return filelist
#
filelist = get_all_file(".")
# os.makedirs(".\\testpath\\Lib\\site-packages\\urllib3\\util\\")


s = json.dumps(data)

# t = zlib.compress(str.encode(s), zlib.Z_BEST_COMPRESSION)
# unt = zlib.decompress(t)
# st = json.loads(unt)
# print(type(st))

with open("shareDir.txt",'rb') as f:
    print(f.read())
    unt = zlib.decompress(f)
    s = json.loads(unt)
    print(s)


