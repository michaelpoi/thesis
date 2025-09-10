import matplotlib.pyplot as plt
import mpld3

class Renderer:
    def __init__(self):
        self.history_coords = []
        self.is_map_sent = False

    def draw_plot(self,  state):
        plt.figure(figsize=(10, 6))
        plt.title("Scenario State")
        plt.xlabel("X")
        plt.ylabel("Y")

        positions = state.get("positions", [])

        map_obj = state.get('map', {})
        self.draw_map(map_obj)

        for xh, yh in self.history_coords:
            plt.plot(xh, yh, 'ro')  # Red dots for history

        # Plot vehicles
        for agent in positions:
            x, y = positions[agent]["position"]
            plt.plot(x, y, 'bo')  # Blue dots for vehicles
            self.history_coords.append((x, y))

        # Plot other elements as needed

        plt.grid(True)
        plt.gca().set_aspect('equal', adjustable='box')
        return plt.gcf()
    
    def draw_map(self, map_obj):
        for lane in map_obj.values():
            xs, ys = lane['x'], lane['y']
            plt.plot(xs, ys, color='gray', linewidth=1)

    

    
    def get_html(self):
        return mpld3.fig_to_html(self.draw_plot())
    


    # def get_dict(self, state):
    #     return mpld3.fig_to_dict(self.draw_plot(state))

    def get_dict(self, state, map):
        
        return { 'positions': state['positions'], 'map': map }
