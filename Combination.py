import yfinance as yf
import pandas as pd
import numpy as np
import pandas_datareader.data as web

def get_rsi(data, period=14):
    delta = data['Adj Close'].diff()
    up = delta.where(delta > 0, 0)
    down = -delta.where(delta < 0, 0)
    avg_gain = up.rolling(window=period).mean()
    avg_loss = down.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return pd.DataFrame({'RSI': rsi}, index=data.index)

def get_macd(data, short_period=12, long_period=26, signal_period=9):
    short_ema = data['Adj Close'].ewm(span=short_period, adjust=False).mean()
    long_ema = data['Adj Close'].ewm(span=long_period, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=signal_period, adjust=False).mean()
    return pd.DataFrame({'MACD': macd, 'Signal': signal}, index=data.index)

def get_kdj(data, n=9, m1=3, m2=3):
    low_min = data['Low'].rolling(window=n).min()
    high_max = data['High'].rolling(window=n).max()
    rsv = (data['Close'] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(span=m1, adjust=False).mean()
    d = k.ewm(span=m2, adjust=False).mean()
    j = 3 * k - 2 * d
    return pd.DataFrame({'K': k, 'D': d, 'J': j}, index=data.index)

def get_vol_signal(data, n=20, buy_threshold=1.5, sell_threshold=0.5):
    vol_avg = data['Volume'].rolling(window=n).mean()
    vol_ratio = data['Volume'] / vol_avg
    signal = pd.DataFrame(index=data.index, columns=['Vol_Signal'])
    buy_signal = vol_ratio > buy_threshold
    sell_signal = vol_ratio < sell_threshold
    signal['Vol_Signal'] = np.where(buy_signal, 'Buy', np.where(sell_signal, 'Sell', ''))
    return signal

def get_signal(data, rsi_buy=30, rsi_sell=70, macd_buy=0, macd_sell=0, kdj_buy=20, kdj_sell=80, vol_buy=1.5, vol_sell=0.5, use_rsi=True, use_macd=True, use_kdj=True, use_vol=True):
    signal = pd.DataFrame(index=data.index, columns=['Signal'])
    
    if use_rsi:
        rsi = get_rsi(data)
        rsi_buy_signal = rsi['RSI'] < rsi_buy
        rsi_sell_signal = rsi['RSI'] > rsi_sell
    else:
        rsi_buy_signal = pd.Series(True, index=data.index)
        rsi_sell_signal = pd.Series(False, index=data.index)
    
    if use_macd:
        macd = get_macd(data)
        macd_buy_signal = (macd['MACD'] > macd_buy) & (macd['MACD'] > macd['Signal'])
        macd_sell_signal = (macd['MACD'] < macd_sell) & (macd['MACD'] < macd['Signal'])
    else:
        macd_buy_signal = pd.Series(True, index=data.index)
        macd_sell_signal = pd.Series(False, index=data.index)
    
    if use_kdj:
        kdj = get_kdj(data)
        kdj_buy_signal = (kdj['K'] > kdj_buy) & (kdj['K'] > kdj['D']) & (kdj['J'] > kdj_buy)
        kdj_sell_signal = (kdj['K'] < kdj_sell) & (kdj['K'] < kdj['D']) & (kdj['J'] < kdj_sell)
    else:
        kdj_buy_signal = pd.Series(True, index=data.index)
        kdj_sell_signal = pd.Series(False, index=data.index)
    
    if use_vol:
        vol = get_vol_signal(data, buy_threshold=vol_buy, sell_threshold=vol_sell)
        vol_buy_signal = vol['Vol_Signal'] == 'Buy'
        vol_sell_signal = vol['Vol_Signal'] == 'Sell'
    else:
        vol_buy_signal = pd.Series(True, index=data.index)
        vol_sell_signal = pd.Series(False, index=data.index)
    
    buy_signal = rsi_buy_signal & macd_buy_signal & kdj_buy_signal & vol_buy_signal
    sell_signal = rsi_sell_signal & macd_sell_signal & kdj_sell_signal & vol_sell_signal
    
    signal['Signal'] = np.where(buy_signal, 'Buy', np.where(sell_signal, 'Sell', ''))
    return signal

def get_stock_data(symbol, start_date=None, end_date=None):
    try:
        data = yf.download(symbol, start=start_date, end=end_date)
        if data.empty:
            print(f"No data found for {symbol}")
            return None
        return data
    except Exception as e:
        print(f"Error downloading data for {symbol}: {str(e)}")
        return None

def get_tradable_stocks(symbols, start_date, end_date, rsi_buy=30, rsi_sell=70, macd_buy=0, macd_sell=0, kdj_buy=20, kdj_sell=80, vol_buy=1.5, vol_sell=0.5, use_rsi=True, use_macd=True, use_kdj=True, use_vol=True):
    buyable_stocks = []
    sellable_stocks = []
    for symbol in symbols:
        data = get_stock_data(symbol, start_date, end_date)
        if data is None or len(data) < 60:  # 確保有足夠的數據點
            continue
        signal = get_signal(data, rsi_buy, rsi_sell, macd_buy, macd_sell, kdj_buy, kdj_sell, vol_buy, vol_sell, use_rsi, use_macd, use_kdj, use_vol)
        if not signal.empty and signal['Signal'].iloc[-1] == 'Buy':
            buyable_stocks.append(symbol)
        elif not signal.empty and signal['Signal'].iloc[-1] == 'Sell':
            sellable_stocks.append(symbol)
    return buyable_stocks, sellable_stocks

# 從Wikipedia獲取標普500的成分股列表
table = pd.read_html('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
df = table[0]
all_symbols = df['Symbol'].tolist()

# 選擇前200個股票進行測試
test_symbols = all_symbols[:200]

# 設定資料的開始和結束日期
start_date = '2022-01-01'
end_date = '2023-05-29'

# 應用範例
buyable, sellable = get_tradable_stocks(test_symbols, start_date, end_date, rsi_buy=30, rsi_sell=70, macd_buy=0, macd_sell=0, kdj_buy=20, kdj_sell=80, vol_buy=1.5, vol_sell=0.5, use_rsi=True, use_macd=True, use_kdj=True, use_vol=True)
print(f"可買入的股票: {buyable}")
print(f"可賣出的股票: {sellable}")