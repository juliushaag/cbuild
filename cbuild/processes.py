import os
import shutil
import subprocess
from typing import Any



class Program:
  def __init__(self, program):
    self.program = program

  def is_valid(self) -> bool:
    return shutil.which(self.program) or os.path.isfile(self.program)
  
  def run(self, args : str = None, cwd=None) -> tuple[Any, Any, int]:
    return self.run_async(args, cwd = cwd).wait()
  
  def run_async(self, args : str, cwd = None) -> "Process":
    cmd = [self.program] + (args.split(" ") if args is not None else [])
    link = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=os.environ.copy(), universal_newlines=True, cwd=cwd)
    return Process(self, link, args=cmd)

  def __call__(self, args : str) -> tuple[Any, Any, int]:
    return self.run(args)
  

class Process:
  def __init__(self, program : Program, link : subprocess.Popen, args = []) -> None:
    self.program = program
    self.link = link
    self.args : list = args


  def wait(self, timeout=None) -> tuple[Any, Any, int]:
    return *self.link.communicate(timeout=timeout), self.link.returncode
  
  def hash_finished(self) -> bool:
    return self.link.poll() is not None

  def kill(self):
    self.link.kill()