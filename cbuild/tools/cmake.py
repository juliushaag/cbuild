from pathlib import Path
from cbuild.compiler import Compiler
from cbuild.project import Target
from cbuild.processes import Process
from cbuild.log import log, success, panic
from cbuild.tools.msbuild import MSBuildCompiler

class CMakeCompiler(Compiler):
  NAME="CMAKE"
  def __init__(self):
    super().__init__("cmake")

    self.compiler = Process("cmake")

    if self.compiler.is_valid(): self.is_valid = True



  def __call__(self, target : Target):
    bin_dir = target.root / target.get("bin_dir", "bin/") / target.name 
    folder = target.root / target.get("folder", ".")
    defines = [f"-D{key}={value}" for key, value in target.get("defines", {}).items()] + ["-DCMAKE_BUILD_TYPE=Release"]


    command = f"{" ".join(defines)} --fresh -B {bin_dir} -S {folder}"
    log("cmake " + command)
    out, err, code = self.compiler(command)

    if code != 0:
      panic(False, CMakeCompiler.NAME + " failed on " + target.name)


    success(CMakeCompiler.NAME + " created " + target.name)

    out, err, code = self.compiler(f"--build {bin_dir} --clean-first")

    print(out + err, code)
    exit()