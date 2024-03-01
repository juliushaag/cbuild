

import json
import os
from pathlib import Path
from typing import Any

class CacheJsonEncoder(json.JSONEncoder):
  def default(self, obj):
    return obj.as_posix() if isinstance(obj, Path) else super().default(obj)

class CacheFile:
  def __init__(self, file_path : Path) -> None:

    

    self.file = file_path if isinstance(file_path, Path) else Path(file_path)
    os.makedirs(self.file.parent, exist_ok=True)
    self.file.touch()
    
    with open(self.file, "r") as fp:
      self.content = json.loads(fp.read() or "{}")

  def __del__(self): 
    with open(self.file, "w") as fp:
      json.dump(self.content, fp=fp, indent=2, cls=CacheJsonEncoder)

  def __getitem__(self, key : str):
    if key not in self.content: return None
    return self.content[key]
  
  def __setitem__(self, key : str, value : Any):
    self.content[key] = value

  def __contains__(self, key : str):
    return key in self.content