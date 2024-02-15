import os
from pathlib import Path
from dataclasses import dataclass
from typing import List
import yaml


from cbuild.log import warn, log, panic

class Target:

  def __init__(self, root : Path, name : str, type : str, data : dict[str, str]):
    self.root : str = root
    self.type : str = type
    self._data = data


  def __repr__(self) -> str:
    return f"<{type(self).__name__} of type {self.type:10} at {self.root}>"
  

class Project:
  def __init__(self, path : str = "."):
    self._files = {}
    self._settings = {}
    self._targets = {}
    self._variables = {}
    self._load(Path(path))


  def _load(self, path : Path):
    path = path.resolve()
    if path in self._files.keys(): return
    
    file = path / "project.yaml"
    if not os.path.isfile(file):
      print("[W] invalid include ", path)
      return 

    with open(file, "r") as fp:
      a = yaml.safe_load(fp.read()) or {}
      self._files[path] = a

      for key, element in a.items():
        # load imports
        if key == "import": 
          for i in element: self._load(path / i) 

        # load targets
        elif key[0] == "(" and key[-1] == ")":
          self._load_target(key[1:-1], element, file, path)

        # load variables
        elif key[0] == "$":
          self._load_variable(key[1:], element)

        # load setting
        else:
          self._load_setting(key, element)

  def __repr__(self) -> str:
    result = f"Project ({len(self._files)})\n"
    for target in self._targets.values(): result += f"\t{target}\n"
    return result

  def _get_attrib(self, node, name : str, default=None):
    if name in node: return node[name]
    return default

  def _load_target(self, name, content, file, path):
    if name in self._targets: print("[W] Target", name, "gets overwritten")
    panic("type" in content, f"({file}) {name} has no type specified e.g (type=lib/exe/cmake_lib/...)")
    self._targets[name] = Target(root=path, name=name, type=self._get_attrib(content, "type", None), data=content.items())
    
  def _load_variable(self, name, content):
    if name in self._targets: warn("Variable", name, "gets overwritten")
    self._variables[name] = content
    
  def _load_setting(self, name, content):
    if name in self._settings: warn("Setting ", name,"overwritten")
    self._settings[name] = content
    

if __name__ == "__main__":
  a = Project(".")
  print(a)