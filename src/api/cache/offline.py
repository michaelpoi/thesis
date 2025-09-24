from pathlib import Path
from settings import settings
from cache.base import FileSystemCache

class OfflineBlobAdapter(FileSystemCache):
    
    def get_filename(self, scenario_id: int, turn: int) -> Path:
        return self.dir / str(scenario_id) / f"{turn}.json"

    def save_blob(self, scenario_id: int, response: dict) -> int:
        turn = self.loaded.get(scenario_id, 0) + 1
        self.loaded[scenario_id] = turn

        filename = self.get_filename(scenario_id, turn)
        filename.parent.mkdir(parents=True, exist_ok=True)
        self.write(filename, response)

        return turn  # useful if caller wants it

    def latest_turn(self, scenario_id: int) -> int | None:
        return self.loaded.get(scenario_id)

    def has_newer_than(self, scenario_id: int, turn: int) -> bool:
        latest = self.latest_turn(scenario_id)
        return latest is not None and latest > turn

    def get_by_turn(self, scenario_id: int, turn: int) -> dict | None:
        filename = self.get_filename(scenario_id, turn)
        if not filename.exists():
            return None
        return self.read(filename)

    def get_latest(self, scenario_id: int) -> tuple[dict, int] | None:
        latest = self.latest_turn(scenario_id)
        if latest is None:
            return None
        blob = self.get_by_turn(scenario_id, latest)
        return (blob, latest)


blob_adapter = OfflineBlobAdapter(settings.blobs_dir)
