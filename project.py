from pathlib import Path
import yaml


class Project:

  def __init__(self, path : str):
    self._targets = {}
    self.files = {}
    self._variables = {}
    self._load(Path(path))


  def _load(self, path : Path):
    path = path.resolve()
    if path in self.files.keys(): return
    

    with open(path / "project.yaml", "r") as fp:
      a = yaml.safe_load(fp.read()) or {}
      self.files[path] = a


      for key, elements in a.items():
        
        # load imports
        if key == "import": 
          for i in elements: self._load(path / i) 

        # load targets
        if key[0] == "(" and key[-1] == ")":
          self._load_target(key[1:-1], elements)

        # load variables
        if key[0] == "$":
          self._load_variable(key[1:], elements)



  def _load_target(self, name, content):
    if name in self._targets.keys(): print("[W] Target", name, "gets overwritten")
    self._targets[name] = content
    print(self._targets)
    
  def _load_variable(self, name, content):
    if name in self._targets.keys(): print("[W] Variable", name, "gets overwritten")
    self._variables[name] = content
    print(self._variables)



a = Project(".")
print(a)