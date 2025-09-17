

from schemas.offline import OfflineScenarioPreview
from metadrive.envs.metadrive_env import MetaDriveEnv
import logging






class Subworker:
    def __init__(self, scenario, curr_x, curr_y, curr_v, curr_h):
        self.scenario = scenario
        self.env = None
        self.connection = None
        self.curr_x = curr_x
        self.curr_y = curr_y
        self.curr_v = curr_v
        self.curr_h = curr_h
        self.state = {  # To not change frontend
            'positions':{
                'agent0': {
                    'position':[curr_x, curr_y],
                    'heading': curr_h
                }
            }
        }

        




    def get_vehicle_config(self):
        return dict(
            show_dest_mark = True,

        )


    def setup_env(self):
        config = {
            "use_render": False,
            "traffic_density": 0.,
            "map": self.scenario.map.layout,
            "vehicle_config": self.get_vehicle_config(),
            "out_of_road_done": False,
            "horizon": self.scenario.steps,
            "truncate_as_terminate": True,
        }
        self.env = MetaDriveEnv(config=config)
        self.env.reset()

    

    def setup_vehicle(self, x, y, v, h):
        ego_vehicle = self.env.agent
        ego_vehicle.set_position([x, y])
        ego_vehicle.set_velocity([v, 0])
        ego_vehicle.set_heading_theta(h)


    
    def get_json(self, trajectory):
        message_body = {
            "scenario_id": self.scenario.id,
            "status": "PREVIEW",
            "map": {},
            "state": self.state,
            "trajectory": trajectory
        }

        return message_body
    



    def process_move(self, move: OfflineScenarioPreview):
        trajectory = []
        for mv in move.moves:
            move_arr = [mv.steering, mv.acceleration]
            for s in range(mv.steps):
                logging.info(f"Step {s}")
                obj, reward, tm, tr, info = self.env.step(move_arr)

                x, y = self.env.agent.position
                trajectory.append([x, y])
                logging.warning(info)

        
        return self.get_json(trajectory)


    def run(self, move, queue=None):
        self.setup_env()
        self.setup_vehicle(self.curr_x, self.curr_y, self.curr_v, self.curr_h)
        state = self.process_move(move)

        if queue:
            queue.put(state)

        return state




