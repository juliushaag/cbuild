from pathlib import Path
from typing import Optional
from cbuild.compiler import Compiler
from cbuild.processes import Process
from cbuild.project import Target
from glob import glob
import os

class MSVCCompiler(Compiler):
  NAME = "MSVC"
  def __init__(self):
    super().__init__(["c", "c++"])  
    self.compiler = Process("cl.exe")
    self.is_valid = self.compiler.is_valid()

    self.std_libs = "kernel32.lib user32.lib gdi32.lib winspool.lib shell32.lib ole32.lib oleaut32.lib uuid.lib comdlg32.lib advapi32.lib"
    

  def __call__(self, target : Target):
    assert target.type in self.type 
    #  CL [option...] file... [option | file]... [lib...] [@command-file] [/link link-opt...]
    args = ["/nologo", "/c", "/Tc" if target.type == "c" else "/Tp"]
    includes = target.get("includes", [])
    sources = target.get("sources", []) 
    bin_dir = target.get("bin_dir", "bin/")


    if not os.path.isdir(target.root / bin_dir): os.mkdir(target.root / bin_dir)


    sources = sources if isinstance(sources, list) else [sources]
    includes = includes if isinstance(includes, list) else [includes]
    
    src_files = [file for source in sources for file in glob(source, root_dir=target.root, recursive=True)]

    for file in src_files:
      self.compile_file(target.root, file, bin_dir, args, includes)

  def compile_file(self, root : Path, file : str, bin_folder : Path, args : list[str], includes) -> Optional[Path]:
    

    src_file = root / file
    includes = ["-I" + str(root / include) for include in (includes + [])]
    output_file = root / bin_folder / file.replace(".c", ".obj")
    compiler_flags = args
    command = f"/Fo{output_file} {" ".join(compiler_flags)} {src_file} {" ".join(includes)}"

    out, err, code = self.compiler(command)
    # print(out, err)
