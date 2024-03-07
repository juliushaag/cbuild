import abc
from dataclasses import dataclass, field
from os import system
from pathlib import Path
import re
from typing import Any, Optional, Self
from cbuild.project import Target


#
# All of these result classes are garbage and have to be replaced 
#

class CompileResult:
  def __init__(self, includes = [], static_lib  = [], executables = [], pch_files = []):
    self.includes = [includes] if isinstance(includes, str) else includes
    self.static_lib = [static_lib] if isinstance(static_lib, str) else static_lib
    self.executable = executables
    self.pch_files = pch_files

  def __add__(self, other : Self) -> "CompileResult":
    return CompileResult(self.includes + other.includes, self.static_lib + other.static_lib, pch_files=self.pch_files + other.pch_files)
  
  def error(self):
    return False
  
  def __repr__(self) -> str:
    return f"<CompileResult libs={self.static_lib}>"
  

class LibCompileResult(CompileResult):
  def __init__(self, includes: list[str], static_lib: list[str] | str):
    static_lib = [static_lib] if not isinstance(static_lib, list) else static_lib
    super().__init__(static_lib=static_lib, includes=includes)


class ExeCompileResult(CompileResult):
  def __init__(self, executables: Path):
    super().__init__(executables = [executables])

class HeaderCompileResult(CompileResult):
  def __init__(self, includes: list[Path]):
    super().__init__(includes=includes)  

class ObjCompileResult(CompileResult):
  def __init__(self, file):
    super().__init__()
    self.file = file

  def get_file(self) -> Path:
    return self.file

@dataclass(order=True)
class CompileErrorEntry:
  sort_index : int = field(init=False, repr=False)
  line : int
  code : str
  message : str 

  def __post_init__(self):
    self.sort_index = self.line
  
  def __repr__(self) -> str:
    return f"   line {self.line} : {self.code} {self.message})\n"

class CompileError(CompileResult):
  def __init__(self):
    self.files : dict[Path, CompileErrorEntry]= {}

  def add_entry(self, file : Path, entry : CompileErrorEntry):
    
    if file not in self.files:
      self.files[file] = [entry]

    else:
      self.files[file] += [entry]

  def add_error(self, file : Path, line : int, message : str, code : str):
    self.add_entry(file, CompileErrorEntry(line,code,message))

  def error(self):
    return True
  
  def has_errors(self):
    return len(self.files)
  

  def __repr__(self) -> str:
    message = ""
    for key, value in self.files.items():
      message = f"[{key}]\n"
      for error in reversed(sorted(value)):
        message += str(error)
    return message 

class Compiler(abc.ABC):
  instances : dict[type, Self] = {}
  arch = ""
  def __init__(self, target=list[str]) -> None: 
    self._target = target 
    self.is_valid = False

  @staticmethod
  def Init(): 
    available = [clazz() for clazz in Compiler.__subclasses__()]
    Compiler.instances = { type(compiler) : compiler for compiler in available if compiler.is_valid}

  @property
  def type(self) -> str:
    return self._target
  
  @property
  def target_type(self) -> str:
    return self._target
  
  @staticmethod
  def Compile(target : Target, result : CompileResult) -> CompileResult:
    for tool in Compiler.instances.values():
      if target.type in tool.type:
        result = tool(target, result)
        return result
    
      
    print("Could not compile", target, Compiler.instances)
    return CompileResult()
  
  @abc.abstractclassmethod
  def __call__(self, target : Target, res : CompileResult) -> CompileResult:
    pass

  
