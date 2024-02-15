import os
import time
from cbuild.log import log
from cbuild.vstoolchain import VSInstallation
from cbuild.project import Project
import subprocess


start = time.monotonic()
toolchain = []

# step one find compilers :)
installations : VSInstallation = VSInstallation.find_installations()
installation = installations[1]
installation.activate()
toolchain = installation.get_toolchain()

print("Toolchain: ", toolchain)

log(f"Loaded toolchain in {time.monotonic() - start}s")
start = time.monotonic()

project = Project(".")

log(f"Loaded project in {time.monotonic() - start}s")
start = time.monotonic()

target = project.get_start_target()
print(target)


