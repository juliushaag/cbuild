import os
import shutil
import subprocess
import tempfile
from typing import Any

class Program:
  def __init__(self, program):
    self.program = program

  def is_valid(self) -> bool:
    return shutil.which(self.program) or os.path.isfile(self.program)
  
  def run_static(self, args : str, cwd = None) -> "StaticProcess":
    cmd = [self.program] + (args.split(" ") if args is not None else [])
    stdout_file = tempfile.TemporaryFile()
    stderr_file = tempfile.TemporaryFile()
    link = subprocess.Popen(cmd, stdout=stdout_file, stderr=stderr_file, stdin=subprocess.DEVNULL, env=os.environ.copy(), universal_newlines=True, cwd=cwd)
    return StaticProcess(self, link, stdout_file, stderr_file)
  
  def run_dynamic(self, args : str, cwd = None) -> "DynamicProcess":
    cmd = [self.program] + (args.split(" ") if args is not None else [])
    link = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, env=os.environ.copy(), universal_newlines=True, cwd=cwd)
    return DynamicProcess(self, link)


class Process:
  def __init__(self, program : Program, link : subprocess.Popen) -> None:
    self.program = program
    self.link = link

  def has_finished(self) -> bool:
    return self.link.poll() is not None 

  def kill(self):
    self.link.kill()

  def return_code(self):
    return self.link.returncode
  
  def pid(self):
    return self.link.pid
  
  def args(self):
    return self.link.args

class StaticProcess(Process):

  def __init__(self, program: Program, link: subprocess.Popen, stdout: tempfile.TemporaryFile, stderr: tempfile.TemporaryFile) -> None:
    super().__init__(program, link)
    self.stdout : tempfile.TemporaryFile = stdout
    self.stderr : tempfile.TemporaryFile = stderr

  def wait(self) -> tuple[str, str]:
    self.link.wait()
    
    self.stdout.seek(0)
    self.stderr.seek(0)
    
    stdout = self.stdout.read().decode('utf-8') if self.stdout else ""
    stderr = self.stderr.read().decode('utf-8') if self.stderr else ""
    
    self.stdout.close()
    self.stderr.close()
    return stdout, stderr, self.return_code()

class DynamicProcess(Process):
  def __init__(self, program: Program, link: subprocess.Popen) -> None:
    super().__init__(program, link)
  
  def output(self):
    for stdout_line in iter(self.link.stdout.readline, ""):
      yield stdout_line
    
  def error(self):
    for stdout_line in iter(self.link.stderr.readline, ""):
      yield stdout_line

  def wait(self) -> int:
    return self.link.wait() 