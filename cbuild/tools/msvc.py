from pathlib import Path
from typing import Optional
from cbuild.compiler import Compiler
from cbuild.processes import Process
from cbuild.project import Target
from glob import glob

class MSVCCompiler(Compiler):
  NAME = "MSVC"
  def __init__(self):
    super().__init__(["c", "c++"])  
    self.compiler = Process("cl.exe")
    self.is_valid = self.compiler.is_valid()

    self.std_libs = "kernel32.lib user32.lib shell32.lib gdi32.lib"
    

  def __call__(self, target : Target):
    assert self.type == target.type
    #  CL [option...] file... [option | file]... [lib...] [@command-file] [/link link-opt...]
    args = ["/c", "/Tc" if target.type == "c" else "/Tp"]
    includes = target._data["includes"]
    sources = target._data["sources"]
    

  def compile_file(self, path, args : list[str], includes) -> Optional[Path]:
    cargs = args + [""]
    
