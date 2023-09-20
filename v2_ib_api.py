from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import *

import pandas as pd
import pandas_ta as ta
import threading
import time
import numpy as np
import yfinance as yf
from datetime import datetime
import time
import math
 
class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.all_positions = pd.DataFrame([], columns = ['Account','Symbol', 'Quantity', 'Average Cost', 'Sec Type'])
 
    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextorderId = orderId
        print('The next valid order id is: ', self.nextorderId)
 
    def orderStatus(self, orderId, status, filled, remaining, avgFullPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print('orderStatus - orderid:', orderId, 'status:', status, 'filled', filled, 'remaining', remaining, 'lastFillPrice', lastFillPrice)
   
    def openOrder(self, orderId, contract, order, orderState):
        print('openOrder id:', orderId, contract.symbol, contract.secType, '@', contract.exchange, ':', order.action, order.orderType, order.totalQuantity, orderState.status)
 
    def execDetails(self, reqId, contract, execution):
        print('Order Executed: ', reqId, contract.symbol, contract.secType, contract.currency, execution.execId, execution.orderId, execution.shares, execution.lastLiquidity)
 
    def position(self, account, contract, position, avgCost):
        super().position(account, contract, position, avgCost)
        print("Position.", "Account:", account, "Symbol:", contract.symbol, "SecType:",
                contract.secType, "Currency:", contract.currency,
                "Position:", position, "Avg cost:", avgCost)
        index = str(contract.symbol)
        self.all_positions.loc[index] = account, contract.symbol, position, avgCost, contract.secType
 
def run_loop():
    app.run()
'''
def RSI(series, period):
    delta = series.diff().dropna()
    u = delta * 0
    d = u.copy()
    u[delta > 0] = delta[delta > 0]
    d[delta < 0] = -delta[delta < 0]
    u[u.index[period-1]] = np.mean( u[:period] ) 
    u = u.drop(u.index[:(period-1)])
    d[d.index[period-1]] = np.mean( d[:period] ) 
    d = d.drop(d.index[:(period-1)])
    rs = u.ewm(com=period-1, adjust=False).mean() / d.ewm(com=period-1, adjust=False).mean()
    return 100 - 100 / (1 + rs)
'''

def GetRSI(tickers):
    df = yf.download(tickers, period = '2d', interval = '2m')
    df['RSI14'] = ta.rsi(df['Adj Close'])
    return df['RSI14'][-1]

def fetchCurrentSecond():
    curTime = datetime.now()
    return curTime.hour * 3600 + curTime.minute * 60 + curTime.second

def Stock_Contract():
    contract = Contract()
    contract.symbol = 'AMZN'
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    return contract

def Stock_Order(direction):
    order = Order()
    order.action = direction
    order.totalQuantity = AMOUNT_OF_SHARES
    order.orderType = 'MKT'
    order.eTradeOnly = False
    order.firmQuoteOnly = False
    return order


if __name__ == "__main__":
    LOWER_THRESHOLD = 40
    UPPER_THRESHOLD = 60
    AMOUNT_OF_SHARES = 1000
    tickers = ['AMZN']

    app = IBapi()
    app.connect('127.0.0.1', 7497, 123)
    
    app.nextorderId = None
    
    #Start the socket in a thread
    api_thread = threading.Thread(target=run_loop, daemon=True)
    api_thread.start()
    
    #Check if the API is connected via orderid
    while True:
        if isinstance(app.nextorderId, int):
            print('connected')
            break
        else:
            print('waiting for connection')
            time.sleep(2)
    
    #Run Algo
    position = 0
    cursec = fetchCurrentSecond()
    curTime = datetime.now()
    curRSI = GetRSI(tickers)
    print(curRSI)
    print("Current Time: ", curTime,"; Current sec: ", cursec)

    if curTime.hour >= 21:
        execution_time = 23*3600 + 3*60 + 59 #inital execution time, set to #23:03:59
        while (curTime.hour >= 21):
            if cursec == execution_time: 
                if position > 0 and curRSI <= 50:
                    #close my sell pos
                    app.placeOrder(app.nextorderId, Stock_Contract(), Stock_Order('BUY'))
                    position = 0
                    app.nextorderId += 1
                elif position < 0 and curRSI >= 50:
                    #close my buy pos
                    app.placeOrder(app.nextorderId, Stock_Contract(), Stock_Order('SELL'))
                    position = 0
                    app.nextorderId += 1
                elif position == 0 and curRSI <= LOWER_THRESHOLD:
                    #buy
                    app.placeOrder(app.nextorderId, Stock_Contract(), Stock_Order('BUY'))
                    position = -AMOUNT_OF_SHARES
                    app.nextorderId += 1
                elif position == 0 and curRSI >= UPPER_THRESHOLD:
                    #sell
                    app.placeOrder(app.nextorderId, Stock_Contract(), Stock_Order('SELL'))
                    position = AMOUNT_OF_SHARES
                    app.nextorderId += 1

                execution_time += 120
                time.sleep(115)

            cursec = fetchCurrentSecond()
            curTime = datetime.now()
            if curTime.hour <= 4:
                break
            curRSI = GetRSI(tickers)
            print("Current Time: ", curTime,"; Current sec: ", cursec)
            print(curRSI)
            print("Current Pos =", position)

    if curTime.hour <= 4:
        execution_time = 0*3600 + 0*60 + 59 #inital execution time, set to 00:00:59
        while (curTime.hour <= 4):
            if cursec == execution_time: 
                if position > 0 and curRSI <= 50:
                    #close my sell pos
                    app.placeOrder(app.nextorderId, Stock_Contract(), Stock_Order('BUY'))
                    position = 0
                    app.nextorderId += 1
                elif position < 0 and curRSI >= 50:
                    #close my buy pos
                    app.placeOrder(app.nextorderId, Stock_Contract(), Stock_Order('SELL'))
                    position = 0
                    app.nextorderId += 1
                elif position == 0 and curRSI <= LOWER_THRESHOLD:
                    #buy
                    app.placeOrder(app.nextorderId, Stock_Contract(), Stock_Order('BUY'))
                    position = -AMOUNT_OF_SHARES
                    app.nextorderId += 1
                elif position == 0 and curRSI >= UPPER_THRESHOLD:
                    #sell
                    app.placeOrder(app.nextorderId, Stock_Contract(), Stock_Order('SELL'))
                    position = AMOUNT_OF_SHARES
                    app.nextorderId += 1

                execution_time += 120
                time.sleep(115)

            cursec = fetchCurrentSecond()
            curTime = datetime.now()
            curRSI = GetRSI(tickers)
            print("Current Time: ", curTime,"; Current sec: ", cursec)
            print(curRSI)
            print("Current Pos =", position)

            if cursec == 14399: #set to 03:59:59
                if position > 0:
                    app.placeOrder(app.nextorderId, Stock_Contract(), Stock_Order('BUY'))
                    app.nextorderId += 1
                elif position < 0:
                    app.placeOrder(app.nextorderId, Stock_Contract(), Stock_Order('SELL'))
                    app.nextorderId += 1
                break

            
        

    time.sleep(0.5)
    app.disconnect()
