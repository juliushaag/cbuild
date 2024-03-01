from collections import deque
from pathlib import Path
from cbuild.compiler import CompileError, CompileResult, Compiler, ExeCompileResult, HeaderCompileResult, LibCompileResult, ObjCompileResult
from cbuild.log import panic, error, success
from cbuild.processes import Process, Program
from cbuild.project import Target
from glob import glob
import time
import os
import re

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
    args = ["/nologo", "/Z7"]
    includes = target.get("includes", [])
    sources = target.get("sources", []) 
    bin_dir = target.get("bin_dir", "bin/")
    kind = target.get("kind", None)
    defines = target.get("defines", [])
    debug = target.get("debug", False)

    if not os.path.isdir(target.root / bin_dir): os.mkdir(target.root / bin_dir)
    

    sources = sources if isinstance(sources, list) else [sources]
    includes = includes if isinstance(includes, list) else [includes]

    includes = [target.root / include for include in includes] + res.includes
    args = ["/D " + name for name in defines] + args

    
    if kind == "header": return HeaderCompileResult(includes=includes)

    # TODO this is garbage 
    compiled_files = []


    # Yeah this is a little scuffed due to early dispatch 
    start = time.monotonic()
    running : deque[tuple[Process, Path]] = deque([self._compile_file_start(target.root, file, bin_dir, args, includes) for source in sources for file in glob(source, root_dir=target.root, recursive=True)])
    finished = []

    success(MSVCCompiler.NAME + " compiles " + target.name)

    # polling the compile status
    while running and (element := running.pop()):
      process = element[0]
      if process.hash_finished():
        finished.append(self._compile_file_end(*element))
      else:
        running.append(element)

    for i in finished:
      if i.error(): return i
      compiled_files += [i.get_file()]

    if kind == "exe": 
      exe = self._compile_exe(compiled_files, res.static_lib, target.root / bin_dir, target.name)
      return exe
    
    elif kind == "lib":
      lib = self._compile_lib(compiled_files + res.static_lib, target.root / bin_dir, target.name)
      lib.includes = includes
      return lib
    
    else: assert False
  
  def _compile_file_start(self, root : Path, file : str, bin_folder : Path, args : list[str], includes) -> tuple[Process, Path]:
    
    src_file = root / file
    includes = ["-I" + str(root / include) for include in includes] if includes is not None else []
    output_file = root / bin_folder / file.replace(".c", ".obj").replace("/", ".").replace("\\", ".")
    command = f"{" ".join(args)} /c /Tc {src_file} {" ".join(includes)} /Fo{output_file}"
    return (self.compiler.run_async(command), output_file)
  
  def _compile_file_end(self, process : Process, output_file : Path):

    out, err, code = process.wait()
    if code != 0: 
      return self._parse_error(out.split("\n", 1)[1])
    
    print(out.strip())
    return ObjCompileResult(output_file)
  
  def _compile_exe(self, compiled, libs, out_path : Path, name : str) -> ExeCompileResult | CompileError:

    out_path = out_path / (name + ".exe")
    cmd = f"/nologo /debug /OUT:{str(out_path)} {" ".join([str(lib) for lib in libs])} {" ".join([str(comp) for comp in compiled])} {" ".join([str(lib) for lib in MSVCCompiler.STD_LIBS])}"
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