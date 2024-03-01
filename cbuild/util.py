
import asyncio
import os
from pathlib import Path
from typing import Any, Callable
import hashlib
import concurrent.futures

def hash_folder(folder : Path, hash_fn : Callable = hashlib.sha256, exclude = {}) -> str:

  hash = hashlib.sha256()
  files = [Path(root) / filename for root, _, files in os.walk(folder) for filename in files]
  
  for file in files:
    if file.suffix in exclude: continue
    with open(file, "rb") as fp:
        hash.update(fp.read())

  return hash.hexdigest()


