
from datetime import datetime

from sim.logger import Logger
from schemas.results import Move
from sim.move_converter import MoveConverter
import numpy as np

from metadrive.envs import MetaDriveEnv



class Worker:
    def __init__(self, scenario):
        self.scenario = scenario
        self.avs, self.humans = self.split_vehicles()
        self.env = None
        self.connection = None
        self.current_step = 0
        self.agent_ids = {}
        self.logger = Logger(self.scenario.id)

    

    def generate_log_entry(self, move, info, tm, tr, to_transmit=False):

        agent_states = {
            agent_id: {
                "position": self.env.engine.agents[agent_id].position.tolist(),
                "velocity": self.env.engine.agents[agent_id].velocity.tolist(),
                "is_human": True,
            }
            for agent_id in self.env.engine.agents
        }

        for av_id, av_obj in self.env.engine.traffic_manager.spawned_objects.items():
            if av_id not in agent_states:
                agent_states[av_id] = {
                    "position": av_obj.position.tolist(),
                    "velocity": av_obj.velocity.tolist(),
                    "is_human": False
                }

        info = info if not to_transmit else {}

        return self.logger.add_entry(
            step_num=self.current_step,
            move_direction=move.direction,
            agent_states=agent_states,
            termination=tm,
            truncation=tr,
            info=info
        )


    def get_vehicle_config(self):
        return dict(
            show_dest_mark = True,

        )


    def split_vehicles(self):
        avs, humans = [], []
        for vehicle in self.scenario.vehicles:
            if vehicle.assigned_user_id is None:
                avs.append(vehicle)
            else:
                humans.append(vehicle)

        return avs, humans
    
    def get_map(self):
        lanes = {}
        for ind, lane in enumerate(self.env.engine.current_map.road_network.get_all_lanes()):
            xs, ys = zip(*lane.get_polyline())
            lanes[ind] = {}
            lanes[ind]['x'] = list(xs)
            lanes[ind]['y'] = list(ys)

        return lanes



    def setup_env(self, is_map_preview=False):
        config = {
            "use_render": False,
            "traffic_density": 0.,
            "map": self.scenario.map.layout,
            "vehicle_config": self.get_vehicle_config(),
            "out_of_road_done": False,
            "horizon": self.scenario.steps,
            "num_agents": len(self.humans),
            "truncate_as_terminate": False,
        }
        if not is_map_preview:
            from sim.multi_mixed_env import MultiPlayerEnv

            self.env = MultiPlayerEnv(config=config, avs=self.avs)
        else:
            config.pop('num_agents')
            self.env = MetaDriveEnv(config=config)
        self.env.reset()

        for human, agent_id in zip(self.humans, self.env.agents.keys()):
            self.agent_ids[human.id] = agent_id

    def setup_vehicle(self):
        for vehicle in self.humans:
            agent_id = self.agent_ids[vehicle.id]
            agent = self.env.engine.agents[agent_id]

            agent.set_position([vehicle.init_x, vehicle.init_y])
            agent.set_velocity([vehicle.init_speed, 0])





    def get_json(self, state):
        message_body = {
            "scenario_id": self.scenario.id,
            "status": "ACTIVE",
            "step": self.current_step,
            "map": self.get_map(),
            "state": state
        }

        return message_body




        
    def process_move(self, move: Move):
        move_arr = MoveConverter.convert(move)
        ego_agent_id = self.agent_ids[move.vehicle_id]
        step = {}
        for agent_id in self.agent_ids.values():
            if agent_id == ego_agent_id:
                step[agent_id] = move_arr

            else:
                step[agent_id] = np.array([0,0])



        obs, reward, tm, tr, info = self.env.step(step)

        state = self.generate_log_entry(move, info, tm, tr, True)
        state['time'] = move.timestamp


        if tm['__all__'] or tr['__all__'] or tm['agent0'] or tr['agent0']:
            pass

        self.current_step += 1

        return self.get_json(state)



        