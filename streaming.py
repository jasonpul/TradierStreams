from tornado.platform.asyncio import AsyncIOMainLoop
from typing import Callable, List, Any

import utils, json, time, logging, weakref, websockets, requests, asyncio, streamz

AsyncIOMainLoop().install()
utils.consolelogger(10)


class TS:

    def __init__(self, API: str, stoptime: str, callback: Callable[[str], Any] = print):
        """
        Programmatic control over starting and stopping Tradier's Market WebSocket API

        Args:
            API (str): (required) a valid Brokerage API key
            stoptime (str): (required) local time string indicating when to close the stream
            callback (callable): callback to run for every message received 
        
        Example usage:

        .. code-block:: python

            results = []

            stream = TS(API_key = "...", stoptime = "2020-12-14 16:00:00", callback = results.append)
            stream.register(symbols = ["TSLA", "SPY"], filters = ["trade", "quote"])
            stream.connect()

        """
        self.stoptime = utils.timestamp(stoptime)
        self.API = API 

        self.source = streamz.Stream(asynchronous = True)
        self.source.sink(callback)

        self.payload = {}
        self.loop = None
        
    
    def register(self, symbols: List[str], filters: List[str], **settings):
        """
        Args:
            symbols (list): (required) equity or option ticker symbols
            filters (list): (required) types of payloads to retrieve in the stream 
        
        Settings:
            linebreak (bool): insert a line break after a completed payload
            validOnly (bool): include only ticks that are considered valid by exchanges.
            advancedDetails (bool): include advanced details in timesale payloads
        """
        
        settings.update({"symbols": symbols, "filter": filters})
        self.payload.update(settings)

        logging.debug(f"Subscription: {self.payload}")
    
    def authenticate(self):
        response = requests.post(
            url = "https://api.tradier.com/v1/markets/events/session",
            headers = {"Accept": "application/json", "Authorization": "Bearer %s" % self.API}
        )

        sessionid = response.json()["stream"]["sessionid"]
        self.payload.update({"sessionid": sessionid})

        logging.debug(f"Authentication Successful ({sessionid})")

    async def ws_connect(self):
        try:
            ws = await websockets.connect("wss://ws.tradier.com/v1/markets/events", 
                                            max_size = 2000,
                                            max_queue = 100000,
                                            
                                        )
            await ws.send(json.dumps(self.payload))
            
            logging.debug("Listening into WebSocket...")
            while True:
                self.source.emit(await ws.recv())

        except (KeyboardInterrupt, KeyError, ValueError, websockets.WebSocketException) as error:
            self.disconnect(error) 

    def disconnect(self, reason: str):
        logging.warn(f"Stream Closed ({reason})")
        
        self.loop.stop()
        self.loop.stop()

    def connect(self):
        self.authenticate()

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
#     stream = TS(API = "<API_KEY>", stoptime = "2020-12-13 14:16:00", callback = results.write)
#     stream.register(symbols = ["TSLA", "SPY"], filters = ["trade", "quote"])
#     stream.connect()
