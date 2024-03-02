import time
from cbuild.compiler import CompileResult, Compiler
from cbuild.log import log, error
from cbuild.processes import Program
from cbuild.vstoolchain import VSInstallation
from cbuild.project import Project, Target

def _tree(target:Target):
  if len(target._dependencies) == 0: 
    return [f"━━ {target.name}"]
  lines = [f"━┳ {target.name}"]
  children = [_tree(c) for c in target._dependencies]
  for c in children[:-1]: 
    lines += [" ┣" + c[0]]
    lines += [" ┃" + l for l in c[1:]]

  lines += [" ┗" + children[-1][0]]
  lines += ["  " + line for line in children[-1][1:]]
  return lines 

def print_tree(target:Target): 
  for line in _tree(target): print(f" {line}")


def compile_target(target : Target) -> CompileResult:
  result = CompileResult()
  for child in target._dependencies:
    res = compile_target(child)
    if res.error(): return res
    result += res

  return Compiler.Compile(target, result)


def main():
  glob_start = time.monotonic()

  # step one find compilers :)
  installations : list[VSInstallation] = VSInstallation.find_installations()
  installation = installations[0]
  installation.activate()

  # Create project and determine start target
  project = Project(".")
  target = project.get_start_target()
  print_tree(target)
  start = time.monotonic()

  Compiler.Init()

    
  result = compile_target(target)

  if result.error():
    error(result)

  print("Execution ", target.name, "took", time.monotonic() - glob_start, "seconds")
  print("=>", result.executable[0], end="")