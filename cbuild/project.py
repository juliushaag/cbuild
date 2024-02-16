from functools import reduce
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Self
import yaml


from cbuild.log import warn, log, panic

class Target:

  def __init__(self, root : Path, name : str, type : str, data : dict[str, str]):
    self.root : Path = root
    self.name : str = name
    self.type : str = type
    self._data = data
    self._dependencies = []

  def add_dependency(self, target : Self):
    self._dependencies += [target]
  
  def file(self):
    return self.root / "project.yaml"

  def get_dependency_list(self):
    if len(self._dependencies) == 0: return [self]
    return reduce(lambda x, y: x + y, [c.get_dependency_list() for c in self._dependencies], [self])
    
  def __repr__(self) -> str:
    return f"<{self.name} of type {self.type} at {self.root}>"
   


class Project:
  def __init__(self, path : str = "."):
    self._files = {}
    self._settings = {}
    self._targets = {}
    self._variables = {}
    self._load(Path(path))
    self._resolve_dependencies()


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
          self._load_target(key, element, file, path)

        # load variables
        elif key[0] == "$":
          self._load_variable(key[1:], element)

        # load setting
        else:
          self._load_setting(key, element)

  def _load_target(self, name, content, file, path):
    if name in self._targets: print("[W] Target", name, "gets overwritten")
    panic("type" in content, f"({file}) {name} has no type specified e.g (type=c/c++/cmake...)")
    self._targets[name] = Target(root=path, name=name, type=content.get("type", None), data=content)
    
  def _load_variable(self, name, content):
    if name in self._targets: warn("Variable", name, "gets overwritten")
    self._variables[name] = content
    
  def _load_setting(self, name, content):
    if name in self._settings: warn("Setting ", name,"overwritten")
    self._settings[name] = content
  
  def _resolve_dependencies(self):
    for target in self._targets.values():
      dependencies = target._data.get("depends", [])
      if not isinstance(dependencies, list): dependencies = [dependencies] 
      
      for dependency in dependencies:
        panic(dependency in self._targets.keys(), f"({target.file()}) Could not find dependency {dependency}")
        target.add_dependency(self._targets[dependency])
    
    # TODO check for circular includes 
      
  def get_start_target(self):

    panic(len(self._targets) != 0, f"There are no targets declared")
    if "StartProject" in self._variables:
      name = self._variables["StartProject"]
      panic(name in self._targets.keys(), f"Specified start project {name} not specified")
      return self._targets[name]
    
    return list(self._targets.values())[0]


  def __repr__(self) -> str:
    result = f"Project ({len(self._files)})\n"
    for target in self._targets.values(): result += f"\t{target}\n"
    return result


if __name__ == "__main__":
  a = Project(".")
  print(a)