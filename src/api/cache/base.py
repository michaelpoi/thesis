from abc import ABC
from pathlib import Path
import json
import shutil

class FileSystemCache(ABC):
    def __init__(self, dir: Path):
        self.dir = Path(dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.loaded = {}

    def write(self, filename, content):
        with open(filename, "w") as f:
            json.dump(content, f)

    def read(self, filename):
        with open(filename, "r") as f:
            return json.load(f)
        
    def remove(self, filename):
        filename.unlink()
        
    def exists(self, key):
        return key in self.loaded
    
    def clear_all(self):
        if self.dir.exists():
            shutil.rmtree(self.dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.loaded.clear()
    
