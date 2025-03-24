import base64
import json
import os

import aio_pika
import io
from settings import settings

class ImageQueue:
    def __init__(self, rabbitmq_url:str):
        self.rabbitmq_url = rabbitmq_url

    def save_frame(self, scenario_id, step_num, image_bytes):
        #file_name = settings.static_dir / "frames" / str(scenario_id) / f"{str(step_num)}.png"
        file_name = settings.base_dir / f"{scenario_id}.png"
        dir_name = os.path.dirname(file_name)

        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

        decoded_bytes = base64.b64decode(image_bytes)

        io_bytes = io.BytesIO(decoded_bytes)

        with open(file_name, "wb+") as f:
            f.write(io_bytes.getvalue())

    async def consume_results(self):
        connection = await aio_pika.connect_robust(self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue('images_queue', durable=True)

            async for message in queue:
                async with message.process():
                    message_body = json.loads(message.body.decode("utf-8"))  # Decode JSON
                    status = message_body.get('status')
                    scenario_id = message_body['scenario_id']
                    if status == 'ACTIVE':
                        step = message_body.get('step')
                        self.save_frame(scenario_id, step, message_body['image_bytes'])
                    else:
                        print(message_body.get('reason'))


queue = ImageQueue(rabbitmq_url=settings.rabbitmq_url)

