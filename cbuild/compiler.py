from os import system
import re
from typing import Any, Optional, Self
from cbuild.project import Target


class Compiler:
  instances = {}
  arch = ""
  def __init__(self, target=list[str]) -> None: 
    self._target = target 
    self.is_valid = False

  def Init(): 
    available = [clazz() for clazz in Compiler.__subclasses__()]
    Compiler.instances = { type(compiler) : compiler for compiler in available if compiler.is_valid }

  @property
  def type(self) -> str:
    return self._target
  
  @property
  def target_type(self) -> str:
    return self._target
    
  def __repr__(self) -> str:
    return f"<{type(self).NAME}>"
  
