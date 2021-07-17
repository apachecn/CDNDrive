import os

def get_all_file(filepath):
    filelist=[]
    for root, dirnames, filenames in os.walk(filepath):
        for filename in filenames:
            filelist.append(os.path.join(root,filename))
            print(os.path.join(root,filename))
    return filelist

get_all_file(".\\")
os.makedirs(".\\testpath\\Lib\\site-packages\\urllib3\\util\\")
