from pathlib import Path
from typing import Any, Optional
from cbuild.compiler import Compiler
from cbuild.log import success
from cbuild.processes import Program
from cbuild.project import Target


class MSBuildCompiler(Compiler):
  NAME="msbuild"
  def __init__(self):
    super().__init__("msbuild")

    self.compiler = Program("msbuild")


    if self.compiler.is_valid(): self.is_valid = True


  def __call__(self, folder : str) -> Any:
    project_file = folder / "ALL_BUILD.vcxproj"
    command = f"{project_file} -detailedSummary:True"
    print(self.compiler(command)[0])
    out, err, code = self.compiler(command)

    if code == 0: success(MSBuildCompiler.NAME + "succeded on " + str(folder))