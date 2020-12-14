from typing import Callable, Any
from urllib.parse import urlencode

import utils, json, time, logging, requests, urllib3, streamz

utils.consolelogger(10)
urllib3.disable_warnings()


paths = {
    "brokerage": "https://api.tradier.com/v1/markets/",
    "sandbox": "https://sandbox.tradier.com/v1/markets/",
    "daily": "history",
    "weekly": "history",
    "monthly": "history",
    "1min": "timesales",
    "5min": "timesales",
    "15min": "timesales",
    "tick": "timesales"
}


class TM:

    def __init__(self, API: str, endpoint: str, delay: float = 0.25, callback: Callable[[dict], Any] = print):
        """ 
        Programmatic control over fetching historical data from Tradier's Market Data API.

        Register multiple tickers with the same parameters and block until the 'request' method is called.

        Args:
            API (str): (required) a valid Sandbox or Brokerage API key
            endpoint (str): (required) corresponding API endpoint, either of "brokerage" or "sandbox"
            delay (float): time delay between requests 
            callback (callable): callback to run for every response received 


        Example usage:

        .. code-block:: python

            results = []

            market = TM(API_key = "...", endpoint = "brokerage", callback = results.append)
            market.register("TSLA", "MSFT", "AAPL", interval = "D")
            market.register("SPY", "VIX", interval = "1min", start = "2020-12-09", end = "2020-12-13")
            market.request()
        """

        self.session = self._create_session(API, endpoint) 
        self.endpoint = endpoint
        self.callback = callback
        self.delay = delay

        self.tasks = []

    @staticmethod
    def _create_session(API: str, endpoint: str):
        session = requests.Session()
        session.headers.update({"Authorization":"Bearer %s" % API, "Accept": "application/json"})
        session.verify = False

        retry = urllib3.util.Retry(total = 3, status = 3, status_forcelist = [403], backoff_factor = 4)
        session.mount(endpoint, requests.adapters.HTTPAdapter(pool_connections = 1, max_retries = retry, pool_maxsize = 500)) 
        return session

    def _create_URL(self, symbol, **params):
        params["symbol"] = symbol
        interval = params["interval"]

        return paths[self.endpoint] + paths[interval] + "?" + urlencode(params)

    def request(self):
        source = streamz.Stream()
        source.rate_limit(self.delay).map(self.session.get).map(lambda x: x.json()).sink(self.callback)

        for URL in self.tasks:
            logging.debug(f"Task: {URL}")
            source.emit(URL)
            

        logging.debug("Completed ")
        self.tasks.clear()


    def register(self, *symbols, **params):
        """ 
        Maps parameters to multiple symbols 

        *symbols (str): equity or option ticker symbols
        **params (str):
            interval = one of "daily", "weekly", "monthly", "1min", "5min", "15min", "tick"
            start, end = time strings in the format YYYY-MM-DD HH:MM 
        """

        if "interval" not in params: 
            params["interval"] = "daily"

        source = streamz.Stream()
        source.map(self._create_URL, **params).sink(self.tasks.append)

        for symbol in symbols:
            logging.debug(f"Registering: {symbol} ({params['interval']})")
            source.emit(symbol)
            


