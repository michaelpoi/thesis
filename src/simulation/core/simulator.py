from metadrive.envs import MetaDriveEnv
import numpy as np

class Simulator:
    def __init__(self, env: MetaDriveEnv, num_steps: int):
        self.env = env
        self.num_steps = num_steps
        self.unprocessed_moves = []

    async def simulate(self):
        while True:
            if self.unprocessed_moves:
                move = self.unprocessed_moves.pop(0)
                action = np.array([*move])
                obs, reward, done, info = self.env.step(action)

                if done:
                    self.env.reset()
                    break
