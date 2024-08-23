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

def get_macd(data, short_period=12, long_period=26, signal_period=9):
    """
    Calculate MACD indicator for given stock data
    """
    short_ema = data['Adj Close'].ewm(span=short_period, adjust=False).mean()
    long_ema = data['Adj Close'].ewm(span=long_period, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=signal_period, adjust=False).mean()
    return pd.DataFrame({'MACD': macd, 'Signal': signal}, index=data.index)

def get_signal(data):
    """
    Generate trading signals based on MACD indicator
    """
    macd_data = get_macd(data)
    macd_cross_above = (macd_data['MACD'].shift(1) <= macd_data['Signal'].shift(1)) & (macd_data['MACD'] > macd_data['Signal'])
    macd_cross_below = (macd_data['MACD'].shift(1) >= macd_data['Signal'].shift(1)) & (macd_data['MACD'] < macd_data['Signal'])
    
    return pd.Series(np.select([macd_cross_above, macd_cross_below], ['Buy', 'Sell'], ''), index=data.index)

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

def process_stock(symbol):
    try:
        data = get_stock_data(symbol)
        if not data.empty and len(data) > 30:
            signal = get_signal(data)
            last_signals = signal.tail(5)
            if 'Buy' in last_signals.values:
                return symbol, 'Buy'
            elif 'Sell' in last_signals.values:
                return symbol, 'Sell'
    except Exception as e:
        logging.error(f"Error processing {symbol}: {str(e)}")
    return symbol, None

def get_tradable_stocks():
    all_stocks = get_all_listed_us_stocks()
    results = []
    
    with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
        futures = [executor.submit(process_stock, symbol) for symbol in all_stocks]
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing stocks"):
            result = future.result()
            if result[1] is not None:
                results.append(result)
    
    buyable_stocks = [symbol for symbol, signal in results if signal == 'Buy']
    sellable_stocks = [symbol for symbol, signal in results if signal == 'Sell']
    
    return buyable_stocks, sellable_stocks

# Main program
if __name__ == "__main__":
    logging.info("Starting MACD analysis")
    start_time = time.time()
    
    buyable, sellable = get_tradable_stocks()
    
    logging.info(f"MACD Buyable Stocks: {buyable}")
    logging.info(f"MACD Sellable Stocks: {sellable}")
    
    end_time = time.time()
    logging.info(f"Analysis completed. Execution time: {end_time - start_time:.2f} seconds")

# Reference: https://www.sinotrade.com.tw/richclub/Financialfreedom/MACD%E6%8C%87%E6%A8%99%E6%98%AF%E4%BB%80%E9%BA%BC-%E8%82%A1%E7%A5%A8%E8%B2%B7%E8%B3%A3%E9%BB%9E%E6%80%8E%E9%BA%BC%E7%9C%8B--%E6%96%B0%E6%89%8B%E6%8A%80%E8%A1%93%E5%88%86%E6%9E%90-651b71353ba60776b8aab818