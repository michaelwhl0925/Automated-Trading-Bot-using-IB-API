from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import *

import pandas as pd
import threading
import time
import numpy as np
import yfinance as yf
from datetime import datetime
import time
 
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

def GetRSI(tickers):
    df = yf.download(tickers, period = '60d', interval = '15m')
    prices = df['Adj Close']
    rsi_df = RSI(prices,14)
    return rsi_df[-1]

def fetchCurrentSecond():
    curTime = datetime.now()
    return curTime.hour * 3600 + curTime.minute * 60 + curTime.second

def TSLA_Contract():
    contract = Contract()
    contract.symbol = 'TSLA'
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    return contract

def TSLA_Order(direction):
    order = Order()
    order.action = direction
    order.totalQuantity = 100
    order.orderType = 'MKT'
    order.eTradeOnly = False
    order.firmQuoteOnly = False
    return order

if __name__ == "__main__":
    MAKRET_OPEN = 22*3600+30*60 #77400
    THRESHOLD = 1
    AMOUNT_OF_SHARES = 100
    tickers = ['TSLA']

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
            time.sleep(1)
    

    app.reqPositions()
    time.sleep(3)
    try:
        position = app.all_positions.loc["TSLA","Quantity"]
    except BaseException:
        position = 0

    #Place order
    FLAG = True
    while FLAG:
        time.sleep(1)
        cursec = fetchCurrentSecond()
        print(cursec)
        print("Current Time: ", datetime.now())
        if cursec >= 0:
            for i in range(48):  
                curRSI = GetRSI(tickers)
                print(curRSI)
                print("Current Time: ", datetime.now())
                if position > 0 and curRSI >= 50:
                    #sell close
                    print(app.nextorderId)
                    app.placeOrder(app.nextorderId, TSLA_Contract(), TSLA_Order('SELL'))
                    position = 0
                elif position < 0 and curRSI <= 50:
                    #buy close
                    app.placeOrder(app.nextorderId, TSLA_Contract(), TSLA_Order('BUY'))
                    position = 0
                elif position == 0 and curRSI <= 30:
                    #buy
                    app.placeOrder(app.nextorderId, TSLA_Contract(), TSLA_Order('BUY'))
                    position = -AMOUNT_OF_SHARES
                elif position == 0 and curRSI >= 70:
                    #sell
                    app.placeOrder(app.nextorderId, TSLA_Contract(), TSLA_Order('SELL'))
                    position = AMOUNT_OF_SHARES

                print("Current Pos =", position)
                time.sleep(900)
                if i == 47:
                    FLAG = False
                    break

    app.disconnect()
