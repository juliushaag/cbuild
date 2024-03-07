from enum import Enum
from print_color import print as cprint

# This is crap
# 1. dont rely on print_color (unnecessary dependency)
# 2. Create a better interface 

def log(msg : str):
  cprint(msg, tag="LOG", color="white", tag_color="blue")

def success(msg : str):
  cprint(msg, tag="+", color="white", tag_color="green")

def warn(msg : str):
  cprint(msg, tag="WARN", color="white", tag_color="yellow")

def panic(cond : bool, msg : str):
  if cond: return
  cprint(msg, tag="ERROR", color="white", tag_color="red")
  exit(1)

def error(msg : str):
  cprint(msg, tag="ERROR", color="white", tag_color="red")
  exit(1)

  