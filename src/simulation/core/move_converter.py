import numpy as np

class MoveConverter:
    @staticmethod
    def convert(move):
        steering = 0
        acceleration = 0
        if move.direction == 'UP':
            acceleration += 1
        elif move.direction == 'DOWN':
            acceleration -= 1
        elif move.direction == 'LEFT':
            steering -= 1
        elif move.direction == 'RIGHT':
            steering += 1

        return np.array([steering, acceleration])


