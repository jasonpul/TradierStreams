import logging, time, ciso8601

def filelogger(filepath: str, level: int = 10):
    """ Create a log handler that logs to the given file """

    logger = logging.getLogger()
    logger.setLevel(level)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(filename)s] %(message)s", datefmt = "%Y-%m-%d %H:%M:%S")
    
    handler = logging.FileHandler(filepath)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def consolelogger(level: int = 10):
    """ Creates a log handler that logs to the console """

    logger = logging.getLogger()
    logger.setLevel(level)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(filename)s] %(message)s", datefmt = "%Y-%m-%d %H:%M:%S")
    
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.handlers = [i for i in logger.handlers if type(i) is not logging.StreamHandler]

    logger.addHandler(handler)

    # disable spam loggers
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    logging.getLogger('asyncio').setLevel(logging.ERROR)
    logging.getLogger('asyncio.coroutines').setLevel(logging.ERROR)
    logging.getLogger('websockets.client').setLevel(logging.ERROR)
    logging.getLogger('websockets.protocol').setLevel(logging.ERROR)


def timestamp(timestring: str):
    """ Converts a time string into a UNIX timestamp """

    ts = ciso8601.parse_datetime(timestring)
    return time.mktime(ts.timetuple())
