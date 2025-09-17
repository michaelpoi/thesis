import asyncio
import base64
import io
import json
import os
from datetime import datetime

from logger import Logger
from schemas import Move
from core.move_converter import MoveConverter
from PIL import Image
import aio_pika
from utils import get_rabbitmq_url
import logging
import requests
from metadrive.utils.draw_top_down_map import draw_top_down_map
import numpy as np

from metadrive.envs import MetaDriveEnv


def get_termination_reason(info):

    tm_reasons = {
        0: 'arrive_dest',
        1: 'out_of_road',
        2: 'crash_vehicle',
        3: 'crash_object',
    }

    for key, value in tm_reasons.items():
        try:
            if info[value]:
                return key
        except:
            pass

    return -1


class Worker:
    def __init__(self, scenario):
        self.rabbitmq_url = get_rabbitmq_url()
        self.scenario = scenario
        self.avs, self.humans = self.split_vehicles()
        self.env = None
        self.connection = None
        self.current_step = 0
        self.agent_ids = {}
        self.logger = Logger(self.scenario.id)

    async def send_message(self, queue_name, body):
        connection = await aio_pika.connect_robust(url=self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            await channel.default_exchange.publish(
                aio_pika.Message(body=body),
                routing_key=queue_name,
            )

    def generate_log_entry(self, move, info, tm, tr, to_transmit=False):

        agent_states = {
            agent_id: {
                "position": self.env.engine.agents[agent_id].position.tolist(),
                "velocity": self.env.engine.agents[agent_id].velocity.tolist(),
                "is_human": True,
            }
            for agent_id in self.env.engine.agents
        }

        for av_id, av_obj in self.env.engine.traffic_manager.spawned_objects.items():
            if av_id not in agent_states:
                agent_states[av_id] = {
                    "position": av_obj.position.tolist(),
                    "velocity": av_obj.velocity.tolist(),
                    "is_human": False
                }

        info = info if not to_transmit else {}

        return self.logger.add_entry(
            step_num=self.current_step,
            move_direction=move.direction,
            agent_states=agent_states,
            termination=tm,
            truncation=tr,
            info=info
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

    def split_vehicles(self):
        avs, humans = [], []
        for vehicle in self.scenario.vehicles:
            if vehicle.assigned_user_id is None:
                avs.append(vehicle)
            else:
                humans.append(vehicle)

        return avs, humans
    
    def get_map(self):
        lanes = {}
        for ind, lane in enumerate(self.env.engine.current_map.road_network.get_all_lanes()):
            xs, ys = zip(*lane.get_polyline())
            lanes[ind] = {}
            lanes[ind]['x'] = list(xs)
            lanes[ind]['y'] = list(ys)

        return lanes



    def setup_env(self, is_map_preview=False):
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
        if not is_map_preview:
            from core.multi_mixed_env import MultiPlayerEnv

            self.env = MultiPlayerEnv(config=config, avs=self.avs)
        else:
            config.pop('num_agents')
            self.env = MetaDriveEnv(config=config)
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


    # async def send_frame(self, image_bytes):
    #     message_body = {
    #         "scenario_id": self.scenario.id,
    #         "status": "ACTIVE",
    #         "step": self.current_step,
    #         "image_bytes": base64.b64encode(image_bytes).decode("utf-8")  # Convert bytes to base64 string
    #     }
    #     message_data = json.dumps(message_body).encode("utf-8")
    #     await self.send_message(self.results_queue_name, message_data)

    async def send_json(self, state):
        message_body = {
            "scenario_id": self.scenario.id,
            "status": "ACTIVE",
            "step": self.current_step,
            "map": self.get_map(),
            "state": state
        }
        json_data = json.dumps(message_body, indent=2, default=self.logger.to_serializable).encode("utf-8")

        await self.send_message(self.results_queue_name, json_data)



    async def process_finish(self, info):
        self.logger.save()
        message_body = {
            "scenario_id": self.scenario.id,
            "status": "FINISHED",
            "reason": get_termination_reason(info),
            # "gif": self.generate_gif(), Gif is not available when render is off
        }
        message_data = json.dumps(message_body).encode("utf-8")
        await self.send_message(self.results_queue_name, message_data)
        logging.warning(f"Shutting down worker {self.scenario.id}")
        self.env.close()
        loop = asyncio.get_event_loop()
        loop.stop()

        
    async def process_move(self, move: Move):
        start = datetime.now()
        move_arr = MoveConverter.convert(move)
        ego_agent_id = self.agent_ids[move.vehicle_id]
        step = {}
        for agent_id in self.agent_ids.values():
            if agent_id == ego_agent_id:
                step[agent_id] = move_arr

            else:
                step[agent_id] = np.array([0,0])



        obs, reward, tm, tr, info = self.env.step(step)

        state = self.generate_log_entry(move, info, tm, tr, True)
        state['time'] = move.timestamp


        if tm['__all__'] or tr['__all__'] or tm['agent0'] or tr['agent0']:
            await self.process_finish(info)

        await self.send_json(state)

        logging.warning(f"Step time: {datetime.now() - start}")

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
        self.setup_vehicle()
        await self.consume_moves()

    def map_preview(self):
        self.setup_env(is_map_preview=True)
        m = draw_top_down_map(self.env.current_map)
        bytes_io = io.BytesIO()
        img = Image.fromarray(m)
        img.save(bytes_io, format="PNG")
        image_bytes = bytes_io.getvalue()

        files = {
            'image': ('file.png', image_bytes, 'image/png'),
        }

        res = requests.post(f"{os.getenv('API_URL')}/maps/{self.scenario.map.id}", files=files)

        exit(0)


    def work(self):
        logging.warning(f"Starting worker process {self.scenario.id}")
        asyncio.run(self.run())


