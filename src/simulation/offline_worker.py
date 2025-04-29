import asyncio
import base64
import io
import json
from multiprocessing import Process, set_start_method
from typing import List

from core.multi_mixed_env import MultiPlayerEnv
from metadrive.policy.idm_policy import IDMPolicy
from metadrive.component.vehicle.vehicle_type import DefaultVehicle
from schemas import OfflineScenarioPreview
from PIL import Image
import aio_pika
from logger import Logger

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
        try:
            if info[value]:
                return key
        except:
            pass

    return -1


class OfflineWorker:
    def __init__(self, scenario):
        self.rabbitmq_url = get_rabbitmq_url()
        self.scenario = scenario
        self.avs, self.humans = self.split_vehicles()
        self.env = None
        self.connection = None
        self.current_step = 0
        self.agent_ids = {}
        self.logger = Logger(self.scenario.id, prefix='offline')

    async def send_message(self, queue_name, body, mtype=None):
        connection = await aio_pika.connect_robust(url=self.rabbitmq_url)
        headers = {'mtype': mtype} if mtype else {'mtype': 'sim_frame'}
        async with connection:
            channel = await connection.channel()
            await channel.default_exchange.publish(
                aio_pika.Message(body=body, headers=headers),
                routing_key=queue_name,
            )

    def split_vehicles(self):
        avs, humans = [], []
        for vehicle in self.scenario.vehicles:
            if vehicle.assigned_user_id is None:
                avs.append(vehicle)
            else:
                humans.append(vehicle)

        return avs, humans


    def get_vehicle_config(self):
        return dict(
            show_dest_mark = True,

        )

    def generate_log_entry(self, info, tm, tr):

        agent_states = {
            agent_id: {
                "position": self.env.engine.agents[agent_id].position.tolist(),
                "velocity": self.env.engine.agents[agent_id].velocity.tolist()
            }
            for agent_id in self.env.engine.agents
        }

        self.logger.add_entry(
            step_num=self.current_step,
            move_direction='N/A',
            agent_states=agent_states,
            termination=tm,
            truncation=tr,
            info=info
        )

    @property
    def move_queue_name(self):
        return f"offline_{self.scenario.id}"

    @property
    def results_queue_name(self):
        return f"offline_queue_{self.scenario.id}"

    def setup_env(self):
        config = {
            "use_render": False,
            "traffic_density": 0.,
            "map": self.scenario.map.layout,
            "vehicle_config": self.get_vehicle_config(),
            "out_of_road_done": False,
            "horizon": self.scenario.steps,
            "num_agents": len(self.humans),
            "truncate_as_terminate": False,
        }
        self.env = MultiPlayerEnv(config=config, avs=self.avs)
        self.env.reset()

        for human, agent_id in zip(self.humans, self.env.agents.keys()):
            self.agent_ids[human.id] = agent_id

    def setup_vehicle(self):
        for vehicle in self.humans:
            agent_id = self.agent_ids[vehicle.id]
            agent = self.env.engine.agents[agent_id]

            agent.set_position([vehicle.init_x, vehicle.init_y])
            agent.set_velocity([vehicle.init_speed, 0])


    def generate_gif(self):
        filename = f"{self.scenario.id}.gif"
        self.env.top_down_renderer.generate_gif(gif_name=filename)

        with open(filename, "rb") as f:
            gif_data = f.read()

        return base64.b64encode(gif_data).decode('utf-8')


    async def send_frame(self, image_bytes):
        await self.send_message(self.results_queue_name, image_bytes)
        logging.warning("Frame sent successfully")

    def to_flat_view(self, moves: List[OfflineScenarioPreview]):
        flat = {}

        for move in moves:
            agent_id = self.agent_ids[move.vehicle_id]
            flat[agent_id] = {}
            curr = 0

            for dsm in move.moves:
                for step in range(dsm.steps):
                    flat[agent_id][curr + step] = [dsm.steering, dsm.acceleration]

                curr += dsm.steps


        return flat


    async def process_finish(self, info):
        self.logger.save()
        message_body = {
            "scenario_id": self.scenario.id,
            "status": "FINISHED",
            "reason": get_termination_reason(info),
            "gif": self.generate_gif(),
        }
        message_data = json.dumps(message_body).encode("utf-8")
        await self.send_message(self.results_queue_name, message_data, 'finish')
        logging.warning(f"Shutting down worker {self.scenario.id}")
        exit(0)

    async def process_move(self, moves: List[OfflineScenarioPreview], for_steps:int=None):
        flat = self.to_flat_view(moves)
        print(flat)
        print(self.env.agents)
        for step in range(for_steps):
            move = {}
            for agent_id in self.agent_ids.values():
                move[agent_id] = flat[agent_id][step]

            obj, reward, tm, tr, info = self.env.step(move)

            self.generate_log_entry(info, tm, tr)

            logging.warning(tm)
            logging.warning(tr)

            if tm['__all__'] or tr['__all__'] or tm['agent0'] or tr['agent0']:
                return await self.process_finish(info)



            if step % 10 == 0:
                logging.warning(f'generated frame {step}')
                self.env.render(mode='topdown',
                                        window=False,
                                        film_size=(1000, 1000),
                                        screen_size=(1000, 1000),
                                        camera_position=self.env.current_map.get_center_point(),
                                        screen_record=True,
                                        scaling=None,
                                        text={"episode step": self.env.engine.episode_step,
                                              "speed m/s": round(self.env.engine.agents['agent0'].speed, 2)})


        image = self.env.render(mode='topdown',
                                window=False,
                                film_size=(1000, 1000),
                                screen_size=(1000, 1000),
                                camera_position=self.env.current_map.get_center_point(),
                                screen_record=True,
                                scaling=None,
                                text={"episode step": self.env.engine.episode_step,
                                      "speed m/s":  round(self.env.engine.agents['agent0'].speed, 2)})

        bytes_io = io.BytesIO()
        img = Image.fromarray(image)
        img.save(bytes_io, format="PNG")
        image_bytes = bytes_io.getvalue()

        await self.send_frame(image_bytes)
        self.current_step += 1
        return True

    async def spawn_preview_worker(self, move):
        agent_id = self.agent_ids[move.vehicle_id]
        agent = self.env.engine.agents[agent_id]
        x, y = agent.position
        speed = agent.speed
        heading = agent.heading_theta
        sub_worker = Subworker(self.scenario, x,y, speed, heading)
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
                    is_preview = message.headers.get("mtype") == "preview"
                    if is_preview:
                        move = OfflineScenarioPreview(**move_json)
                        await self.spawn_preview_worker(move)
                    else:
                        steps = move_json["steps"]
                        moves = [OfflineScenarioPreview(**move) for move in move_json["moves"]]
                        await self.process_move(moves, steps)

    async def run(self):
        self.setup_env()
        self.setup_vehicle()
        await self.consume_moves()



    def work(self):
        logging.warning(f"Starting Offline Worker process {self.scenario.id}")
        asyncio.run(self.run())


