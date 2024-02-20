from os import system
import re
from typing import Any, Optional, Self
from cbuild.project import Target


class Compiler:
  def __init__(self, target=list[str]) -> None: 
    self._target = target 
    self.is_valid = False

  @property
  def type(self) -> str:
    return self._target
  
  @property
  def target_type(self) -> str:
    return self._target
    
  def __repr__(self) -> str:
    return f"<{type(self).NAME}>"