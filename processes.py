import os
import pprint
import subprocess
from typing import Optional


def run_process(file, cmd : Optional[str] = None):
  try:
    cmd = [file] + cmd.split(" ") if cmd is not None else file
    out, err =  subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=os.environ).communicate()
    return out.decode(), err.decode(), True
  except FileNotFoundError:
    return None, None, False
  except Exception as e:
    return None, str(e), False
  