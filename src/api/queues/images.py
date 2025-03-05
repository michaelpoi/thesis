import base64
import json

import aio_pika
import io
from settings import settings

class ImageQueue:
    def __init__(self, rabbitmq_url:str):
        self.rabbitmq_url = rabbitmq_url

    async def consume_results(self):
        print("Got Image")
        connection = await aio_pika.connect_robust(self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue('images_queue', durable=True)

            async for message in queue:
                async with message.process():
                    message_body = json.loads(message.body.decode("utf-8"))  # Decode JSON
                    image_bytes = base64.b64decode(message_body["image_bytes"])
                    scenario_id = message_body['scenario_id']
                    io_bytes = io.BytesIO(image_bytes)

                    with open('/app/output.png', 'wb+') as f:
                        f.write(io_bytes.getvalue())


queue = ImageQueue(rabbitmq_url=settings.rabbitmq_url)

