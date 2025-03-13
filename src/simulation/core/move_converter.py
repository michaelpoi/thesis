import numpy as np

class MoveConverter:

    acceleration_delta = 0.3
    steering_delta = 0.3
    @classmethod
    def convert(cls, move):
        steering = 0
        acceleration = 0
        if move.direction == 'UP':
            acceleration += cls.acceleration_delta
        elif move.direction == 'DOWN':
            acceleration -= cls.acceleration_delta
        elif move.direction == 'LEFT':
            steering += cls.steering_delta
        elif move.direction == 'RIGHT':
            steering -= cls.steering_delta

        return np.array([steering, acceleration])


