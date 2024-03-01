from pathlib import Path
import re
import subprocess
from typing import Generator, Optional
from cbuild.compiler import CompileError, CompileResult, Compiler, ExeCompileResult, HeaderCompileResult, LibCompileResult, ObjCompileResult
from cbuild.log import panic, error, success
from cbuild.processes import Process, Program
from cbuild.project import Target
from glob import glob
import os
import time

class MSVCCompiler(Compiler):
  NAME = "MSVC"
  STD_LIBS = "kernel32.lib User32.lib gdi32.lib winspool.lib shell32.lib ole32.lib oleaut32.lib uuid.lib comdlg32.lib advapi32.lib msvcrt.lib".split(" ")
  def __init__(self):
    super().__init__(["c", "c++"])  
    self.compiler = Program("cl.exe")
    self.linker = Program("link.exe")
    self.lib = Program("lib.exe")
    self.is_valid = self.compiler.is_valid()

  
  def __call__(self, target : Target, res : LibCompileResult) -> CompileResult:
    assert target.type in self.type 
    #  CL [option...] file... [option | file]... [lib...] [@command-file] [/link link-opt...]
    args = ["/nologo",  "/D _CRT_SECURE_NO_WARNINGS", "/Z7", "/c","/Tc" if target.type == "c" else "/Tp"]
    includes = target.get("includes", [])
    sources = target.get("sources", []) 
    bin_dir = target.get("bin_dir", "bin/")
    kind = target.get("kind", None)



    if not os.path.isdir(target.root / bin_dir): os.mkdir(target.root / bin_dir)

    sources = sources if isinstance(sources, list) else [sources]
    includes = includes if isinstance(includes, list) else [includes]

    includes = [target.root / include for include in includes] + res.includes
    
    src_files = [file for source in sources for file in glob(source, root_dir=target.root, recursive=True)]

    success(MSVCCompiler.NAME + " compiles " + target.name)


    # TODO this is garbage 
    compiled_files = []


    start = time.monotonic()
    result : list[tuple[Process, Path]] = [self._compile_file_start(target.root, file, bin_dir, args, includes) for file in src_files]
    compiled = [self._compile_file_end(*end) for end in result]
    for i in compiled:
      if i.error(): return i
      compiled_files += [i.get_file()]
    print("Compiling the files took", time.monotonic() - start)

    if kind == "exe": 
      exe = self._compile_exe(compiled_files, res.static_lib, target.root / bin_dir, target.name)
      return exe
    
    elif kind == "lib":
      lib = self._compile_lib(compiled_files + res.static_lib, target.root / bin_dir, target.name)
      lib.includes = includes
      return lib
    
    elif kind == "header":
      return HeaderCompileResult(includes=includes)

    else: assert False
  
  def _compile_file_start(self, root : Path, file : str, bin_folder : Path, args : list[str], includes) -> tuple[Process, Path]:
    
    src_file = root / file
    includes = ["-I" + str(root / include) for include in includes] if includes is not None else []
    output_file = root / bin_folder / file.replace(".c", ".obj").replace("/", ".").replace("\\", ".")
    command = f"/Fo{output_file} {" ".join(args)} {src_file} {" ".join(includes)}"

    return (self.compiler.run_async(command), output_file)
  
  def _compile_file_end(self, process : Process, output_file : Path):

    out, err, code = process.wait()
    if code != 0: return self._parse_error(out.split("\n", 1)[1])
    
    print(f"{out.strip():20}")
    return ObjCompileResult(output_file)
  
  def _compile_exe(self, compiled, libs, out_path : Path, name : str) -> ExeCompileResult | CompileError:

    out_path = out_path / (name + ".exe")
    cmd = f"/debug /OUT:{str(out_path)} {" ".join([str(lib) for lib in libs])} {" ".join([str(comp) for comp in compiled])} {" ".join([str(lib) for lib in MSVCCompiler.STD_LIBS])}"
    out, err, code = self.linker(cmd)
  
    if code != 0: return self._parse_error(err + out)

    return ExeCompileResult(out_path)

  def _compile_lib(self, compiled, out_path : Path, name : str) -> LibCompileResult | CompileError:
    out_path = out_path / (name + ".lib")
    cmd = f"/nologo /OUT:{out_path} {" ".join([str(comp) for comp in compiled])}"
    out, err, code = self.lib(cmd)
    
    if code != 0: return self._parse_error(out)
    return LibCompileResult([], str(out_path))
  
  def _parse_error(self, error : str) -> CompileError:
    pattern = r'^(.+)\((\d+)\):\s+(.+)\s+(\w+):\s+(.+)$' 
    match = re.search(pattern, error)
    assert match is not None, error 
    return CompileError(Path(match.group(1)), int(match.group(2)), match.group(5), match.group(4))