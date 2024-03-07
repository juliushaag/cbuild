import json
import os
import time
from typing import Self
from pathlib import Path
from cbuild.cache import CacheFile
from cbuild.log import log
from cbuild.compiler import Compiler
from cbuild.processes import Program
from cbuild.project import Target

from cbuild.tools.msvc import MSVCCompiler
from cbuild.tools.cmake import CMakeCompiler

from cbuild import CBUILD_INSTALL_DIR  

class VSInstallation():
  CACHE_FILE = Path(CBUILD_INSTALL_DIR) / "vswhere.ch"
  def __init__(self, name : str, path : str, version : str, isPreview : str, update_date : str) -> None:
    self.name : str = name
    self.path : Path = Path(path)
    self.version : list[int] = [int(i) for i in version.split(".")]
    self.ispreview = isPreview
    self.is_activated = False
    self.update_data = update_date
    self.hash = self.name + self.update_data

  def activate(self, platform = 'x64'):    

    assert not self.ispreview, "Preview envs can not be used at the moment"

    log(f"Initializing {self.name} {".".join([str(i) for i in self.version])}")

    cache = CacheFile(VSInstallation.CACHE_FILE)
    conf_hash = self.hash + platform

    update_environ = {}
    if conf_hash not in cache:
      vcvars = Program(self.path / "VC/Auxiliary/Build/vcvarsall.bat")
      assert vcvars.is_valid(), "Failed set up the environment"
      
      out, _, _ = vcvars.run_static(f"{platform} 1>&2 && set").wait()

      # TODO check err output
      for line in out.splitlines():
        split = lambda array, sep: filter(None, array.split(sep) if sep in array else [array])

        line = line.split("=", 1)
        name, content = line[0], list(split(line[1], ";"))
        
        original = list(split(os.environ[name], ";")) if name in os.environ else []

        result = [element for element in content if element not in original]
        
        if len(result) == 0: continue
        update_environ[name] = result # just update new stuff

    else:
      update_environ = cache[conf_hash]

    for key, content in update_environ.items(): 
      os.environ[key] = ";".join([str(var) for var in content]) + (os.environ[key] if key in os.environ else "")

    cache[conf_hash] = update_environ # update cache

    self.is_activated = True
    Compiler.arch = platform

  
  @staticmethod
  def find_installations() -> list["VSInstallation"]:
    # cache this in a file
    program_files_path : str = os.getenv("PROGRAMFILES(X86)") or ""
    vswhere = Program(program_files_path + "/Microsoft Visual Studio/Installer/vswhere.exe")
    if not vswhere.is_valid(): return []

    output, _, _ = vswhere.run_static("-all -format json -utf8 -nocolor").wait()

    return [VSInstallation(x["displayName"], x["installationPath"], x["installationVersion"], x["isPrerelease"], x["updateDate"]) for x in json.loads(output)]