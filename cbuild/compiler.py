from os import system
import re
from typing import Any, Optional, Self
from cbuild.processes import run_process, program_exists
from cbuild.project import Target


class Compiler:
  PATTERN = r"(\b(\d+(\.\d+)*)\b)"
  def __init__(self, type : str, cmd : str, version_cmd : str = "") -> None: 
    self._type = type
    self._cmd = cmd
    self._version_cmd = version_cmd
    self._version = None

  @property
  def type(self) -> str:
    return self._type
  
  @property
  def version(self) -> str:
    return self._version

  def __call__(target : Target) -> Any:
    ...

  def test(self) -> Optional[Self]:
    out, err, success = run_process(self._cmd, self._version_cmd)

    if success and out:
      matches = re.search(Compiler.PATTERN, err + out)
      self._version = matches.group(1)
      return self
    else: 
      return None
    
  def __repr__(self) -> str:
    return f"<{type(self).__name__:16} version={self.version}>"