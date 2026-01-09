"""
Data handler for fetching and preparing market data
"""
import yfinance as yf
import pandas as pd
import backtrader as bt
from datetime import datetime


class DataHandler:
    """Handle data downloading and preparation"""
    
    def __init__(self, symbols, start_date, end_date):
        self.symbols = symbols if isinstance(symbols, list) else [symbols]
        self.start_date = start_date
        self.end_date = end_date
        self.data = {}
        
    def download_data(self, symbol):
        """Download data for a single symbol"""
        print(f"Downloading data for {symbol}...")
        try:
            data = yf.download(
                symbol,
                start=self.start_date,
                end=self.end_date,
                progress=False
            )
            
            if data.empty:
                print(f"Warning: No data downloaded for {symbol}")
                return None
                
            # Flatten multi-index columns if present
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
                
            self.data[symbol] = data
            print(f"Downloaded {len(data)} bars for {symbol}")
            return data
            
        except Exception as e:
            print(f"Error downloading {symbol}: {e}")
            return None
            
    def download_all(self):
        """Download data for all symbols"""
        for symbol in self.symbols:
            self.download_data(symbol)
        return self.data
        
    def get_backtrader_feed(self, symbol):
        """Convert pandas data to backtrader feed"""
        if symbol not in self.data or self.data[symbol] is None:
            return None
            
        return bt.feeds.PandasData(
            dataname=self.data[symbol],
            name=symbol
        )
        
    def get_all_feeds(self):
        """Get backtrader feeds for all symbols"""
        feeds = {}
        for symbol in self.symbols:
            feed = self.get_backtrader_feed(symbol)
            if feed is not None:
                feeds[symbol] = feed
        return feeds
        
    def save_data(self, filepath):
        """Save downloaded data to CSV"""
        for symbol, data in self.data.items():
            if data is not None:
                filename = f"{filepath}/{symbol}.csv"
                data.to_csv(filename)
                print(f"Saved {symbol} to {filename}")
                
    def load_data(self, filepath, symbol):
        """Load data from CSV"""
        try:
            filename = f"{filepath}/{symbol}.csv"
            data = pd.read_csv(filename, index_col=0, parse_dates=True)
            self.data[symbol] = data
            print(f"Loaded {symbol} from {filename}")
            return data
        except Exception as e:
            print(f"Error loading {symbol}: {e}")
            return None
