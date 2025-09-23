import json
import shutil
from pathlib import Path
from settings import settings

class OfflineBlobAdapter:
    def __init__(self, dir: Path):
        self.dir = Path(dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.loaded: dict[int, int] = {}  # scenario_id -> latest turn

    def get_filename(self, scenario_id: int, turn: int) -> Path:
        return self.dir / str(scenario_id) / f"{turn}.json"

    def save_blob(self, scenario_id: int, response: dict) -> int:
        turn = self.loaded.get(scenario_id, 0) + 1
        self.loaded[scenario_id] = turn

        filename = self.get_filename(scenario_id, turn)
        filename.parent.mkdir(parents=True, exist_ok=True)
        with open(filename, "w") as f:
            json.dump(response, f)

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
        with open(filename, "r") as f:
            return json.load(f)

    def get_latest(self, scenario_id: int) -> tuple[dict, int] | None:
        latest = self.latest_turn(scenario_id)
        if latest is None:
            return None
        blob = self.get_by_turn(scenario_id, latest)
        return (blob, latest)

    def clear_all(self):
        if self.dir.exists():
            shutil.rmtree(self.dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.loaded.clear()

blob_adapter = OfflineBlobAdapter(settings.blobs_dir)
