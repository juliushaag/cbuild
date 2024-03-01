import abc
from dataclasses import dataclass
from os import system
from pathlib import Path
import re
from typing import Any, Optional, Self
from cbuild.project import Target

class CompileResult:
  def __init__(self, includes = [], static_lib  = [], executables = []):
    self.includes = includes
    self.static_lib = static_lib
    self.executable = executables

  def __add__(self, other : Self) -> "CompileResult":
    return CompileResult(self.includes + other.includes,self.static_lib + other.static_lib)
  
  def error(self):
    return False
  
  def __repr__(self) -> str:
    return f"<CompileResult libs={self.static_lib}>"
  

class LibCompileResult(CompileResult):
  def __init__(self, includes: list[str], static_lib: list[str] | str):
    static_lib = [static_lib] if not isinstance(static_lib, list) else static_lib
    super().__init__(includes = includes, static_lib = static_lib)

class ExeCompileResult(CompileResult):
  def __init__(self, executables: Path):
    super().__init__(executables = [executables])

class HeaderCompileResult(CompileResult):
  def __init__(self, includes: list[str]):
    super().__init__(includes, [], [])  

class ObjCompileResult(CompileResult):
  def __init__(self, file):
    super().__init__()
    self.file = file

  def get_file(self) -> str:
    return self.file

class CompileError(CompileResult):

  def __init__(self, path : Path, line : int, message : str, code : str):
    self.path = path
    self.line = line
    self.message = message
    self.error_code = code

  def error(self):
    return True
  

  def __repr__(self) -> str:
    return f"{self.path} : {self.line} : {self.error_code}\n{self.message}"



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

  
