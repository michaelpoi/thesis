from multiprocessing import Pipe, Process
from sim.workers.offline_worker import OfflineWorker
from sim.workers.worker import Worker
from sim.workers.map_preview import MapPreviewWorker

class SimulationManager:
    def __init__(self, WorkerClass):
        self.processes = {}
        self.pipes = {}
        self.WorkerClass = WorkerClass

    def register_worker(self, scenario):
        if self.is_worker_registered(scenario.id):
            return
        par_conn, child_conn = Pipe()
        worker = self.WorkerClass(scenario, pipe=child_conn)
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
    
    def process_move(self, move, scenario_id=None):

        if not scenario_id:
            scenario_id = getattr(move, 'scenario_id')

        pipe = self.get_pipe(scenario_id)

        if not pipe:
            raise Exception("Scenario not registered")
        
        pipe.send(move)

        response = pipe.recv()

        if response['status'] == "FINISHED":
            self.unregister_worker(scenario_id)

        return response
    

def map_preview(scenario):
    par_conn, child_conn = Pipe()
    worker = MapPreviewWorker(scenario, pipe=child_conn)
    p = Process(target=worker.run)
    map_resp = par_conn.recv()
    p.join()
    return map_resp



    
manager = SimulationManager(Worker)

offline_manager = SimulationManager(OfflineWorker)


