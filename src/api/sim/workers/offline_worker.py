from sim.workers.base_worker import BaseWorker
from schemas.offline import OfflineScenarioPreview
from typing import List
from sim.workers.subworker import Subworker
from multiprocessing import Process, Queue, set_start_method
from sim.utils import get_termination_reason

import logging

set_start_method("spawn", force=True)


class OfflineWorker(BaseWorker):

    def to_flat_view(self, moves: List[OfflineScenarioPreview]):
        flat = {}

        for move in moves:
            agent_id = self.agent_ids[move.vehicle_id]
            flat[agent_id] = {}
            curr = 0

            for dsm in move.moves:
                for step in range(dsm.steps):
                    flat[agent_id][curr + step] = [dsm.steering, dsm.acceleration]

                curr += dsm.steps


        return flat

    
    def preprocessor(self, data: dict) -> List[OfflineScenarioPreview]:
        steps = data["steps"]
        moves = [OfflineScenarioPreview(**move) for move in data["moves"]]
        return moves, steps
    
    def preview_preprocessor(self, data:dict):
        move = OfflineScenarioPreview(**data)
        return move
    
    def form_tm_info(self, dones, info):
        termination_info = {}
        logging.info(f"Dones: {dones}")
        for vid, aid in dones:
            reason = None
            if ainfo := info.get(aid, None):
                reason = get_termination_reason(ainfo)
            termination_info[vid] = reason
            self.agent_ids.pop(vid, None)

        return termination_info

    def process_move(self, data: dict):
        moves, steps = self.preprocessor(data)
        frames = []

        flat = self.to_flat_view(moves)

        state = None
        for step in range(steps):
            move = {}
            for agent_id in self.agent_ids.values():
                move[agent_id] = flat[agent_id][step]

            for aid in self.env.engine.agents.keys():
                if aid not in move:
                    move[aid] = [0.0, 0.0]

            obj, reward, tm, tr, info = self.env.step(move)

            state = self.generate_log_entry(info, tm, tr, True)
            


            if self.all_done(tm, tr):
                finish_state = self.process_finish(state, None) # Replace None later
                finish_state['frames'] = frames
                finish_state['tm_info'] = self.form_tm_info(self.get_dones(tm, tr), info)
                logging.warning(f"Finish tm info: {finish_state['tm_info']}")
                return finish_state, False
            elif dones := self.get_dones(tm, tr):
                state = self.get_json(state)
                state['frames'] = frames
                state['tm_info'] = self.form_tm_info(dones, info)
                return state, True

            frames.append(self.get_agent_states())


            self.current_step += 1

        if state:
            response = self.get_json(state)
        else:
            response = {}
        response['frames'] = frames
        return response, True
    

    def get_preview(self, move):
        agent_id = self.agent_ids[move.vehicle_id]
        agent = self.env.engine.agents[agent_id]
        x, y = agent.position
        speed = agent.speed
        heading = agent.heading_theta
        sub_worker = Subworker(self.scenario, x,y, speed, heading)

        queue = Queue()

        p = Process(target=sub_worker.run, args=(move, queue))

        p.start()
        p.join()

        state = queue.get()

        return state
    

    def process_preview(self, data: dict):
        move = self.preview_preprocessor(data)
        return self.get_preview(move)
    

    def consume_moves(self): #Overidden to handle preview

        self.logger.prefix = 'offline'
        
        active = True
        
        while active:
            move = self.pipe.recv()

            is_preview = move.pop('is_preview')

            if is_preview:
                response = self.process_preview(move)
            else:
                response, active = self.process_move(move)

            self.pipe.send(response)

        