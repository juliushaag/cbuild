from enum import Enum
from print_color import print as cprint



def log(msg : str):
  cprint(msg, tag="LOG", color="white", tag_color="blue")


def warn(msg : str):
  cprint(msg, tag="WARN", color="white", tag_color="yellow")

def panic(cond : bool, msg : str):
  if cond: return
  cprint(msg, tag="ERROR", color="white", tag_color="red")
  exit(1)

  