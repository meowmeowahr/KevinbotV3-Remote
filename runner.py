#!/usr/bin/python

import os
from utils import is_pi

if __name__ == "__main__":
    os.system("python3 menu.py")
    if is_pi():
        print("Looks like something went wrong")
        # os.system("sudo shutdown now -r")
