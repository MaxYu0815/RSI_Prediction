import yfinance as yf
import pandas as pd
import numpy as np
import pandas_datareader.data as web

def get_macd(data, short_period=12, long_period=26, signal_period=9):
    """
    計算給定股票數據的MACD指標
    :param data: 包含'Adj Close'列的股票數據DataFrame
    :param short_period: 短期EMA計算周期,默認為12
    :param long_period: 長期EMA計算周期,默認為26
    :param signal_period: 信號線計算周期,默認為9
    :return: 包含MACD值的DataFrame
    """
    short_ema = data['Adj Close'].ewm(span=short_period, adjust=False).mean()
    long_ema = data['Adj Close'].ewm(span=long_period, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=signal_period, adjust=False).mean()
    return pd.DataFrame({'MACD': macd, 'Signal': signal}, index=data.index)

def get_signal(data):
    """
    根據MACD指標生成交易信號
    :param data: 包含'Adj Close'列的股票數據DataFrame
    :return: 包含交易信號的DataFrame
    """
    macd_data = get_macd(data)
    signal = pd.DataFrame(index=macd_data.index, columns=['Signal'])
    
    # 判斷MACD值和信號線的交叉情況
    macd_cross_above = (macd_data['MACD'].shift(1) <= macd_data['Signal'].shift(1)) & (macd_data['MACD'] > macd_data['Signal'])
    macd_cross_below = (macd_data['MACD'].shift(1) >= macd_data['Signal'].shift(1)) & (macd_data['MACD'] < macd_data['Signal'])
    
    signal['Signal'] = np.where(macd_cross_above, 'Buy', np.where(macd_cross_below, 'Sell', ''))
    return signal

def get_stock_data(symbol, period="max"):
    """
    從Yahoo Finance下載股票數據
    :param symbol: 股票代碼
    :param period: 數據期間,默認為"max"
    :return: 包含股票數據的DataFrame
    """
    return yf.download(symbol, period=period)

def get_tradable_stocks(symbols):
    """
    根據MACD指標篩選可交易的股票
    :param symbols: 股票代碼列表
    :return: 可買入和可賣出的股票列表
    """
    buyable_stocks = []
    sellable_stocks = []
    for symbol in symbols:
        try:
            data = get_stock_data(symbol)
            signal = get_signal(data)
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

# reference: https://www.sinotrade.com.tw/richclub/Financialfreedom/MACD%E6%8C%87%E6%A8%99%E6%98%AF%E4%BB%80%E9%BA%BC-%E8%82%A1%E7%A5%A8%E8%B2%B7%E8%B3%A3%E9%BB%9E%E6%80%8E%E9%BA%BC%E7%9C%8B--%E6%96%B0%E6%89%8B%E6%8A%80%E8%A1%93%E5%88%86%E6%9E%90-651b71353ba60776b8aab818