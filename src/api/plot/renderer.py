class Renderer:
    def __init__(self):
        self.is_map_sent = False
    


    def get_dict(self, state, map):

        return { 'positions': state['positions'], 'map': map}
    
    def get_rendering_data(self, state, time=None):
        return {
                    'plt': self.get_dict(state['state'], state['map']),
                    'time': time,
                    'alive': state['status'] == "ACTIVE",
                    'step': state.get('step', 0),
                    'agents_map': state.get('agents_map', {}),
                    'reason': state.get('reason', None),
                    'trajectory': state.get('trajectory', None),
                    'frames': state.get('frames', None)
                }
