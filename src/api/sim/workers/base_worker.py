from sim.logger import Logger
from abc import ABC, abstractmethod
from sim.utils import get_termination_reason
import numpy as np
import logging

from metadrive.envs import MetaDriveEnv
from metadrive.type import MetaDriveType



class BaseWorker(ABC):
    def __init__(self, scenario, pipe=None):
        self.scenario = scenario
        self.avs, self.humans = self.split_vehicles()
        self.env = None
        self.connection = None
        self.current_step = 0
        self.agent_ids = {}
        self.logger = Logger(self.scenario.id)
        self.rendered_map = None
        self.pipe = pipe


    def get_agent_states(self):
        agent_states = {
            agent_id: {
                "position": self.env.engine.agents[agent_id].position.tolist(),
                "velocity": self.env.engine.agents[agent_id].velocity.tolist(),
                "heading": self.env.engine.agents[agent_id].heading_theta,
                'goal': self.get_agent_destination(agent_id),
                "is_human": True,
            }
            for agent_id in self.env.engine.agents
        }

        for av_id, av_obj in self.env.engine.traffic_manager.spawned_objects.items():
            if av_id not in agent_states:
                agent_states[av_id] = {
                    "position": av_obj.position.tolist(),
                    "velocity": av_obj.velocity.tolist(),
                    "heading": av_obj.heading_theta,
                    "is_human": False
                }

        return agent_states
    

    def get_agent_destination(self, agent_id):
        """
        Returns:
        {
            "point": (x, y),                     # goal point
            "region": {"center": (x, y), "length": L, "width": W}  # small box near goal
        }
        or None if not available.
        """
        agent = self.env.agents.get(agent_id)
        if agent is None:
            return None

        nav = getattr(agent, "navigation", None)
        if nav is None:
            return None

        # Try to get the final lane from navigation
        lane = getattr(nav, "final_lane", None)
        if lane is None:
            route = getattr(nav, "route", None)
            if route:
                lane = route[-1]

        if lane is None:
            return None

        # Goal point
        if hasattr(lane, "end"):
            gx, gy = lane.end
        elif hasattr(lane, "position") and hasattr(lane, "length"):
            gx, gy = lane.position(lane.length)  # fallback
        else:
            return None

        # Build a tiny rectangular "goal area" around that point
        lane_width = float(getattr(lane, "width", 3.5))
        lane_width *= 3
        goal_box_len = 7.5 # meters along lane; tweak as you like
        region = {
            "center": (gx, gy),
            "length": goal_box_len,
            "width": lane_width,
        }

        return {"point": (gx, gy), "region": region}



    

    def generate_log_entry(self, info, tm, tr, to_transmit=False, move=None):

        entry = self.logger.add_entry(
            step_num=self.current_step,
            move_direction=move.direction if move else 'N/A',
            agent_states=self.get_agent_states(),
            termination=tm,
            truncation=tr,
            info=info
        )

        if to_transmit:
            entry_copy = {**entry}
            entry_copy.pop('info')
            return entry_copy


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
    
    def render_map(self, md_map):
        """
        Convert MetaDrive map to a minimal, styled JSON for the web renderer.
        Output schema:
        {
        "lane_width": <float>,
        "features": [
            { "kind": "lane" | "road_line" | "boundary_line",
            "polyline": [[x,y], ...],
            "style": { "width": <m> }                # for lanes
            # or
            "style": { "color": "#FFFFFF|#FFD400",
                        "pattern": "solid|dashed",
                        "line_width": <m> }           # for lines
            },
            ...
        ]
        }
    """
        line_sample_interval = 2
        all_feats = md_map.get_map_features(line_sample_interval)

        # lane width & stripe width
        lane_width = float(md_map.config.get("lane_width", 3.5))
        try:
            from metadrive.component.map.base_map import LaneGraphics
            stripe_width = float(getattr(LaneGraphics, "STRIPE_WIDTH", 0.15))
        except Exception:
            stripe_width = 0.15

        def color_hex(is_yellow: bool) -> str:
            return "#FFD400" if is_yellow else "#FFFFFF"

        out_map = {
            "lane_width": lane_width,
            "features": []
        }

        for _, obj in all_feats.items():
            md_type = obj.get("type")
            poly = obj.get("polyline", [])
            if poly is None or len(poly) < 2:
                continue

            # keep MetaDrive (x,y) order; cast to float
            poly_xy = [[float(x), float(y)] for (x, y) in poly]

            if MetaDriveType.is_lane(md_type):
                out_map["features"].append({
                    "kind": "lane",
                    "polyline": poly_xy,
                    "style": { "width": lane_width }
                })

            elif MetaDriveType.is_road_line(md_type) or MetaDriveType.is_road_boundary_line(md_type):
                is_yellow = MetaDriveType.is_yellow_line(md_type)
                is_solid  = MetaDriveType.is_solid_line(md_type)
                out_map["features"].append({
                    "kind": "road_line" if MetaDriveType.is_road_line(md_type) else "boundary_line",
                    "polyline": poly_xy,
                    "style": {
                        "color": color_hex(is_yellow),
                        "pattern": "solid" if is_solid else "dashed",
                        "line_width": stripe_width
                    }
                })

            # else: ignore other types

        return out_map

    



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
            "allow_respawn": False,
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

        self.rendered_map = self.render_map(self.env.current_map)



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
            "map": self.rendered_map,
            "agents_map": self.agent_ids,
            "state": state
        }

        return message_body
    
    

    def consume_moves(self):
        active = True
        
        while active:
            move = self.pipe.recv()

            response, active = self.process_move(move)
            self.pipe.send(response)

    def all_done(self, tm, tr):
        return all(tm.get(agent_id, True) or tr.get(agent_id, True) for agent_id in self.agent_ids.values())
    
    def ego_done(self, tm, tr, ego_agent_id):
        return ego_agent_id and (tm.get(ego_agent_id, True) or tr.get(ego_agent_id, True))
    
    def get_dones(self, tm, tr):
        return [(vid, aid) for (vid, aid) in self.agent_ids.items() if tm.get(aid, True) or tr.get(aid, True)]
    

    def process_finish(self, state, agent_info):
        logging.info(f"Scenario {self.scenario.id} finished at step {self.current_step}")

        state = self.get_json(state, status="FINISHED")
        if agent_info:
            state['reason'] = get_termination_reason(agent_info)
            
        self.logger.save()
        self.env.close()

        return state
        

    def process_termination(self, state, agent_id, info):
        state = self.get_json(state, status="TERMINATED")
        reason = get_termination_reason(info.get(agent_id, {}))
        state['reason'] = reason
        logging.info(f"Scenario {self.scenario.id}: agent {agent_id} terminated at step {self.current_step} due to {reason}")
        return state



    
    def run(self):
        self.setup_env()
        self.setup_vehicle()
        self.consume_moves()


    @abstractmethod
    def process_move(self, move) -> tuple[dict, bool]:
        '''
        Process move in a loop and return a tuple (response, active)
        '''
        raise NotImplementedError("Implement in subclass")



        