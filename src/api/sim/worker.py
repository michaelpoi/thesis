
from datetime import datetime

from sim.logger import Logger
from schemas.results import Move
from sim.move_converter import MoveConverter
import numpy as np
import logging

from metadrive.envs import MetaDriveEnv



class Worker:
    def __init__(self, scenario, pipe=None):
        self.scenario = scenario
        self.avs, self.humans = self.split_vehicles()
        self.env = None
        self.connection = None
        self.current_step = 0
        self.agent_ids = {}
        self.logger = Logger(self.scenario.id)
        self.pipe = pipe

    

    def generate_log_entry(self, move, info, tm, tr, to_transmit=False):

        agent_states = {
            agent_id: {
                "position": self.env.engine.agents[agent_id].position.tolist(),
                "velocity": self.env.engine.agents[agent_id].velocity.tolist(),
                "heading": self.env.engine.agents[agent_id].heading_theta,
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





    def get_json(self, state, status="ACTIVE"):
        message_body = {
            "scenario_id": self.scenario.id,
            "status": status,
            "step": self.current_step,
            "map": self.get_map(),
            "state": state
        }

        return message_body
    
    

    def consume_moves(self):

        # def recv(timeout=0.1):
        #     if self.pipe.poll(timeout):
        #         return self.pipe.recv()
        #     return None

        active = True
        

        while active:
            move = self.pipe.recv()

            # if not move:
            #     move = Move(scenario_id=self.scenario.id, vehicle_id=None, direction="KEEP_ALIVE", timestamp=None)
            response, active = self.process_move(move)
            self.pipe.send(response)
    

    def process_finish(self, state, status="FINISHED"):
        logging.info(f"Scenario {self.scenario.id} finished at step {self.current_step}")

        state = self.get_json(state, status=status)

        if status == "FINISHED":
            self.logger.save()
            self.env.close()

        return state
        # TODO: Could be refactored



        
    def process_move(self, move: Move):
        move_arr = MoveConverter.convert(move)
        if move.direction == "KEEP_ALIVE":
            ego_agent_id = None
        
        else:
            ego_agent_id = self.agent_ids[move.vehicle_id]

        step = {}
        for agent_id in self.agent_ids.values():
            if agent_id and agent_id == ego_agent_id:
                step[agent_id] = move_arr

            else:
                step[agent_id] = np.array([0,0])


        
            try:
                obs, reward, tm, tr, info = self.env.step(step)
            except KeyError:
                logging.warning("Catched KeyError")
                for agent_id in self.env.agents.keys():
                    if agent_id not in step:            # Weird Bug
                        step[agent_id] = np.array([0,0])

                obs, reward, tm, tr, info = self.env.step(step)
        

        state = self.generate_log_entry(move, info, tm, tr, True)
        state['time'] = move.timestamp


        if all(tm.get(agent_id, True) or tr.get(agent_id, True) for agent_id in self.agent_ids.values()):  # Strange Bug with MetaDrive
            logging.warning("All agents done")
            return self.process_finish(state), False
        elif ego_agent_id and (tm.get(ego_agent_id, True) or tr.get(ego_agent_id, True)):
            logging.warning(f"Agent {ego_agent_id} done")
            # if ego_agent_id in self.agent_ids.values():
            #     del self.agent_ids[ego_agent_id]
            return self.process_finish(state, "TERMINATED"), True
            

        self.current_step += 1

        return self.get_json(state), True
    
    def run(self):
        self.setup_env()
        self.setup_vehicle()
        self.consume_moves()



        