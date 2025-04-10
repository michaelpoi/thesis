import asyncio
import base64
import io

from metadrive.policy.idm_policy import IDMPolicy
from metadrive.component.vehicle.vehicle_type import DefaultVehicle
from schemas import OfflineScenarioPreview
from PIL import Image
import aio_pika

from metadrive.envs.metadrive_env import MetaDriveEnv
from utils import get_rabbitmq_url
import logging
import requests
from metadrive.utils.draw_top_down_map import draw_top_down_map


def get_termination_reason(info):

    tm_reasons = {
        0: 'arrive_dest',
        1: 'out_of_road',
        2: 'crash_vehicle',
        3: 'crash_object'
    }

    for key, value in tm_reasons.items():
        if info[value]:
            return key


class Subworker:
    def __init__(self, scenario, curr_x, curr_y, curr_v):
        self.rabbitmq_url = get_rabbitmq_url()
        self.scenario = scenario
        self.env = None
        self.connection = None
        self.current_step = 0
        self.curr_x = curr_x
        self.curr_y = curr_y
        self.curr_v = curr_v

    async def send_message(self, queue_name, body):
        connection = await aio_pika.connect_robust(url=self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            await channel.default_exchange.publish(
                aio_pika.Message(body=body),
                routing_key=queue_name,
            )


    def get_vehicle_config(self):
        return dict(
            show_dest_mark = True,

        )


    @property
    def results_queue_name(self):
        return f"offline_queue"

    def setup_env(self):
        config = {
            "use_render": False,
            "traffic_density": 0.,
            "map": self.scenario.map.layout,
            "vehicle_config": self.get_vehicle_config(),
            "out_of_road_done": False,
            "horizon": self.scenario.steps,
            "truncate_as_terminate": True,
        }
        self.env = MetaDriveEnv(config=config)
        self.env.reset()

    def setup_vehicle(self, x, y, v):
        ego_vehicle = self.env.agent
        ego_vehicle.set_position([x, y])
        ego_vehicle.set_velocity([v, 0])




    async def send_frame(self, image_bytes):
        await self.send_message(self.results_queue_name, image_bytes)
        logging.warning("Frame sent successfully")

    def generate_gif(self):
        filename = f"preview_{self.scenario.id}.gif"
        self.env.top_down_renderer.generate_gif(gif_name=filename)

        with open(filename, "rb") as f:
            gif_data = f.read()

        return gif_data




    async def process_move(self, move: OfflineScenarioPreview):
        for mv in move.moves:
            move_arr = [mv.steering, mv.acceleration]
            for s in range(mv.steps):
                logging.info(f"Step {s}")
                obj, reward, tm, tr, info = self.env.step(move_arr)
                self.env.render(mode='topdown', window=False, draw_target_vehicle_trajectory=True,screen_record=True)

        gif_data = self.generate_gif()
        await self.send_frame(gif_data)
        self.current_step += 1
        return True


    async def run(self, move):
        self.setup_env()
        self.setup_vehicle(self.curr_x, self.curr_y, self.curr_v)
        return await self.process_move(move)




    def work(self, move:OfflineScenarioPreview):
        logging.warning(f"Starting Preview Worker process {self.scenario.id}")
        asyncio.run(self.run(move))


