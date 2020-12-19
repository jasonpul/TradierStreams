import pandas as pd 
from historical import Market

"""
Since Tradier does not allow chunk-streaming of large requests (like daily ticks),
one must manually split up the requests in small time intervals. 

You may need to adjust the interval depending on the ticker's trade volume. 
I use 30 minute intervals in this example (safe for tickers like 'SPY')
"""

# create a Market client for historical data
market = Market("API_KEY", "brokerage")


# create 30 minute time intervals to iterate through
start = pd.date_range("09:30", "15:30", freq = "30min")
stop = start + pd.Timedelta("29min")

for i, k in zip(start, stop):
    market.register(symbols = ["SPY"], interval = "tick", start = i, end = k)


# example of a callback to run after every response
results = []
parse = lambda response: results.extend(response["series"]["data"])


# start making requests
market.request(delay = 0, callback = parse)
