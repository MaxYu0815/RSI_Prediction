import yfinance as yf
import pandas as pd
import numpy as np
import pandas_datareader.data as web

def get_rsi(data, period=14):
    """
    計算給定股票數據的RSI指標
    :param data: 包含'Adj Close'列的股票數據DataFrame
    :param period: RSI計算周期,默認為14
    :return: 包含RSI值的DataFrame
    """
    delta = data['Adj Close'].diff()
    up = delta.where(delta > 0, 0)
    down = -delta.where(delta < 0, 0)
    avg_gain = up.rolling(window=period).mean()
    avg_loss = down.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return pd.DataFrame({'RSI': rsi}, index=data.index)

def get_signal(data, buy_threshold=30, sell_threshold=70):
    """
    根據RSI指標生成交易信號
    :param data: 包含'Adj Close'列的股票數據DataFrame
    :param buy_threshold: 買入閾值,默認為30
    :param sell_threshold: 賣出閾值,默認為70
    :return: 包含交易信號的DataFrame
    """
    rsi = get_rsi(data)
    signal = pd.DataFrame(index=rsi.index, columns=['Signal'])
    signal['Signal'] = np.where(rsi['RSI'] < buy_threshold, 'Buy', np.where(rsi['RSI'] > sell_threshold, 'Sell', ''))
    return signal

def get_stock_data(symbol, period="max"):
    """
    從Yahoo Finance下載股票數據
    :param symbol: 股票代碼
    :param period: 數據期間,默認為"max"
    :return: 包含股票數據的DataFrame
    """
    return yf.download(symbol, period=period)

def get_tradable_stocks(symbols, buy_threshold=30, sell_threshold=70):
    """
    根據RSI指標篩選可交易的股票
    :param symbols: 股票代碼列表
    :param buy_threshold: 買入閾值,默認為30
    :param sell_threshold: 賣出閾值,默認為70
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
table=pd.read_html('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
df = table[0]
all_symbols = df['Symbol'].tolist()

# 應用範例
buyable, sellable = get_tradable_stocks(all_symbols)
print(f"可買入的股票: {buyable}")
print(f"可賣出的股票: {sellable}")
