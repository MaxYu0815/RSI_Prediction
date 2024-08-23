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

def get_vol_signal(data, n=20, buy_threshold=1.5, sell_threshold=0.5):
    """
    Generate trading signals based on volume indicator
    """
    vol_avg = data['Volume'].rolling(window=n).mean()
    vol_ratio = data['Volume'] / vol_avg
    
    buy_signal = vol_ratio > buy_threshold
    sell_signal = vol_ratio < sell_threshold
    
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

def process_stock(symbol, n=20, buy_threshold=1.5, sell_threshold=0.5):
    try:
        data = get_stock_data(symbol)
        if not data.empty and len(data) > 30:
            signal = get_vol_signal(data, n, buy_threshold, sell_threshold)
            last_signals = signal.tail(5)
            if 'Buy' in last_signals.values:
                return symbol, 'Buy'
            elif 'Sell' in last_signals.values:
                return symbol, 'Sell'
    except Exception as e:
        logging.error(f"Error processing {symbol}: {str(e)}")
    return symbol, None

def get_tradable_stocks(n=20, buy_threshold=1.5, sell_threshold=0.5):
    all_stocks = get_all_listed_us_stocks()
    results = []
    
    with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
        futures = [executor.submit(process_stock, symbol, n, buy_threshold, sell_threshold) for symbol in all_stocks]
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing stocks"):
            result = future.result()
            if result[1] is not None:
                results.append(result)
    
    buyable_stocks = [symbol for symbol, signal in results if signal == 'Buy']
    sellable_stocks = [symbol for symbol, signal in results if signal == 'Sell']
    
    return buyable_stocks, sellable_stocks

# Main program
if __name__ == "__main__":
    logging.info("Starting Volume analysis")
    start_time = time.time()
    
    buyable, sellable = get_tradable_stocks()
    
    logging.info(f"Volume Buyable Stocks: {buyable}")
    logging.info(f"Volume Sellable Stocks: {sellable}")
    
    end_time = time.time()
    logging.info(f"Analysis completed. Execution time: {end_time - start_time:.2f} seconds")