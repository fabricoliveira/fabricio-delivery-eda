from datetime import datetime

import pytz


def time_now():
    return str(datetime.now(pytz.timezone('America/Sao_Paulo')))
