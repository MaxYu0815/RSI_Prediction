import yfinance as yf
import pandas as pd
import numpy as np
import pandas_datareader.data as web

def get_kdj(data, n=9, m1=3, m2=3):
    """
    計算給定股票數據的KDJ指標
    :param data: 包含'High', 'Low', 'Close'列的股票數據DataFrame
    :param n: KDJ指標的計算周期,默認為9
    :param m1: K值的平滑周期,默認為3
    :param m2: D值的平滑周期,默認為3
    :return: 包含K值、D值和J值的DataFrame
    """
    low_min = data['Low'].rolling(window=n).min()
    high_max = data['High'].rolling(window=n).max()
    rsv = (data['Close'] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(span=m1, adjust=False).mean()
    d = k.ewm(span=m2, adjust=False).mean()
    j = 3 * k - 2 * d
    return pd.DataFrame({'K': k, 'D': d, 'J': j}, index=data.index)

def get_signal(data, buy_threshold=20, sell_threshold=80):
    """
    根據KDJ指標生成交易信號
    :param data: 包含'High', 'Low', 'Close'列的股票數據DataFrame
    :param buy_threshold: 買入閾值,默認為20
    :param sell_threshold: 賣出閾值,默認為80
    :return: 包含交易信號的DataFrame
    """
    kdj_data = get_kdj(data)
    signal = pd.DataFrame(index=kdj_data.index, columns=['Signal'])
    
    # 判斷K值和D值的交叉情況以及J值的位置
    k_cross_above_d = (kdj_data['K'].shift(1) <= kdj_data['D'].shift(1)) & (kdj_data['K'] > kdj_data['D'])
    k_cross_below_d = (kdj_data['K'].shift(1) >= kdj_data['D'].shift(1)) & (kdj_data['K'] < kdj_data['D'])
    j_above_buy_threshold = kdj_data['J'] > buy_threshold
    j_below_sell_threshold = kdj_data['J'] < sell_threshold
    
    buy_signal = k_cross_above_d & j_above_buy_threshold
    sell_signal = k_cross_below_d & j_below_sell_threshold
    
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

def get_tradable_stocks(symbols, buy_threshold=20, sell_threshold=80):
    """
    根據KDJ指標篩選可交易的股票
    :param symbols: 股票代碼列表
    :param buy_threshold: 買入閾值,默認為20
    :param sell_threshold: 賣出閾值,默認為80
    :return: 可買入和可賣出的股票列表
    """
    buyable_stocks = []
    sellable_stocks = []
    for symbol in symbols:
        try:
            data = get_stock_data(symbol)
            signal = get_signal(data, buy_threshold, sell_threshold)
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
