from metadrive.envs import MetaDriveEnv
import pickle

class EnvManager:
    def __init__(self):
        self.envs = {}

    def get_env(self, scenario_id:int ):
        # with open(f'{scenario_id}.pkl', 'rb') as f:
        #     env = pickle.load(f)

        if scenario_id not in self.envs:
            return None

        return self.envs[scenario_id]


    def add_env(self, scenario_id:int, config: dict=None):
        if not config:
            config = {
                "use_render": False,
                "traffic_density": 0.1,
            }
        env = MetaDriveEnv(config=config)
        env.reset()
        # with open(f'{scenario_id}.pkl', 'wb') as f:
        #     f.write(pickle.dumps(env))

        self.envs[scenario_id] = env


    def remove_env(self, scenario_id:int):
        del self.envs[scenario_id]

env_manager = EnvManager()
