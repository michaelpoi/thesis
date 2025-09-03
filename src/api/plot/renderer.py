import matplotlib.pyplot as plt
import mpld3

class Renderer:
    def __init__(self, state: dict):
        self.state = state

    def draw_plot(self):
        plt.figure(figsize=(10, 6))
        plt.title("Scenario State")
        plt.xlabel("X")
        plt.ylabel("Y")

        positions = self.state.get("positions", [])

        # Plot vehicles
        for agent in positions:
            x, y = positions[agent]["position"]
            plt.plot(x, y, 'bo')  # Blue dots for vehicles

        # Plot other elements as needed

        plt.grid(True)
        return plt.gcf()
    

    
    def get_html(self):
        return mpld3.fig_to_html(self.draw_plot())
    


    def get_dict(self):
        return mpld3.fig_to_dict(self.draw_plot())
    