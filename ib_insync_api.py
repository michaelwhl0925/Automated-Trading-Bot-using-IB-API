from pickle import FALSE
from ib_insync import *
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import time

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
    df = yf.download(tickers, period = '60d', interval = '30m')
    prices = df['Adj Close']
    rsi_df = RSI(prices,14)
    return rsi_df[-1], np.mean(rsi_df), np.std(rsi_df)

def fetchCurrentSecond():
    curTime = datetime.now()
    return curTime.hour * 3600 + curTime.minute * 60 + curTime.second

if __name__ == "__main__":
    MAKRET_OPEN = 21*3600+30*60 #77400
    MARKET_CLOSE = 4*3600
    THRESHOLD = 1
    AMOUNT_OF_SHARES = 10
    tickers = ['TSLA']
    list = [0]

    ib = IB()
    ib.connect('127.0.0.1', 7497, clientId=1)
    account_summary = ib.accountSummary(account='DU4900120')
    account_summary_df = pd.DataFrame(account_summary).set_index('tag')
    #print(account_summary_df)

    position_df = pd.DataFrame(ib.positions()).set_index('contract')
    position = 0
    for value in position_df.index.values:
        if value.symbol == 'TSLA':
            position = float(position_df.loc[value,'position'])
    
    contract = Contract(secType='STK',symbol='TSLA',exchange='SMART',currency='USD')
    buy_order = Order(action='BUY',totalQuantity=AMOUNT_OF_SHARES,orderType='MKT')
    sell_order = Order(action='SELL',totalQuantity=AMOUNT_OF_SHARES,orderType='MKT')
    #ib.placeOrder(contract, order)
    FLAG = True
    while FLAG:
        cursec = fetchCurrentSecond()
        print(cursec)
        time.sleep(1)
        if cursec >= MAKRET_OPEN + 1:
            for i in range(14):  
                CurrentRSI, RSI_MEAN, RSI_STD = GetRSI(tickers)
                print(CurrentRSI, RSI_MEAN, RSI_STD)
                current_zscore = (CurrentRSI - RSI_MEAN)/ RSI_STD
                list.append(current_zscore)
                print('current_zscore = ', list[-1])
                print('prev zscore = ', list[-2])
                print('list =', list)

                if current_zscore > THRESHOLD and position == 0:
                    ib.placeOrder(contract, sell_order)
                    position = -AMOUNT_OF_SHARES
                elif current_zscore < -THRESHOLD and position == 0:
                    ib.placeOrder(contract, buy_order)
                    position = AMOUNT_OF_SHARES
                elif position < 0:
                    if (list[-1] * list[-2]) < 0:
                        ib.placeOrder(contract, buy_order)
                        position = 0
                elif position > 0:
                    if (list[-1] * list[-2]) < 0:
                        ib.placeOrder(contract, sell_order)
                        position = 0

                print("Current Pos =", position)
                list.pop(0)
                time.sleep(1800)
                if i == 13:
                    FLAG = False
                    break
            
    
    print(ib.executions)