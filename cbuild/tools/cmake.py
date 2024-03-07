import abc
import os
from pathlib import Path
import shutil
from cbuild.compiler import Compiler, CompileResult, LibCompileResult, CompileError
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
    folder = target.root / target.get("folder", "")
    includes = target.get("includes", [])
    defines = [f"-D{key}={value}" for key, value in target.get("defines", {}).items()]
    
    includes = includes if isinstance(includes, list) else [includes]    
    includes = [target.root / include for include in includes]

    cache = CacheFile(bin_dir / "cbuild.cache")

    hash_value = hash_folder(folder, exclude={".cache"})

    if hash_value in cache: 
      success(CMakeCompiler.NAME + " cached " + target.name)
      return LibCompileResult(**cache[hash_value])

    success(CMakeCompiler.NAME + " creating build files " + target.name)
    shutil.rmtree(bin_dir)
    process = self.compiler.run_dynamic(f"{" ".join(defines)} -B {bin_dir} -S {folder}")

    for message in process.output():
      print(message, end="") 

    return_code = process.wait()
    panic(return_code == 0, CMakeCompiler.NAME + " failed on " + target.name)



    success(CMakeCompiler.NAME + " building " + target.name)
    process = self.compiler.run_dynamic(f"--build {bin_dir}")

    static_lib = None
    for message in process.output():
      print(message, end="")
      if "->" in message and message.endswith(".lib\n"): 
        static_lib = message.split("-> ")[1].replace("\n", "")

    if not static_lib:
      return CompileError(folder, 0, "Failed to find a library to compile", 0)

    cache[hash_value] = {
      "includes" : includes,
      "static_lib" : static_lib
    }

    success(CMakeCompiler.NAME + " compiled " + static_lib)
    return LibCompileResult(includes, static_lib)