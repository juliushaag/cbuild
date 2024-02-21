import json
import os
import time
from typing import Self
from pathlib import Path
from cbuild.log import log
from cbuild.compiler import Compiler
from cbuild.processes import Process
from cbuild.project import Target
from cbuild.tools.msvc import MSVCCompiler
from cbuild.tools.cmake import CMakeCompiler
from cbuild.tools.cmake import MSBuildCompiler
import cbuild


class ClangCompiler(Compiler):
  NAME = "clang"
  def __init__(self):
    super().__init__("compiled")
  

class VSInstallation():
  CACHE_FILE = "vscache.json" # Path(cbuild.CBUILD_INSTALL_DIR) / "cache
  def __init__(self, name : str, path : str, version : str, isPreview : str, update_date : str) -> None:
    self.name : str = name
    self.path : Path = Path(path)
    self.version : list[int] = [int(i) for i in version.split(".")]
    self.ispreview = isPreview
    self.is_activated = False
    
    self.update_data = update_date

    self.hash = self.name + self.update_data


  def __hash__(self) -> int:
    return self.hash


  def activate(self, platform = 'x64'):    

    assert not self.ispreview, "Preview envs can not be used at the moment"

    log(f"Initializing {self.name} {".".join([str(i) for i in self.version])}")

    cache = {}
    if os.path.isfile(VSInstallation.CACHE_FILE):
      with open(VSInstallation.CACHE_FILE, "r") as fp:
        content = fp.read()
        cache = json.loads(content) if content else {}

    conf_hash = self.hash + platform

    update_environ = {}
    if conf_hash not in cache:

      vcvars = Process(self.path / "VC/Auxiliary/Build/vcvarsall.bat")
      assert vcvars.is_valid(), "Failed set up the environment"
      
      out, err, code = vcvars(f"{platform} 1>&2 && set") # why is this sometimes so slow also cache this 
      # TODO check err output
    
      for line in out.splitlines():

        split = lambda list, sep: filter(None, list.split(sep) if sep in list else [list])

        line = line.split("=", 1)
        name, content = line[0], list(split(line[1], ";"))
        
        original = list(split(os.environ[name], ";")) if name in os.environ else []

        result = [element for element in content if element not in original]
        
        if len(result) > 0: continue
        
        update_environ[name] = result # just update new stuff
    else:
      update_environ = cache[conf_hash]

    for key, content in update_environ.items(): 
      os.environ[key] = ";".join([str(var) for var in content]) + (os.environ[key] if key in os.environ else "")

    cache[conf_hash] = update_environ # update cache

    with open(VSInstallation.CACHE_FILE, "w") as fp:
      json.dump(cache, fp=fp, indent=2)

    self.is_activated = True
    Compiler.arch = platform

  def parse_vs_installation(x): 
    return 
  
  def find_installations() -> Self:
    # cache this in a file
    program_files_path = os.getenv("PROGRAMFILES(X86)")
    vswhere = Process(program_files_path + "/Microsoft Visual Studio/Installer/vswhere.exe")
    if not vswhere.is_valid(): return []

    output, err, code = vswhere("-all -format json -utf8 -nocolor") # TODO what to do if call fails
    return [VSInstallation(x["displayName"], x["installationPath"], x["installationVersion"], x["isPrerelease"], x["updateDate"]) for x in json.loads(output)]