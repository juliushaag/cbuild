# step one find compilers )
import os
from pathlib import Path
import processes
from vscompiler import VSInstallation
import time

start = time.monotonic()
installations = VSInstallation.find_installations()

for i in installations: 
  if i.name != "Visual Studio Community 2019":
    i.activate()
    a = i.get_compilers()
    print(a)


print(f"Took {time.monotonic() - start}s")