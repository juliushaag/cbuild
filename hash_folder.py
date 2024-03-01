import hashlib
import os
from pathlib import Path
import time
from typing import Callable

def iterate(folder : Path, hash_fn : Callable[[str], int] = hashlib.sha256) -> str:
  
  hash = hashlib.sha256()
  files = [Path(root) / filename for root, _, files in os.walk(folder) for filename in files]
  
  for file in files:
    with open(file, "rb") as fp:
        hash.update(fp.read())

  return hash.hexdigest()

if __name__ == "__main__":
    start = time.monotonic()
    folder = "NeuralEngine/lib/glfw"
    print(folder, ":", iterate(folder)) 
    print("Took ", time.monotonic() - start, "s")