import yfinance as yf
import pandas as pd
import numpy as np
import pandas_datareader.data as web

def get_vol_signal(data, n=20, buy_threshold=1.5, sell_threshold=0.5):
    """
    根據成交量指標生成交易信號
    :param data: 包含'Volume'列的股票數據DataFrame
    :param n: 成交量平均值的計算周期,默認為20
    :param buy_threshold: 買入閾值,默認為1.5
    :param sell_threshold: 賣出閾值,默認為0.5
    :return: 包含交易信號的DataFrame
    """
    vol_avg = data['Volume'].rolling(window=n).mean()
    vol_ratio = data['Volume'] / vol_avg
    
    signal = pd.DataFrame(index=data.index, columns=['Signal'])
    buy_signal = vol_ratio > buy_threshold
    sell_signal = vol_ratio < sell_threshold
    
    signal['Signal'] = np.where(buy_signal, 'Buy', np.where(sell_signal, 'Sell', ''))
    return signal

def get_stock_data(symbol, period="max"):
    """
    從Yahoo Finance下載股票數據
    :param symbol: 股票代碼
    :param period: 數據期間,默認為"max"
    :return: 包含股票數據的DataFrame
    """
    return yf.download(symbol, period=period)

def get_tradable_stocks(symbols, n=20, buy_threshold=1.5, sell_threshold=0.5):
    """
    根據成交量指標篩選可交易的股票
    :param symbols: 股票代碼列表
    :param n: 成交量平均值的計算周期,默認為20
    :param buy_threshold: 買入閾值,默認為1.5
    :param sell_threshold: 賣出閾值,默認為0.5
    :return: 可買入和可賣出的股票列表
    """
    buyable_stocks = []
    sellable_stocks = []
    for symbol in symbols:
        try:
            data = get_stock_data(symbol)
            signal = get_vol_signal(data, n, buy_threshold, sell_threshold)
            if not signal.empty:  # 檢查是否有交易信號
                if signal['Signal'].iloc[-1] == 'Buy':  # 使用.iloc訪問最後一個元素
                    buyable_stocks.append(symbol)
                elif signal['Signal'].iloc[-1] == 'Sell':
                    sellable_stocks.append(symbol)
        except Exception as e:
            print(f"Error processing {symbol}: {str(e)}")
    return buyable_stocks, sellable_stocks

# 從Wikipedia獲取標普500的成分股列表
table = pd.read_html('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
df = table[0]
all_symbols = df['Symbol'].tolist()

# 應用範例
buyable, sellable = get_tradable_stocks(all_symbols)
print(f"可買入的股票: {buyable}")
print(f"可賣出的股票: {sellable}")