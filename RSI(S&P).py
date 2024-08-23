import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import time
import logging
import requests
from io import StringIO
import functools
from multiprocessing import cpu_count

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@functools.lru_cache(maxsize=None)
def get_sp500_symbols():
    """
    Get the list of S&P 500 stock symbols
    """
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    for _ in range(3):  # Retry 3 times
        try:
            tables = pd.read_html(url)
            df = tables[0]
            return tuple(df['Symbol'].tolist())
        except Exception as e:
            logging.error(f"Error fetching S&P 500 list: {e}")
            time.sleep(5)  # Wait 5 seconds before retrying
    return tuple()

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

def get_rsi(data, period=14):
    """
    Calculate RSI indicator
    """
    delta = data['Adj Close'].diff()
    up = delta.where(delta > 0, 0)
    down = -delta.where(delta < 0, 0)
    avg_gain = up.rolling(window=period).mean()
    avg_loss = down.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def process_stock(symbol, buy_threshold=20, sell_threshold=80):
    try:
        data = get_stock_data(symbol)
        if not data.empty and len(data) > 30:
            rsi = get_rsi(data)
            last_rsi = rsi.iloc[-1]
            
            if last_rsi < buy_threshold:
                return symbol, 'Buy'
            elif last_rsi > sell_threshold:
                return symbol, 'Sell'
    except Exception as e:
        logging.error(f"Error processing {symbol}: {str(e)}")
    return symbol, None

def get_tradable_stocks(buy_threshold=20, sell_threshold=80):
    all_stocks = get_sp500_symbols()
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
    logging.info("Starting analysis")
    start_time = time.time()
    
    buyable, sellable = get_tradable_stocks()
    
    logging.info(f"RSI Buyable Stocks: {buyable}")
    logging.info(f"RSI Sellable Stocks: {sellable}")
    
    end_time = time.time()
    logging.info(f"Analysis completed. Execution time: {end_time - start_time:.2f} seconds")