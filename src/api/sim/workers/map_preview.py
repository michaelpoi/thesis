from sim.workers.base_worker import BaseWorker


class MapPreviewWorker(BaseWorker):

    def run(self):
        self.setup_env(is_map_preview=True)
        self.pipe.send({'map': self.rendered_map})
