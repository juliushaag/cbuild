import os
import time
from cbuild.log import log
from cbuild.vstoolchain import VSInstallation
from cbuild.project import Project, Target
import subprocess



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
installation = installations[0]
installation.activate()
toolchain = installation.get_toolchain()

print("Toolchain: ", toolchain)

log(f"Loaded toolchain in {time.monotonic() - start}s")
start = time.monotonic()

project = Project(".")

log(f"Loaded project in {time.monotonic() - start}s")
start = time.monotonic()

target = project.get_start_target()
for tar in reversed(target.get_dependency_list()):
  
  type = tar.type

  for tool in toolchain:
    if type == tool.type:
      tool(tar)