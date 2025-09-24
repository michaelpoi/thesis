from cache.base import FileSystemCache
from settings import settings

class MapCache(FileSystemCache):

    def get_filename(self, map_id):
        return self.dir / f"{map_id}.json"
    
    def add_map(self, map_id, blob):
        self.loaded[map_id] = True
        self.write(self.get_filename(map_id), blob)

    def invalidate(self, map_id):
        self.loaded.pop(map_id, None)
        self.remove(self.get_filename(map_id))

    
    def get(self, map_id):
        if not self.exists(map_id):
            return None
        
        return self.read(self.get_filename(map_id))
    
map_cache = MapCache(settings.maps_dir)

