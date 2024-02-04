import json
import os
from pprint import pprint
from typing import Any, Self, Optional

from compiler import Compiler

from pathlib import Path
import re
from processes import run_process


class CLCompiler(Compiler):
  PATTERN = r"Version (\d+\.\d+\.\d+)"
  def __init__(self, version : str):
    super.__init__("MSVC", "cl")
    self.version = version

  def test() -> Optional[Self]: 
    out, err, success = run_process("cl")
    if success:
      matches = re.search(CLCompiler.PATTERN, err)
      return CLCompiler(matches.group(1))
    else: 
      return None
    
  def __repr__(self) -> str:
    return f"<CLCompiler version={self.version}>"
  
  def __call__(self, file) -> Any:
    



class ClangCompiler(Compiler):
  PATTERN = r"clang version (\d+\.\d+\.\d+)"
  def __init__(self, version : str):
    super.__init__("CLANG", "clang")
    self.version = version

  def test() -> Optional[Self]: 
    out, err, success = run_process("clang", "--version")
    if success:
      matches = re.search(ClangCompiler.PATTERN, out)
      return ClangCompiler(matches.group(1))
    else: 
      return None

  def __repr__(self) -> str:
    return f"<ClangCompiler version={self.version}>"


class VSInstallation():

  def __init__(self, name : str, path : Path, version : str, isPreview : str) -> None:
    self.name : str = name
    self.path : Path = path if isinstance(path, Path) else Path(path)
    self.version : str = [int(i) for i in version.split(".")]
    self.ispreview = isPreview
    self.is_activated = False

  def activate(self, platform = 'x86_amd64') -> CLCompiler: 
    if not self.ispreview:
      vcvarsPath = self.path / "VC/Auxiliary/Build/vcvarsall.bat"
      out, _, success = run_process(vcvarsPath, f"{platform} >nul 2> nul && set") # why is this sometimes so slow 

      env_lines = out.split("\r\n")
      for line in env_lines:
        if line == '': continue
        name = line.split("=")
        os.environ[name[0]] = name[1]
      self.is_activated = True
    else:
      print("Preview compilers can not be used at the moment")

  def get_compilers(self):
    assert self.is_activated, "Installation has to be activated before the compilers are queried"

    available = [CLCompiler.test, ClangCompiler.test]
    compilers = []
    for comp in available:
      result = comp()
      if result is not None: compilers += [result]

    return compilers

  def parse_vs_installation(x): return VSInstallation (x["displayName"], Path(x["installationPath"]), x["installationVersion"], x["isPrerelease"])
  
  def find_installations() -> Self:
    # cache this in a file
    program_files_path = os.getenv("PROGRAMFILES(X86)")
    path = Path(program_files_path + "/Microsoft Visual Studio/Installer")
    if os.path.isdir(path):
      output, err, _ = run_process((path / 'vswhere'), "-all -format json -utf8 -nocolor")
      # TODO what to do if call fails
      return [VSInstallation.parse_vs_installation(installation) for installation in json.loads(output)]
    return []