from sim.worker import Worker
from multiprocessing import Pipe, Process

class SimulationManager:
    def __init__(self):
        self.processes = {}
        self.pipes = {}

    def register_worker(self, scenario):
        if self.is_worker_registered(scenario.id):
            return
        par_conn, child_conn = Pipe()
        worker = Worker(scenario, pipe=child_conn)
        self.pipes[scenario.id] = par_conn

        p = Process(target=worker.run)
        self.processes[scenario.id] = p
        p.start()
        return worker

    def is_worker_registered(self, scenario_id):
        return scenario_id in self.processes
    
    def get_pipe(self, scenario_id):
        if scenario_id in self.pipes:
            return self.pipes[scenario_id]
        
        return None
    
    def unregister_worker(self, scenario_id):
        if not self.is_worker_registered(scenario_id):
            return
        
        self.processes[scenario_id].join()
        del self.processes[scenario_id]
        del self.pipes[scenario_id]
    
    def process_move(self, move):

        pipe = self.get_pipe(move.scenario_id)

        if not pipe:
            raise Exception("Scenario not registered")
        
        pipe.send(move)

        response = pipe.recv()

        if response['status'] == "FINISHED":
            self.unregister_worker(move.scenario_id)

        return response
    
manager = SimulationManager()


