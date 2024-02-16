import os
import shutil
import subprocess
  

class Process:
  def __init__(self, program):
    self.program = program

  def is_valid(self) -> bool:
    return shutil.which(self.program) or os.path.isfile(self.program)
  
  def run(self, args : str) -> tuple[str, str]:
    cmd = [self.program] + (args.split(" ") if args is not None else [])
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=os.environ, universal_newlines=True)
    return process.communicate()

  def __call__(self, args : str) -> tuple[str, str]:
    return self.run(args)