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
  STD_LIBS = "kernel32.lib User32.lib gdi32.lib winspool.lib shell32.lib ole32.lib oleaut32.lib uuid.lib comdlg32.lib advapi32.lib opengl32.lib".split(" ")
  
  def __init__(self):
    super().__init__(["c", "c++"])  
    self.compiler = Program("cl.exe")
    self.linker = Program("link.exe")
    self.lib = Program("lib.exe")
    self.is_valid = self.compiler.is_valid()

  
  def __call__(self, target : Target, res : LibCompileResult) -> CompileResult:
    assert target.type in self.type 
    #  CL [option...] file... [option | file]... [lib...] [@command-file] [/link link-opt...]
    args = ["/nologo", "/c", "/Z7", "/EHsc", "/MDd"]
    sources = target.get("sources", []) 
    include_paths = target.get("includes", [])
    bin_dir = target.root / target.get("bin_dir", "bin/") / target.name
    kind = target.get("kind", None)
    defines = target.get("defines", [])
    debug = target.get("debug", False)

    sources = sources if isinstance(sources, list) else [sources]
    include_paths = include_paths if isinstance(include_paths, list) else [include_paths]
    include_paths = [str(target.root / i) for i in include_paths]
    includes = ["-I" + include for include in include_paths]
    includes += ["-I" + include for include in res.includes]

    args = ["/D " + name for name in defines] + args

    if not os.path.isdir(target.root / bin_dir): os.makedirs(target.root / bin_dir)
    
    if kind == "header": return HeaderCompileResult(includes=include_paths)

    success(MSVCCompiler.NAME + " compiles " + target.name)

    pch_files : list[tuple[str, str]] = res.pch_files

  
    compiled_files = []
    if pch_data := target.get("precompiled_header", None):
      source = pch_data["source"]
      header = Path(pch_data["header"]).name
      compiled = self._compile_pch(target.root, source, bin_dir, args, includes, header)
      pch_file = str(compiled.get_file())
      pch_files += [(header, pch_file)]
    
    for item in pch_files:
      args = ["/FI" + item[0], "/Yu" + item[0], "/Fp" + item[1]] + args

    # Yeah this is a little scuffed due to early dispatch 
    running : deque[tuple[Process, Path]] = deque([self._compile_file_start(target.root, file, bin_dir, args, includes) for source in sources for file in glob(source, root_dir=target.root, recursive=True)])
    finished = []


    # polling the compile status
    while running and (element := running.popleft()):
      process = element[0]
      if process.hash_finished():
        finished.append(self._compile_file_end(*element))
      else:
        running.append(element)

    for i in finished:
      if i.error(): return i
      compiled_files += [i.get_file()]

    if kind == "exe": 
      exe = self._compile_exe(compiled_files, res.static_lib, bin_dir, target.name)
      return exe
    
    elif kind == "lib":
      lib = self._compile_lib(compiled_files + res.static_lib, bin_dir, target.name)
      lib.includes = include_paths if isinstance(include_paths, list) else [include_paths] 
      lib.pch_files = pch_files
      return lib
    
    else: assert False
  
  def _compile_file_start(self, root : Path, file : str, bin_folder : Path, args : list[str], includes : list) -> tuple[Process, Path]:
    
    is_c = file.endswith(".c")

    type_switch = "/Tc" if is_c else "/Tp"
    output_file = file.replace(".c" if is_c else "cpp", ".obj")
    output_file = bin_folder / output_file.replace("/", ".").replace("\\", ".")
    
    src_file = root / file

    command = f"{" ".join(args)} {" ".join(includes)} /Fo{output_file} {type_switch} {src_file}"
    return (self.compiler.run_async(command), output_file)

  def _compile_file_end(self, process : Process, output_file : Path):
    out, err, code = process.wait()
    if code != 0: 
      split_str = out.split("\n", 1)
      error = self._parse_error(split_str[1])
      print(split_str)
      return error
    print(out.strip())
    return ObjCompileResult(output_file)
  
  def _compile_pch(self, root : Path, file : str, bin_folder : Path, args : list[str], includes : list, header : str):
    
   
    type_switch = "/Tp"
    output_file = bin_folder / file.replace(".cpp", ".pch").replace("/", ".").replace("\\", ".")

    src_file = root / file
    command = f"{" ".join(args)} {" ".join(includes)} /Yc{header} {type_switch} {src_file} /Fp{output_file}"
    out, err, code = self.compiler(command)

    if code != 0: 
      split_str = out.split("\n", 1)
      error = self._parse_error(split_str[1])
      print(split_str)
      return error
    
    print(out.strip())
    return ObjCompileResult(output_file)

  def _compile_exe(self, compiled, libs, out_path : Path, name : str) -> ExeCompileResult | CompileError:

    out_path = out_path / (name + ".exe")
    cmd = f"/nologo /debug /OUT:{str(out_path)} {" ".join([str(lib) for lib in libs + compiled])} {" ".join(MSVCCompiler.STD_LIBS)}"
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