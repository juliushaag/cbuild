import json
import os
import shutil
import time
from typing import List, Self
from pathlib import Path
from cbuild.log import log
from cbuild.compiler import Compiler
from cbuild.processes import run_process


class MSVCCompiler(Compiler):
  def __init__(self):
    super().__init__("MSVC", "cl.exe")  

class ClangCompiler(Compiler):
  def __init__(self):
    super().__init__("CLANG", "clang.exe", version_cmd="--version")

class CMakeCompiler(Compiler):
  def __init__(self):
    super().__init__("CMAKE", "cmake.exe", version_cmd="--version")
  
class MSBuildCompiler(Compiler):
  def __init__(self):
    super().__init__("MSBuild", "msbuild.exe",  version_cmd="--version")

class VSInstallation():
  def __init__(self, name : str, path : Path, version : str, isPreview : str) -> None:
    self.name : str = name
    self.path : Path = path if isinstance(path, Path) else Path(path)
    self.version : str = [int(i) for i in version.split(".")]
    self.ispreview = isPreview
    self.is_activated = False

  def activate(self, platform = 'x86_amd64'): 

    assert not self.ispreview, "Preview envs can not be used at the moment"

    vcvarsPath = self.path / "VC/Auxiliary/Build/vcvarsall.bat"
    start = time.monotonic()
    out, err, success = run_process(vcvarsPath, f"{platform} 1>&2 && set") # why is this sometimes so slow also cache this 
    # TODO check err output 
    
    log(f"VCVARS took {time.monotonic() - start}")

    assert success, "Failed set up the environment"

    for line in out.splitlines():
      name = line.split("=")
      os.environ[name[0]] = name[1]

    self.is_activated = True

  def get_toolchain(self) -> List[Compiler]:
    assert self.is_activated, "Installation has to be activated before the compilers are queried"

    available = [clazz() for clazz in Compiler.__subclasses__()]
    compilers = [result for compiler in available if (result := compiler.test())]

    return compilers

  def parse_vs_installation(x): return VSInstallation(x["displayName"], Path(x["installationPath"]), x["installationVersion"], x["isPrerelease"])
  
  def find_installations() -> Self:
    # cache this in a file
    program_files_path = os.getenv("PROGRAMFILES(X86)")
    path = Path(program_files_path + "/Microsoft Visual Studio/Installer")
    if os.path.isdir(path):
      output, err, _ = run_process(path / 'vswhere', "-all -format json -utf8 -nocolor")
      # TODO what to do if call fails
      return [VSInstallation.parse_vs_installation(installation) for installation in json.loads(output)]
    return []