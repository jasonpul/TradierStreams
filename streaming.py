

from dataclasses import dataclass, field
from typing import Callable, List, Any
from tornado.platform.asyncio import AsyncIOMainLoop

import utils, json, time, logging, weakref, websockets, asyncio, streamz

AsyncIOMainLoop().install()
utils.consolelogger(10)

@dataclass
class TS:
    """
    Programmatic control over starting and stopping Tradier's Market WebSocket API

    Args:
        API (str): (required) a valid Brokerage API key
        stoptime (str): (required) local time string indicating when to close the stream
        callback (callable): (required) callback to run for every message received 

        symbols (list): equity or option ticker symbols
        filters (list): types of payloads to retrieve in the stream 
        linebreak (bool): insert a line break after a completed payload
        validticks (bool): include only ticks that are considered valid by exchanges.
        details (bool): include advanced details in timesale payloads
    

    Example usage:

    .. code-block:: python

        results = []

        stream = TS(API_key = "...", stoptime = "2020-12-14 16:00:00", callback = results.append)
        stream.symbols += ["TSLA", "SPY", "AAPL", "MSFT"]
        stream.filters += ["trade", "tradex", "quote", "summary", "timesale"]
        stream.connect()

    """
    API: str
    stoptime: str
    callback: Callable[[str], Any]

    symbols: List[str] = field(default_factory = list)
    filters: List[str] = field(default_factory = list)
    linebreak: bool = False
    validticks: bool = True
    details: bool = False

    def __post_init__(self):
        self.source = streamz.Stream(asynchronous = True)
        self.source.sink(self.callback)

        self.stoptime = utils.timestamp(self.stoptime)
        self.loop = None

    @property
    def payload(self):
        if not self.symbols: raise ValueError("No symbols were specified")

        payload = {
            "linebreak": self.linebreak, 
            "validOnly": self.validticks, 
            "advancedDetails": self.details,
            "symbols": self.symbols,
            "filter": self.filters,
            "sessionid": utils.sessionid(self.API)
        }

        logging.debug(f"Prepared payload: {payload}")
        return json.dumps(payload)

    async def ws_connect(self):
        try:
            ws = await websockets.connect("wss://ws.tradier.com/v1/markets/events", 
                                            max_size = 2000,
                                            max_queue = 100000,
                                            
                                        )
            await ws.send(self.payload)
            
            logging.debug("Listening into stream...")
            while True:
                self.source.emit(await ws.recv())

        except (KeyboardInterrupt, KeyError, ValueError, websockets.WebSocketException) as error:
            self.disconnect(error) 
    
    def disconnect(self, reason: str):
        logging.debug(f"Stream connection closed ({reason})")
        
        self.loop.stop()
        self.loop.stop()

    def connect(self):
        self.loop = asyncio.get_event_loop()
        self.loop.call_later(self.stoptime - time.time(), self.disconnect, "reached stoptime")
        self.loop.create_task(self.ws_connect())
        self.loop.run_forever()


class FileWriter:
    """ 
    Example class that writes each stream message to a file 

    Args:
        filepath (str): (required) TXT or JSON file to write into

    Example usage:

    .. code-block:: python
    
        results = FileWriter("data/2020-12-13.json")
        stream = TS(callback = results.write, ...)
            ....
        stream.connect()

    """

    def __init__(self, filepath: str):
        self.fp = open(filepath, "a")
        weakref.finalize(self, self.fp.close)

    def write(self, data: str):
        self.fp.write(data + "\n")


# if __name__ == '__main__':
#     results = FileWriter("data/2020-12-13.json")
#     stream = TS(API = "GET_YOUR_OWN_KEY", callback = results.write, stoptime = "2020-12-13 14:16:00")
#     stream.symbols += ["AAPL", "TSLA", "SPY", "MSFT", "AMZN", "VIX"]
#     stream.filters += ["trade", "tradex", "quote", "summary", "timesale"]
#     stream.connect()
