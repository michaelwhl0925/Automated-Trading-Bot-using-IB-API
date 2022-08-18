from ib.ext.Contract import Contract
from ib.ext.Order import Order
from ib.opt import Connection, message
from ib_insync import util
import time
import pandas as pd
import yfinance as yf
import numpy as np


def error_handler(msg):
    print("Server Error: %s" % msg)

def reply_handler(msg):
    print("Server Response: %s, %s" % (msg.typeName, msg))

def RSI(series, period):
    delta = series.diff().dropna()
    u = delta * 0
    d = u.copy()
    u[delta > 0] = delta[delta > 0]
    d[delta < 0] = -delta[delta < 0]
    u[u.index[period-1]] = np.mean( u[:period] ) #first value is sum of avg gains
    u = u.drop(u.index[:(period-1)])
    d[d.index[period-1]] = np.mean( d[:period] ) #first value is sum of avg losses
    d = d.drop(d.index[:(period-1)])
    rs = u.ewm(com=period-1, adjust=False).mean() / d.ewm(com=period-1, adjust=False).mean()
    return 100 - 100 / (1 + rs)


def GetRSI(tickers):
    df = yf.download(tickers, period = '1d', interval = '1m')
    prices = df['Adj Close']
    rsi_df = RSI(prices,14)
    return rsi_df[-1], np.mean(rsi_df), np.std(rsi_df)


def create_contract(symbol, sec_type, exch, curr):
    contract = Contract()
    contract.m_symbol = symbol
    contract.m_secType = sec_type
    contract.m_exchange = exch
    #contract.m_primaryExch = prim_exch
    contract.m_currency = curr
    return contract


def create_order(order_type, quantity, action):
    order = Order()
    order.m_orderType = order_type
    order.m_totalQuantity = quantity
    order.m_action = action
    return order

if __name__ == "__main__":
    ORDER_ID = 1
    THRESHOLD = 0.1
    AMOUNT_OF_SHARES = 10
    position = 0
    tickers = ['EURUSD=X']
    list = [0]

    ib = Connection.create(port=7497, clientId=1)
    ib.connect()

    ib.register(error_handler, 'Error')
    ib.registerAll(reply_handler)

    contract = create_contract('EUR', 'CASH', 'IDEALPRO', 'USD')
    #contract = create_contract('700', 'STK', 'SEHK', 'HKD')
    #contract = create_contract('ETH', 'CRYPTO', 'PAXOS', 'USD')

    buy_order = create_order('MKT', AMOUNT_OF_SHARES, 'BUY')
    sell_order = create_order('MKT', AMOUNT_OF_SHARES, 'SELL')
    
    for i in range(100):
        ORDER_ID += 1    
        CurrentRSI, RSI_MEAN, RSI_STD = GetRSI(tickers)
        print(CurrentRSI, RSI_MEAN, RSI_STD)
        current_zscore = (CurrentRSI - RSI_MEAN)/ RSI_STD
        list.append(current_zscore)
        print('current_zscore = ', list[-1])
        print('prev zscore = ', list[-2])
        print('list =', list)


        if current_zscore > THRESHOLD and position == 0:
            ib.placeOrder(ORDER_ID, contract, sell_order)
            position = -AMOUNT_OF_SHARES
        elif current_zscore < -THRESHOLD and position == 0:
            ib.placeOrder(ORDER_ID, contract, buy_order)
            position = AMOUNT_OF_SHARES
        elif position < 0:
            if (list[-1] * list[-2]) < 0:
                ib.placeOrder(ORDER_ID, contract, buy_order)
                position = 0
        elif position > 0:
            if (list[-1] * list[-2]) < 0:
                ib.placeOrder(ORDER_ID, contract, sell_order)
                position = 0


        
        print("Current Pos =", position)
        list.pop(0)
        time.sleep(3600)


ib.disconnect()


print("\n")
print("------------------------------END OF SCRIPT------------------------------")