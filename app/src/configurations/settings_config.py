import os

from dotenv import load_dotenv

load_dotenv()


class Settings():
    POSTGRES_USER: str = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD: str = os.getenv('POSTGRES_PASSWORD', '1234')
    POSTGRES_HOST: str = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT: str = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_DB: str = os.getenv('POSTGRES_DB', 'fabricio_delivery_db')
    POSTGRES_URL: str = f'postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'

    RABBITMQ_USER: str = os.getenv('RABBITMQ_USER', 'rabbitmq')
    RABBITMQ_PW: str = os.getenv('RABBITMQ_PW', '1234')
    RABBITMQ_HOST: str = os.getenv('RABBITMQ_HOST', 'localhost')
    RABBITMQ_PORT: str = os.getenv('RABBITMQ_PORT', '5672')
    RABBITMQ_QUEUE: str = os.getenv('RABBITMQ_QUEUE', 'fabricio_delivery_queue')

    class Config:
        env_file = '.env'


settings = Settings()
