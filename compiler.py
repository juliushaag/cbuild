from enum import Enum
from typing import Any

class CompilerArgs(Enum):
  WARN0 = 0
  WARN1 = 1
  WARN2 = 2
  WARN3 = 3
  WARN4 = 4


class CompiledFile:
  def __init__(self, type : str, bin_location : str, debug_location : str) -> None: 
    self._type = type
    self._bin_location = bin_location
    self._debug_location = debug_location

class Compiler:
  def __init__(self, type : str, cmd : str) -> None: 
    self._type = type
    self._cmd = cmd

    
  def activate(self): 
    pass

  @property
  def type(self) -> str:
    return self._type

  def __call__(self, *args: Any, **kwds: Any) -> Any:
    ...