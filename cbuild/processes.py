import os
import shutil
import subprocess
from typing import Optional

def program_exists(file): return shutil.which(file) or os.path.isfile(file)
 
def run_process(file, cmd : Optional[str] = None):
  if not  program_exists(file): return None, None, False

  cmd = [file] + cmd.split(" ") if cmd is not None else file
  process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=os.environ, universal_newlines=True)
  out, err = process.communicate()
  return out, err, True

class Process:
  ...