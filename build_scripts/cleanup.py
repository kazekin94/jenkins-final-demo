#!/usr/bin/python3
import os

#clean workspace
def cleanup(path):
    try:
        if os.path.exists(path):
            os.rmdir(path)
        else:
            print('First deployment')
    except OSError as e:
        print("Error: %s : %s" % (dir_path, e.strerror))


if __name__ == "__main__":
    work_dir='/home/ec2-user/app'
    #calls
    cleanup(work_dir) 
