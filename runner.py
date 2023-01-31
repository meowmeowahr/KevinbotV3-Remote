#!/usr/bin/python

import os
from utils import is_pi

if __name__ == "__main__":
    os.system("./menu.py")
    if is_pi():
        print("Looks like something went wrong\nRebooting Now")
        # os.system("sudo shutdown now -r")
