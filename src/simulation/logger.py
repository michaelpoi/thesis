import os
import json
import numpy as np


class Logger:
    def __init__(self, scenario_id, prefix=None):
        self.scenario_id = scenario_id
        self.logs = []
        self.log_dir = "/app/logs"  # Change this if you want a different folder
        self.prefix = prefix
        os.makedirs(self.log_dir, exist_ok=True)

    def add_entry(self, step_num, move_direction, agent_states, termination, truncation, info):
        entry = {
            "step": step_num,
            "move": move_direction,
            "positions": agent_states,
            "termination": termination,
            "truncation": truncation,
            "info": info
        }
        self.logs.append(entry)

    def to_serializable(self, obj):
        if isinstance(obj, (np.integer, np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        elif isinstance(obj, (np.bool_)):
            return bool(obj)
        return obj

    def save(self):
        filename = f"scenario_{self.scenario_id}.json"
        filename = self.prefix + filename if self.prefix else filename
        log_path = os.path.join(self.log_dir, filename)
        with open(log_path, "w") as f:
            json.dump(self.logs, f, indent=2, default=self.to_serializable)