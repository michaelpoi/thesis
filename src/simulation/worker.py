import asyncio
import base64
import io
import json
import os
from MoveManager import MovingExampleEnv
from metadrive.policy.idm_policy import IDMPolicy
from metadrive.component.vehicle.vehicle_type import DefaultVehicle
from MoveManager import MovingExampleManager
from schemas import Move
from core.move_converter import MoveConverter
from PIL import Image
import aio_pika
from utils import get_rabbitmq_url
import logging
import requests
from metadrive.utils.draw_top_down_map import draw_top_down_map
from subworker import Subworker
from multiprocessing import Process


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
    def move_queue_name(self):
        return f"moves_{self.scenario.id}"

    @property
    def results_queue_name(self):
        return f"images_queue"

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
        self.env = MovingExampleEnv(config=config, avs=self.scenario.vehicles[1:])
        self.env.reset()

    def setup_vehicle(self, x, y, v):
        ego_vehicle = self.env.agent
        ego_vehicle.set_position([x, y])
        ego_vehicle.set_velocity([v, 0])


    def generate_gif(self):
        filename = f"{self.scenario.id}.gif"
        self.env.top_down_renderer.generate_gif(gif_name=filename)

        with open(filename, "rb") as f:
            gif_data = f.read()

        return base64.b64encode(gif_data).decode('utf-8')


    async def send_frame(self, image_bytes):
        message_body = {
            "scenario_id": self.scenario.id,
            "status": "ACTIVE",
            "step": self.current_step,
            "image_bytes": base64.b64encode(image_bytes).decode("utf-8")  # Convert bytes to base64 string
        }
        message_data = json.dumps(message_body).encode("utf-8")
        await self.send_message(self.results_queue_name, message_data)



    async def process_finish(self, info):
        message_body = {
            "scenario_id": self.scenario.id,
            "status": "FINISHED",
            "reason": get_termination_reason(info),
            "gif": self.generate_gif(),
        }
        message_data = json.dumps(message_body).encode("utf-8")
        await self.send_message(self.results_queue_name, message_data)
        logging.warning(f"Shutting down worker {self.scenario.id}")
        exit(0)

    async def process_move(self, move: Move):
        move_arr = MoveConverter.convert(move)
        obs, reward, tm, tr, info = self.env.step(move_arr)
        if tm:
            await self.process_finish(info)

        image = self.env.render(mode='topdown', window=False, screen_record=True)

        bytes_io = io.BytesIO()
        img = Image.fromarray(image)
        img.save(bytes_io, format="PNG")
        image_bytes = bytes_io.getvalue()

        await self.send_frame(image_bytes)
        self.current_step += 1
        return True

    async def consume_moves(self):
        connection = await aio_pika.connect_robust(url=self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(self.move_queue_name, durable=True)

            async for message in queue:
                async with message.process():
                    move_json = json.loads(message.body)
                    move = Move(**move_json)
                    await self.process_move(move)

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

        requests.post(f"{os.getenv('API_URL')}/maps/{self.scenario.map.id}", files=files)


    def work(self):
        logging.warning(f"Starting worker process {self.scenario.id}")
        asyncio.run(self.run())


