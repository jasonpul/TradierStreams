import logging, utils 
from streamz import Stream
from helpers import History, Client

utils.consolelogger(10)

class Market:
    def __init__(self, key: str, endpoint: str):
        """ 
        Programmatic control over fetching historical data from Tradier's Market Data API.

        Can be used to register multiple tickers with the same parameters.

        Args:
            key (str): (required) a valid Sandbox or Brokerage API key
            endpoint (str): (required) corresponding API endpoint, either of "brokerage" or "sandbox"

        Example usage:

        .. code-block:: python

            market = Market(key = "API_KEY" endpoint = "API_ENDPOINT")
            market.register(["TSLA", "MSFT", "AAPL"], interval = "daily")
            market.register(["SPY", "VIX"], interval = "1min", start = "2020-12-09", end = "2020-12-13")
            market.request()

            print(market.results)
        """

        self.httpclient = Client(key, endpoint)
        
        self.tasks = []
        self.results = []

    def register(self, symbols = list, interval = str, **kwargs):
        """ 
        Maps parameters to multiple symbols 

        Args:
            symbols (list): (required) equity or option ticker symbols
            interval (str): (required) one of "daily", "weekly", "monthly", "1min", "5min", "15min", "tick"

        Keyword Args:
            start, end = time strings in the format YYYY-MM-DD HH:MM 
        """

        for symbol in symbols:
            self.tasks.append(repr(History(symbol, interval, **kwargs)))
        
        logging.debug("[-->] registered %d URLs (current queue size: %d)" % (len(symbols), len(self.tasks)))

    def request(self):
        """ Starts making requests and stores results in a list """

        fetch = Stream()
        fetch.rate_limit(0.25).map(self.httpclient.s.get).map(lambda x: x.json()).sink(self.results.append)
        
        for task in self.tasks:
            fetch.emit(task)    
            logging.debug("[<--] %s" % task.split("?")[1])
        
        self.tasks.clear()
