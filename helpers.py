import attr, datetime, requests, urllib3, logging, utils, os 
from urllib.parse import urlencode
from datetime import datetime as dt 

utils.consolelogger(10)
urllib3.disable_warnings()

base = {"brokerage": "https://api.tradier.com/v1/", "sandbox": "https://sandbox.tradier.com/v1/"}

@attr.s(repr = False)
class History:
    """ Factory responsible for generating Market request URLs """

    symbol = attr.ib()
    interval = attr.ib()
    start = attr.ib("2000-01-01")
    end = attr.ib(str(dt.date(dt.now())))

    path = attr.ib()
    parameters = attr.ib()

    @parameters.default 
    def _create_parameters(self):
        return urlencode({"symbol": self.symbol, "interval": self.interval, "start": self.start, "end": self.end})

    @path.default
    def _create_path(self):
        if self.interval in ("daily", "weekly", "monthly"):
            return "markets/history?"
        elif self.interval in ("tick", "1min", "5min", "15min"):
            return "markets/timesales?"
        else:
            raise(ValueError("Invalid interval"))

    def __repr__(self):
        return os.environ["endpoint"] + self.path + self.parameters

@attr.s
class Client:
    """ Tradier-Authenticated client for HTTP requests """

    key = attr.ib(converter = lambda x: "Bearer %s" % x)
    endpoint = attr.ib(converter = lambda x: base[x])

    s = attr.ib()

    def __attrs_post_init__(self):
        os.environ["endpoint"] = self.endpoint

    @s.default 
    def _create_session(self):
        session = requests.Session()
        session.headers.update({"Authorization": self.key, "Accept": "application/json"})
        session.verify = False

        retry = urllib3.util.Retry(total = 3, status = 3, status_forcelist = [403], backoff_factor = 4)
        session.mount(self.endpoint, requests.adapters.HTTPAdapter(pool_connections = 1, max_retries = retry, pool_maxsize = 500)) 
        
        logging.debug("[<--] created client session")
        
        return session

    @property
    def sessionid(self):
        response = self.s.post(self.endpoint + "markets/events/session")
        auth = response.json()["stream"]["sessionid"]
        
        logging.debug("[<--] retrieved sessionid")
        return auth

@attr.s
class Subscription:
    """
    Holds Streaming subscription parameters.

    Args:
        symbols (list): (required) equity or option ticker symbols
        filter  (list): (required) types of payloads to retrieve in the stream 
    
    Settings:
        linebreak (bool): insert a line break after a completed payload
        validOnly (bool): include only ticks that are considered valid by exchanges.
        advancedDetails (bool): include advanced details in timesale payloads
    """
    
    symbols = attr.ib(default = attr.Factory(list))
    filter = attr.ib(default = attr.Factory(list))
    validOnly = attr.ib(True)
    linebreak = attr.ib(False)
    advancedDetails = attr.ib(False)

