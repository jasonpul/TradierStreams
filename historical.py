from dataclasses import dataclass, field
from typing import Callable, Any
from urllib.parse import urlencode

import utils, json, time, logging, requests, urllib3, streamz

urllib3.disable_warnings()

paths = {
    "brokerage": "https://api.tradier.com/v1/markets/",
    "sandbox": "https://sandbox.tradier.com/v1/markets/",
    "D": "history",
    "W": "history",
    "M": "history",
    "1min": "timesales",
    "5min": "timesales",
    "15min": "timesales",
    "tick": "timesales"
}

@dataclass
class TM:
    """ 
    Programmatic control over requesting historical data from Tradier's Market Data API.

    Register multiple tickers with the same parameters and block until the 'request' method is called.

    Args:
        API (str): (required) a valid Sandbox or Brokerage API key
        endpoint (str): (required) corresponding API endpoint, either of "brokerage" or "sandbox"
        callback (callable): (required) callback to run for every response received 
        delay (float): time delay between requests 


    Example usage:

    .. code-block:: python

        results = []

        market = TM(API_key = "...", endpoint = "brokerage", callback = results.append)
        market.register("TSLA", "MSFT", "AAPL", interval = "D")
        market.register("SPY", "VIX", interval = "1min", start = "2020-12-09", end = "2020-12-13")
        market.request()
    """

    API: str 
    endpoint: str 
    callback: Callable[[dict], Any]
    delay: int = 0.25

    def __post_init__(self):
        self.session = requests.Session()
        self.session.headers.update({"Authorization":"Bearer %s" % self.API, "Accept": "application/json"})
        self.session.verify = False

        retry = urllib3.util.Retry(total = 3, status = 3, status_forcelist = [403], backoff_factor = 4)
        self.session.mount(self.endpoint, requests.adapters.HTTPAdapter(pool_connections = 1, max_retries = retry, pool_maxsize = 500)) 
        self.tasks = []

    def _create_URL(self, symbol, **params):
        params["symbol"] = symbol
        interval = params["interval"]

        return paths[self.endpoint] + paths[interval] + "?" + urlencode(params)

    def request(self):
        assert self.tasks, "No tasks to request"

        source = streamz.Stream()
        source.rate_limit(self.delay).map(self.session.get).map(lambda x: x.json()).sink(self.callback)

        for URL in self.tasks:
            source.emit(URL)

    def register(self, *symbols, **params):
        """ 
        Maps parameters to multiple symbols 

        *symbols (str): equity or option ticker symbols
        **params (str):
            interval = one of "D", "W", "M", "1min", "5min", "15min", "tick"
            start, end = time strings in the format YYYY-MM-DD HH:MM 
        """

        if "interval" not in params: 
            params["interval"] = "D"

        source = streamz.Stream()
        source.map(self._create_URL, **params).sink(self.tasks.append)

        for symbol in symbols:
            source.emit(symbol)





