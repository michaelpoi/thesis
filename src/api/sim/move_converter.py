import numpy as np
from constants import Constants

class MoveConverter:

    @classmethod
    def convert(cls, move):
        steering = 0
        acceleration = 0
        if move.direction == 'UP':
            acceleration += move.sens_acceleration
        elif move.direction == 'DOWN':
            acceleration -= move.sens_acceleration
        elif move.direction == 'LEFT':
            steering += move.sens_steering
        elif move.direction == 'RIGHT':
            steering -= move.sens_steering

        return np.array([steering, acceleration])


