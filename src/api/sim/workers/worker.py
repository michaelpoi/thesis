from sim.workers.base_worker import BaseWorker
from schemas.results import Move
from sim.move_converter import MoveConverter

import numpy as np
import logging


class Worker(BaseWorker):
     def process_move(self, move: Move):
        move_arr = MoveConverter.convert(move)
        if move.direction == "KEEP_ALIVE":
            ego_agent_id = None
        
        else:
            ego_agent_id = self.agent_ids[move.vehicle_id]

        step = {}
        for agent_id in self.agent_ids.values():
            if ego_agent_id and agent_id == ego_agent_id:
                step[agent_id] = move_arr

            else:
                step[agent_id] = np.array([0,0])


        
        try:
            obs, reward, tm, tr, info = self.env.step(step)
        except KeyError:
            logging.warning(f"Catched KeyError - step: {step}, active agents: {self.env.agents.keys()}")
            for agent_id in self.env.agents.keys():
                if agent_id not in step:            # Weird Bug
                    step[agent_id] = np.array([0,0])

            obs, reward, tm, tr, info = self.env.step(step)
        

        state = self.generate_log_entry(info, tm, tr, True, move=move)
        state['time'] = move.timestamp


        if self.all_done(tm, tr):  # Strange Bug with MetaDrive
            logging.warning("All agents done")
            agent_info = info.get(ego_agent_id, None)
            return self.process_finish(state, agent_info), False
        elif self.ego_done(tm, tr, ego_agent_id):
            logging.warning(f"Agent {ego_agent_id} done")
            # if ego_agent_id in self.agent_ids.values():
            #     del self.agent_ids[ego_agent_id]
            return self.process_termination(state, ego_agent_id, info), True

        self.current_step += 1

        return self.get_json(state), True