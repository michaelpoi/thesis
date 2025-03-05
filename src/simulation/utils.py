import os

def get_rabbitmq_url():
    url = "amqp://{}:{}@{}/".format(
                                     os.getenv('rq_user', 'guest'),
                                     os.getenv('rq_password', 'guest'),
                                     os.getenv('rq_host'))

    return url

