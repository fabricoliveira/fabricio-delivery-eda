import logging
import os
import sys


def configure_logging():
    level_name = os.getenv('LOG_LEVEL', 'DEBUG').upper()
    level = getattr(logging, level_name, logging.DEBUG)

    root = logging.getLogger()
    root.setLevel(level)

    for h in list(root.handlers):
        if isinstance(h, logging.StreamHandler):
            root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    fmt = '%(asctime)s %(levelname)s %(name)s %(message)s'
    handler.setFormatter(logging.Formatter(fmt))
    root.addHandler(handler)

    logging.getLogger('sqlalchemy').setLevel(os.getenv('SQLALCHEMY_LOG_LEVEL', 'INFO'))
    logging.getLogger('aio_pika').setLevel(os.getenv('AIO_PIKA_LOG_LEVEL', level_name))
