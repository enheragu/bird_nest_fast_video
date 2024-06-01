#!/usr/bin/env python3
# encoding: utf-8

import sys
import os

from datetime import datetime

################################
#     Format Logging stuff     #
################################

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def log(msg = "", color = bcolors.ENDC):
    timetag = datetime.utcnow().strftime('%F %T.%f')[:-3]
    print(f"{color}[{timetag}] {msg}{bcolors.ENDC}")


def logCoolMessage(msg, color = bcolors.OKCYAN):
    min_len = len(msg) + 6
    print(f"{color}\n\n\n{'#'*min_len}\n#{' '*(min_len-2)}#\n#  {msg}  #\n#{' '*(min_len-2)}#\n{'#'*min_len}\n{bcolors.ENDC}")
