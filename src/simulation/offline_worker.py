import asyncio
import base64
import io
import json
from multiprocessing import Process, set_start_method

from MoveManager import MovingExampleEnv
from metadrive.policy.idm_policy import IDMPolicy
from metadrive.component.vehicle.vehicle_type import DefaultVehicle
from schemas import OfflineScenarioPreview
from PIL import Image
import aio_pika

from subworker import Subworker
from utils import get_rabbitmq_url
import logging
import requests
from metadrive.utils.draw_top_down_map import draw_top_down_map

set_start_method("spawn", force=True)


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


class OfflineWorker:
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
        return f"offline_{self.scenario.id}"

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
        await self.send_message(self.results_queue_name, image_bytes)
        logging.warning("Frame sent successfully")



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

    async def process_move(self, move: OfflineScenarioPreview):
        for mv in move.moves:
            move_arr = [mv.steering, mv.acceleration]
            for s in range(mv.steps):
                logging.info(f"Step {s}")
                obj, reward, tm, tr, info = self.env.step(move_arr)

        # if tm:
        #     await self.process_finish(info)

        image = self.env.render(mode='topdown', window=False, screen_record=True)

        bytes_io = io.BytesIO()
        img = Image.fromarray(image)
        img.save(bytes_io, format="PNG")
        image_bytes = bytes_io.getvalue()

        await self.send_frame(image_bytes)
        self.current_step += 1
        return True

    async def spawn_preview_worker(self, move):
        x, y = self.env.vehicle.position
        speed = self.env.vehicle.speed
        sub_worker = Subworker(self.scenario, x,y, speed)
        process = Process(target=sub_worker.work, args=(move,))
        process.start()

    async def consume_moves(self):
        connection = await aio_pika.connect_robust(url=self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(self.move_queue_name, durable=True)

            async for message in queue:
                async with message.process():
                    move_json = json.loads(message.body)
                    move = OfflineScenarioPreview(**move_json)

                    is_preview = message.headers.get("mtype") == "preview"
                    if is_preview:
                        await self.spawn_preview_worker(move)
                    else:
                        await self.process_move(move)

    async def run(self):
        self.setup_env()
        ego_vehicle = self.scenario.vehicles[0]
        self.setup_vehicle(ego_vehicle.init_x, ego_vehicle.init_y, ego_vehicle.init_speed)
        await self.consume_moves()



    def work(self):
        logging.warning(f"Starting Offline Worker process {self.scenario.id}")
        asyncio.run(self.run())


