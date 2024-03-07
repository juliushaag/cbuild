from collections import deque
from pathlib import Path
import sys
from cbuild.compiler import CompileError, CompileErrorEntry, CompileResult, Compiler, ExeCompileResult, HeaderCompileResult, LibCompileResult, ObjCompileResult
from cbuild.log import panic, error, success
from cbuild.processes import Process, Program, StaticProcess
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
    sources = target.get("sources", []) 
    include_paths = target.get("includes", [])
    bin_dir = target.root / target.get("bin_dir", "bin/") / target.name
    kind = target.get("kind", None)
    defines = target.get("defines", [])
    debug = target.get("debug", False)

    # sources and includes
    sources = sources if isinstance(sources, list) else [sources]
    include_paths = include_paths if isinstance(include_paths, list) else [include_paths]
    include_paths = [target.root / i for i in include_paths] + res.includes

    
    # if its a header lib we can return here  
    if kind == "header": return HeaderCompileResult(includes=include_paths)

    # Compile arguments
    defines = ["/D " + name for name in defines]
    std_args = ["/nologo", "/c", "/Z7", "/EHsc"]
    include_args = ["-I" + str(include) for include in include_paths]
    args = std_args + defines + include_args

    # create bin dir if it does not exist
    os.makedirs(target.root / bin_dir, exist_ok=True)

    start = time.monotonic()

    compiled_pch : Path = ""
    compiled_files = []
    if pch_data := target.get("precompiled_header", None):
      source = Path(pch_data["source"])
      header = Path(pch_data["header"])
      force_include = "force_include" in pch_data and pch_data["force_include"]
      
      pch_args = args + [f"/Yc{header.name}", f"/Fp{bin_dir / source.with_suffix(".pch")}"]
      compiled, errors = self._compile_files(pch_args, target.root, [source], bin_dir)

      if errors.has_errors(): return errors

      pch_file = compiled[0]
      compiled_pch = pch_file.with_suffix(".obj")
      args += ([f"/FI{header}"] if force_include else []) + [f"/Yu{header}", f"/Fp{pch_file.with_suffix(".pch")}"]
        
    src_files = [Path(file) for source in sources for file in glob(source, root_dir=target.root, recursive=True)]

    compiled_files, errors = self._compile_files(args, target.root, src_files, bin_dir)

    if errors.has_errors(): return errors

    success(f"{MSVCCompiler.NAME} {time.monotonic() - start:.2} sec compiles {target.name}")

    if kind == "exe": 
      files = compiled_files + res.pch_files + res.static_lib + MSVCCompiler.STD_LIBS
      exe = self._compile_exe(files, bin_dir, target.name)
      return ExeCompileResult(exe)
    
    elif kind == "lib":
      lib = self._compile_lib(compiled_files + res.static_lib, bin_dir, target.name)
      lib.includes = include_paths
      if compiled_pch != "": lib.pch_files = [compiled_pch]
      return lib
    
    else: assert False

  def _compile_files(self, args : list[str], root : Path, files : list[Path], bin_folder : Path) -> tuple[list[Path], CompileError]:


    data : dict[int, Path]= {}
    running : deque[StaticProcess] = deque()
    command_args = " ".join(args) 

    for file in files:
      output_file : Path = bin_folder / file.with_suffix("")
      os.makedirs(Path(output_file).parent, exist_ok=True)
      command = command_args + f" /Fo{output_file.with_suffix(".obj")} {root / file}"
      process = self.compiler.run_static(command)
      running.appendleft(process)
      data[process.pid()] = output_file.with_suffix(".obj")

    print(f"\r[0/{len(files)}] compiling {str(root):50}", end = "\r")
    file_count = 0
    errors = CompileError()
    # polling the compile status
    while running and (process := running.popleft()):

      if not process.has_finished():
        running.append(process)
        continue

      file_count += 1
      out, _, code = process.wait()
      if code:
        del data[process.pid()]
        lines = list(reversed(out.splitlines()))
        for line in lines:
          file, entry = self._parse_error(line)
          if file is not None: errors.add_entry(file, entry)

      else:
        print(f"\r[{file_count}/{len(files)}] {out.strip():50}", end="\r") # would like line replacement (maybe replace this in the future)
        
    return list(data.values()), errors
  

  def _compile_exe(self, compiled, out_path : Path, name : str) -> ExeCompileResult | CompileError:
    out_path = out_path / (name + ".exe")
    cmd = f"/nologo /debug /OUT:{out_path} {" ".join([str(comp) for comp in compiled])}"
    
    out, _, code = self.linker.run_static(cmd).wait()

    if code:
      print(out)
      exit(1)

    return out_path

  def _compile_lib(self, compiled, out_path : Path, name : str) -> LibCompileResult | CompileError:
    out_path = out_path / (name + ".lib")
    cmd = f"/nologo /debug /OUT:{out_path} {" ".join([str(comp) for comp in compiled])}"
    out, _, code = self.lib.run_static(cmd).wait()
    
    if code:
      print(out)
      exit(1)

    return LibCompileResult([], str(out_path))
  
  def _parse_error(self, error: list[str]) -> CompileErrorEntry:

    compile_error_pattern = r'^(.+)\((\d+)\):\s+(.+)\s+(\w+):\s+(.+)$' 
    
    match = re.search(compile_error_pattern, error)
    if not match:
      return None, None
    
    return Path(match.group(1)), CompileErrorEntry(int(match.group(2)), match.group(4), match.group(5))