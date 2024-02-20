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



class ClangCompiler(Compiler):
  NAME = "clang"
  def __init__(self):
    super().__init__("compiled")

class CMakeCompiler(Compiler):
  NAME="cmake"
  def __init__(self):
    super().__init__("cmake")

  def __call__(self, target : Target):
    assert self.type == target.type
    print(target)

  
class MSBuildCompiler(Compiler):
  NAME="msbuild"
  def __init__(self):
    super().__init__("msbuild")

class VSInstallation():
  def __init__(self, name : str, path : Path, version : str, isPreview : str) -> None:
    self.name : str = name
    self.path : Path = path if isinstance(path, Path) else Path(path)
    self.version : list[int] = [int(i) for i in version.split(".")]
    self.ispreview = isPreview
    self.is_activated = False

  def activate(self, platform = 'x86_amd64'): 

    assert not self.ispreview, "Preview envs can not be used at the moment"

    vcvars = Process(self.path / "VC/Auxiliary/Build/vcvarsall.bat")
    assert vcvars.is_valid(), "Failed set up the environment"
    
    out, err = vcvars(f"{platform} 1>&2 && set") # why is this sometimes so slow also cache this 
    # TODO check err output
    
 
    for line in out.splitlines():

      split = lambda list, sep: filter(None, list.split(sep) if sep in list else [list])

      line = line.split("=", 1)
      name, content = line[0], line[1]

      
      original = os.environ[name] if name in os.environ else ""
      original = split(original, ";")

      new_content = set(split(content, ";"))

      result = new_content.symmetric_difference(original)
      if len(result) > 0: os.environ[name] = content # just update new stuff

    self.is_activated = True

  def get_toolchain(self) -> list[Compiler]:
    assert self.is_activated, "Installation has to be activated before the compilers are queried"

    available = [clazz() for clazz in Compiler.__subclasses__()]
    compilers = [compiler for compiler in available if compiler.is_valid]

    return compilers

  def parse_vs_installation(x): return VSInstallation(x["displayName"], Path(x["installationPath"]), x["installationVersion"], x["isPrerelease"])
  
  def find_installations() -> Self:
    # cache this in a file
    program_files_path = os.getenv("PROGRAMFILES(X86)")
    vswhere = Process(program_files_path + "/Microsoft Visual Studio/Installer/vswhere.exe")
    if not vswhere.is_valid(): return []

    output, err = vswhere("-all -format json -utf8 -nocolor") # TODO what to do if call fails
    return [VSInstallation.parse_vs_installation(installation) for installation in json.loads(output)]