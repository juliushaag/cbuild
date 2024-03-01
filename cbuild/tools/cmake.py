import abc
import os
from pathlib import Path
import shutil
from cbuild.compiler import Compiler, CompileResult, LibCompileResult
from cbuild.project import Target
from cbuild.processes import Program
from cbuild.log import log, success, panic
from cbuild.cache import CacheFile
from cbuild.util import hash_folder

class CMakeCompiler(Compiler):
  NAME="CMAKE"
  def __init__(self):
    super().__init__("cmake")

    self.compiler = Program("cmake")

    if self.compiler.is_valid(): self.is_valid = True


  def __call__(self, target : Target, res : CompileResult) -> CompileResult:

    bin_dir = target.root / target.get("bin_dir", "bin/") / target.name 
    folder = target.root / target.get("folder", ".")
    pub_includes = target.get("includes", [])
    pub_includes = [target.root / include for include in pub_includes]
    defines = [f"-D{key}={value}" for key, value in target.get("defines", {}).items()]

    cache = CacheFile(bin_dir / "cbuild.cache")

    hash_value = hash_folder(folder, exclude={".cache"})

    if hash_value in cache: 
      success(CMakeCompiler.NAME + " cached " + target.name)
      return LibCompileResult(**cache[hash_value])    

    shutil.rmtree(bin_dir)
    command = f"{" ".join(defines)} -B {bin_dir} -S {folder}"
    out, err, code = self.compiler(command)

    panic(code == 0, CMakeCompiler.NAME + " failed on " + target.name + " " + err)

    success(CMakeCompiler.NAME + " created " + target.name)

    out, err, code = self.compiler(f"--build {bin_dir}")

    static_lib = None
    for line in out.splitlines():
      if "->" not in line: continue
      static_lib = line.split("-> ")[1]

    assert static_lib

    cache[hash_value] = {
      "includes" : pub_includes,
      "static_lib" : static_lib
    }


    return LibCompileResult(pub_includes, static_lib)