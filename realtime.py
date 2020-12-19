import json, time, logging, utils
import _thread as thread

from websocket import WebSocketApp, WebSocketConnectionClosedException, WebSocketPayloadException, WebSocketTimeoutException
from typing import List, Type, Callable, Any
from streamz import Stream
from attr import asdict

from helpers import Client, Subscription


class Streaming:

    (DISCONNECTED, CONNECTING, CONNECTED) = range(3)

    def __init__(self, key: str):
        """
        Programmatic control over starting and stopping Tradier's Market WebSocket API

        Args:
            key (str): (required) a valid Brokerage API key
        
        Example usage:

        .. code-block:: python

            from helpers import Subscription

            sub = Subscription(symbols = ["TSLA", "SPY"], filter = ["trade", "quote"])

            stream = Streaming(key = "API_KEY")
            stream.subscribe(sub)
            stream.startup()

        """

        self.httpclient = Client(key, "brokerage")
        self.ws = self._create_websocket()
        self.reset()

    def reset(self):
        self.payload = None  
        self.sequence = 0
        self.state = Streaming.DISCONNECTED
        self.event = Stream()

    def _create_websocket(self):
        ws = WebSocketApp(
            "wss://ws.tradier.com/v1/markets/events",
            on_open = lambda ws: self.opened(ws),
            on_close = lambda ws: self.closed(ws),
            on_error = lambda ws, reason: self.errors(ws, reason),
            on_message = lambda ws, message: self.receive(ws, message)
        )

        return ws

    def opened(self, ws):
        logging.debug("[<--] connected to websocket")
        self.state = Streaming.CONNECTED

        if self.payload is None: 
            raise WebSocketPayloadException("no subscription registered")

        logging.debug("[-->] %s" % self.payload)
        self.ws.send(json.dumps(self.payload))

        thread.start_new_thread(self.heartbeat, ())
        
    def receive(self, ws, message):
        self.event.emit(message, asynchronous = True)
        self.sequence += 1

    #TODO: use heartbeat for subscriptions
    def heartbeat(self):
        logging.debug("[<--] entered heartbeat")
        while self.state == 2:    
            if self.state != 2:
                logging.debug("[<--] exiting heartbeat")
                break 
            logging.debug("[<--] total sequence (received) %d" % self.sequence)
            time.sleep(10)

    def errors(self, ws, reason):
        if isinstance(reason, WebSocketPayloadException):
            logging.error("[<--] invalid payload")
        elif isinstance(reason, WebSocketTimeoutException):
            logging.error("[<--] stream connection timed out")
        elif isinstance(reason, WebSocketConnectionClosedException):
            logging.error("[<--] fatal connection error")
        elif isinstance(reason, KeyboardInterrupt):
            logging.error("[<--] stream manually interrupted")
        else:
            logging.error("[<--] unhandled error '%s'" % reason)
        
        self.shutdown()

    def closed(self, ws):
        logging.debug("[<--] disconnected from websocket")

    def subscribe(self, subscription: Type[Subscription]): 
        self.payload = asdict(subscription)
        sessionid = self.httpclient.sessionid
        self.payload.update({"sessionid": sessionid})

    def shutdown(self):
        logging.debug("[-->] shutdown sequence initiated")
        self.reset()
        self.ws.close()

    def startup(self, delay: float = 60, callback: Callable[[list], Any] = print):
        """ 
        Connects to the stream and listens for messages

        Args:
            delay (float): time interval to wait before passing through a data chunk 
            callback (function): a callble receiving every chunk (list)
        
        """

        logging.debug("[-->] startup sequence initiated")
        self.state = Streaming.CONNECTING
        
        self.event.timed_window(delay).sink(callback)
        self.ws.run_forever(ping_interval = 10, ping_timeout = 5)
