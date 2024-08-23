import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import time
import logging
import functools
from multiprocessing import cpu_count
import requests
from io import StringIO

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@functools.lru_cache(maxsize=None)
def get_all_listed_us_stocks():
    """
    Get the list of all currently listed US stocks from NASDAQ Traded List
    """
    url = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt"
    try:
        response = requests.get(url)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text), sep='|')
        df = df[df['ETF'] == 'N']  # Exclude ETFs
        df = df[df['Financial Status'] != 'D']  # Exclude deficient stocks
        df = df[df['Test Issue'] == 'N']  # Exclude test issues
        symbols = df['Symbol'].tolist()
        logging.info(f"Fetched {len(symbols)} symbols from NASDAQ Traded List")
        return tuple(symbols)
    except Exception as e:
        logging.error(f"Error fetching symbols from NASDAQ Traded List: {e}")
        return tuple()

def get_kdj(data, n=9, m1=3, m2=3):
    """
    Calculate KDJ indicator for given stock data
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
    Generate trading signals based on KDJ indicator
    """
    kdj_data = get_kdj(data)
    k_cross_above_d = (kdj_data['K'].shift(1) <= kdj_data['D'].shift(1)) & (kdj_data['K'] > kdj_data['D'])
    k_cross_below_d = (kdj_data['K'].shift(1) >= kdj_data['D'].shift(1)) & (kdj_data['K'] < kdj_data['D'])
    j_above_buy_threshold = kdj_data['J'] > buy_threshold
    j_below_sell_threshold = kdj_data['J'] < sell_threshold
    
    buy_signal = k_cross_above_d & j_above_buy_threshold
    sell_signal = k_cross_below_d & j_below_sell_threshold
    
    return pd.Series(np.select([buy_signal, sell_signal], ['Buy', 'Sell'], ''), index=data.index)

def get_stock_data(symbol, period="max"):
    """
    Download stock data from Yahoo Finance
    """
    try:
        data = yf.download(symbol, period=period)
        return data
    except Exception as e:
        logging.error(f"Error fetching data for {symbol}: {str(e)}")
        return pd.DataFrame()

def process_stock(symbol, buy_threshold=20, sell_threshold=80):
    try:
        data = get_stock_data(symbol)
        if not data.empty and len(data) > 30:
            signal = get_signal(data, buy_threshold, sell_threshold)
            last_signals = signal.tail(5)
            if 'Buy' in last_signals.values:
                return symbol, 'Buy'
            elif 'Sell' in last_signals.values:
                return symbol, 'Sell'
    except Exception as e:
        logging.error(f"Error processing {symbol}: {str(e)}")
    return symbol, None

def get_tradable_stocks(buy_threshold=20, sell_threshold=80):
    all_stocks = get_all_listed_us_stocks()
    results = []
    
    with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
        futures = [executor.submit(process_stock, symbol, buy_threshold, sell_threshold) for symbol in all_stocks]
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing stocks"):
            result = future.result()
            if result[1] is not None:
                results.append(result)
    
    buyable_stocks = [symbol for symbol, signal in results if signal == 'Buy']
    sellable_stocks = [symbol for symbol, signal in results if signal == 'Sell']
    
    return buyable_stocks, sellable_stocks

# Main program
if __name__ == "__main__":
    logging.info("Starting KDJ analysis")
    start_time = time.time()
    
    buyable, sellable = get_tradable_stocks()
    
    logging.info(f"KDJ Buyable Stocks: {buyable}")
    logging.info(f"KDJ Sellable Stocks: {sellable}")
    
    end_time = time.time()
    logging.info(f"Analysis completed. Execution time: {end_time - start_time:.2f} seconds")

# Reference: https://tw.stock.yahoo.com/news/%E6%8A%80%E8%A1%93%E5%88%86%E6%9E%90-kdj%E6%8C%87%E6%A8%99-%E8%82%A1%E7%A5%A8%E8%B6%85%E8%B2%B7%E8%B6%85%E8%B3%A3-%E8%82%A1%E5%83%B9%E8%BD%89%E6%8A%98%E9%BB%9E-%E8%B2%B7%E8%B3%A3%E8%A8%8A%E8%99%9F-133421567.html