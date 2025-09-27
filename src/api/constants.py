class Constants:
    class RealTime:
        MOVE_ACCELERATION_SENSITIVITY = 0.3 # [0,1]
        MOVE_STEERING_SENSITIVITY = 0.15 # [0,1]

        WS_MOVE_TIMEOUT = 0.1 # If frontend does not submit move during this => emits KEEP ALIVE


