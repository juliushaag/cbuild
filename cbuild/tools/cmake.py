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
    folder = target.root / target.get("folder", ".")
    pub_includes = target.get("includes", [])
    defines = [f"-D{key}={value}" for key, value in target.get("defines", {}).items()]
    
    if not isinstance(pub_includes, list):
      pub_includes = [pub_includes] 
    
    pub_includes = [target.root / include for include in pub_includes]

    cache = CacheFile(bin_dir / "cbuild.cache")

    hash_value = hash_folder(folder, exclude={".cache"})

    if hash_value in cache: 
      success(CMakeCompiler.NAME + " cached " + target.name)
      return LibCompileResult(**cache[hash_value])    

    success(CMakeCompiler.NAME + " creating build files " + target.name)
    shutil.rmtree(bin_dir)
    command = f"{" ".join(defines)} -B {bin_dir} -S {folder}"
    process = self.compiler.run_async(command)

    for message in process.output():
      print(message, end="")

    out, err, code = process.wait()
    panic(code == 0, CMakeCompiler.NAME + " failed on " + target.name + " " + err)



    success(CMakeCompiler.NAME + " building " + target.name)
    process = self.compiler.run_async(f"--build {bin_dir}")

    
    static_lib = None
    for message in process.output():
      print(message, end="")
      if "->" in message and message.endswith(".lib\n"): 
        static_lib = message.split("-> ")[1].replace("\n", "")

    _, _, code = process.wait()

    if not static_lib:
      return CompileError(folder, 0, "Failed to find a library to compile", 0)

    cache[hash_value] = {
      "includes" : pub_includes,
      "static_lib" : static_lib
    }

    
    success(CMakeCompiler.NAME + " compiled " + static_lib)


    return LibCompileResult(pub_includes, static_lib)