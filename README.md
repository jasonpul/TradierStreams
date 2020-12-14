## **Tradier Data Streaming**
The goal of this library is to make working with Tradier's WebSocket and Market Data API as easy as possible.

### [Realtime](https://github.com/akbar-amin/tradier-market-streams/blob/main/streaming.py)
Realtime data streaming is handled asynchronously with the ```websockets``` module. 
<br/><br/>
A valid Brokerage API key is needed to create a WebSocket connection. The connection will run until a given stop time is reached or when a keyboard interrupt (CTRL + C) occurs.
Stop times are accepted up to microsecond precision as a time string: ```(YYYY-MM-DD hh:mm:ss.ssssss)```. 
<br/>
By default, all messages received by the WebSocket will be printed to console; however, a callback can be passed to override this. This allows you to filter and/or store incoming data however you like.
```python3
results = []    # store incoming data into a list
stream = TS(API = "...", stoptime = "2020-12-14 16:00:00", callback = results.append)  # specify callback as a list append 
```
A stream subscription must contain equity/option symbols and data-filters. You may also include any additional payload parameters as keyword arguments. After registering a subscription, simply connect to the stream.
```python3
stream.register(symbols = ["TSLA", "SPY"], filters = ["trade", "quote"])
stream.connect()                                                                       
```
*Refer to the docstring for "register" to see all acceptable parameters.*
<br/><br/>
Currently, you cannot change your subscription after calling "connect". This is something I plan on changing in the future with an interactive, command-line terminal.


### [Historical](https://github.com/akbar-amin/tradier-market-streams/blob/main/historical.py)
Historical data is fetched synchronously with HTTP requests. 
<br/><br/>
A valid Sandbox or Brokerage API key is needed to request historical data. Additionally, some features such as tick data are exclusive to Brokerage API members. All requests are made individually with an adjustable time delay in between each request (.25 seconds by default). A delay is needed to reduce the possibility of a rate limit; however, a request can be retried upto 3 times if a ratelimit occur. Similar to realtime streaming, a callback can be specified to run after receiving a response. 
<br/><br/>
In contrast with realtime subscriptions, multiple historical subscriptions can be registered at once in bulk. Multiple symbols can be registered to the same parameters *multiple* times. See the following example for clarification. 
```python3
results = []

market = TM(API = "...", endpoint = "brokerage", callback = results.append)
market.register("TSLA", "MSFT", "AAPL", interval = "daily")
market.register("TSLA", "SPY", "VIX", interval = "1min", start = "2020-12-09", end = "2020-12-13")
market.request()
```
*Refer to the docstring for "register" to see all acceptable parameters.*

### Callback Example
Realtime stream example with a custom class to write results into a TXT or JSON file. 

```python3
class FileWriter:
    def __init__(self, filepath: str):
        self.fp = open(filepath, "a")
        weakref.finalize(self, self.fp.close)

    def write(self, data: str):
        self.fp.write(data + "\n")
        

results = FileWriter("data/2020-12-13.json")
stream = TS(API = "...", stoptime = "..." callback = results.write)
stream.register(symbols = ["TSLA", "SPY"], filters = ["trade", "quote", "tradex", "timesale", "summary"], linebreak = False)
stream.connect()
```

