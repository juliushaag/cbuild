import time
from cbuild.compiler import CompileResult, Compiler
from cbuild.log import log, error
from cbuild.processes import Program
from cbuild.vstoolchain import VSInstallation
from cbuild.project import Project, Target

def _tree(target:Target):
  if len(target._dependencies) == 0: return [f"━━ {target.name}"]
  lines = [f"━┳ {target.name}"]
  childs = [_tree(c) for c in target._dependencies]
  for c in childs[:-1]: lines += [" ┣" + c[0]] + [" ┃" + l for l in c[1:]]
  return lines + [" ┗"+childs[-1][0]] + ["  "+l for l in childs[-1][1:]]

def print_tree(target:Target): 
  for i,s in enumerate(_tree(target)): print(f"{i} {s}")

glob_start = start = time.monotonic()

# step one find compilers :)
installations : list[VSInstallation] = VSInstallation.find_installations()
installation = installations[0]
installation.activate()


log(f"Loaded toolchain in {time.monotonic() - start}s")
start = time.monotonic()

project = Project(".")

log(f"Loaded project in {time.monotonic() - start}s")
start = time.monotonic()

Compiler.Init()

target = project.get_start_target()


def compile_target(target : Target) -> CompileResult:
  result = CompileResult()
  for child in target._dependencies:
    res = compile_target(child)
    if res.error(): return res
    result += res

  return Compiler.Compile(target, result)
  
result = compile_target(target)

if result.error():
  error(result)

print_tree(target)
  

print("Execution ", target.name, "took", time.monotonic() - glob_start, "seconds")
print("=>", result.executable[0])