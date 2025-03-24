import asyncio
import base64
import io
import json
import os
from time import sleep
from metadrive.envs import MetaDriveEnv
import numpy as np
from schemas import OfflineScenarioPreview, DiscreteMove
from core.move_converter import MoveConverter
from PIL import Image
import aio_pika
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


class Worker:
    def __init__(self, scenario):
        self.rabbitmq_url = get_rabbitmq_url()
        self.scenario = scenario
        self.env = None
        self.connection = None
        self.current_step = 0

    async def get_connection(self):
        # # if not self.connection:
        # self.connection =

        return await aio_pika.connect_robust(url=get_rabbitmq_url())

    @property
    def move_queue_name(self):
        return f"offline_{self.scenario.id}"

    @property
    def results_queue_name(self):
        return f"offline_queue"


    def setup_env(self):
        config = {
            "use_render": False,
            "traffic_density": 0.1,
            "map": self.scenario.map.layout,
        }
        self.env = MetaDriveEnv(config=config)
        self.env.reset()

    def setup_vehicle(self, x, y, v):
        ego_vehicle = self.env.agent
        ego_vehicle.set_position([x, y])
        ego_vehicle.set_velocity([v, 0])




    async def send_frame(self, image_bytes):
        connection = await self.get_connection()
        async with connection:
            channel = await connection.channel()

            message_body = {
                "scenario_id": self.scenario.id,
                "status": "ACTIVE",
                "step": self.current_step,
                "image_bytes": base64.b64encode(image_bytes).decode("utf-8")  # Convert bytes to base64 string
            }

            message_data = json.dumps(message_body).encode("utf-8")

            await channel.default_exchange.publish(
                aio_pika.Message(body=message_data),
                routing_key=self.results_queue_name,
            )



    async def process_finish(self, info):
        connection = await self.get_connection()
        async with connection:
            channel = await connection.channel()

            message_body = {
                "scenario_id": self.scenario.id,
                "status": "FINISHED",
                "reason": get_termination_reason(info)
            }

            message_data = json.dumps(message_body).encode("utf-8")

            await channel.default_exchange.publish(
                aio_pika.Message(body=message_data),
                routing_key=self.results_queue_name,
            )

    async def send_current_frame(self):
        image = self.env.render(mode='topdown', window=False)

        bytes_io = io.BytesIO()
        img = Image.fromarray(image)
        img.save(bytes_io, format="PNG")
        image_bytes = bytes_io.getvalue()

        await self.send_frame(image_bytes)

    async def process_move(self, move: DiscreteMove):
        move_arr = np.array([move.steering, move.acceleration])
        obs, reward, tm, tr, info = self.env.step(move_arr)
        if tm:
            await self.process_finish(info)
            return False
        self.current_step += 1
        return True

    async def consume_moves(self):
        connection = await self.get_connection()
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(self.move_queue_name, durable=True)

            async for message in queue:
                async with message.process():
                    move_json = json.loads(message.body)
                    move = OfflineScenarioPreview(**move_json)
                    for move in move.moves:
                        await self.process_move(move.moves)
                        await self.send_current_frame()

    async def run(self):
        self.setup_env()
        ego_vehicle = self.scenario.vehicles[0]
        self.setup_vehicle(ego_vehicle.init_x, ego_vehicle.init_y, ego_vehicle.init_speed)
        await self.consume_moves()

    def map_preview(self):
        self.setup_env()
        m = draw_top_down_map(self.env.current_map)
        bytes_io = io.BytesIO()
        img = Image.fromarray(m)
        img.save(bytes_io, format="PNG")
        image_bytes = bytes_io.getvalue()

        files = {
            'image': ('file.png', image_bytes, 'image/png'),
        }

        response = requests.post(f"{os.getenv('API_URL')}/maps/{self.scenario.map.id}", files=files)

        print(response.json())

        return


    def work(self):
        logging.warn(f"Starting worker process {self.scenario.id}")
        asyncio.run(self.run())


