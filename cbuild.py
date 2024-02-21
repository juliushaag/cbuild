import time
from cbuild.compiler import Compiler
from cbuild.log import log
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

start = time.monotonic()
toolchain = []

# step one find compilers :)
installations : VSInstallation = VSInstallation.find_installations()
installation = installations[1]
installation.activate()


log(f"Loaded toolchain in {time.monotonic() - start}s")
start = time.monotonic()

project = Project(".")

log(f"Loaded project in {time.monotonic() - start}s")
start = time.monotonic()

Compiler.Init()

target = project.get_start_target()
for tar in reversed(target.get_dependency_list()):
  
  type = tar.type

  for tool in Compiler.instances.values():
    if type in tool.type:
      tool(tar)
      break

  


print_tree(target)
  