from metadrive.policy.idm_policy import IDMPolicy
from metadrive.envs.marl_envs import MultiAgentMetaDrive
from metadrive.manager import BaseManager
from metadrive.component.vehicle.vehicle_type import DefaultVehicle

class MovingExampleManager(BaseManager):

    def __init__(self, avs):
        self.avs = avs
        super().__init__()

    def before_step(self):
        for id, obj in self.spawned_objects.items():
            p = self.get_policy(id)
            obj.before_step(p.act())  # set action

    def reset(self):
        for av in self.avs:
            obj = self.spawn_object(DefaultVehicle,
                                    vehicle_config=dict(),
                                    position=(av.init_x, av.init_y),
                                    heading=0)
            obj.set_velocity([av.init_speed, 0])
            self.add_policy(obj.id, IDMPolicy, obj, self.generate_seed())

    def after_step(self):
        for obj in self.spawned_objects.values():
            obj.after_step()
        # if self.episode_step == 180:
        #     self.clear_objects(list(self.spawned_objects.keys()))


class MultiPlayerEnv(MultiAgentMetaDrive):

    def __init__(self, avs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.avs = avs


    def setup_engine(self):
        super(MultiPlayerEnv, self).setup_engine()
        self.engine.update_manager("traffic_manager", MovingExampleManager(self.avs))