import numpy as np
import pandas as pd
import logging
import ccxt
import os
import json
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Optional, Union, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Data processor for crypto market making
    
    This class handles loading, processing, and preparing data for market making models.
    It supports both CEX and onchain data sources.
    """
    
    def __init__(self, data_dir="data"):
        """
        Initialize the data processor
        
        Parameters:
            data_dir (str): Directory to store/read data files
        """
        self.data_dir = data_dir
        self.exchange = None
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
    def connect_exchange(self, exchange_id="binance", api_key=None, secret=None):
        """
        Connect to a cryptocurrency exchange
        
        Parameters:
            exchange_id (str): Exchange ID (e.g., 'binance', 'coinbase')
            api_key (str): API key for the exchange
            secret (str): API secret for the exchange
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Initialize exchange connection
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class({
                'apiKey': api_key,
                'secret': secret,
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })
            
            # Test connection
            self.exchange.load_markets()
            logger.info(f"Connected to {exchange_id} successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {exchange_id}: {e}")
            self.exchange = None
            return False
            
    def fetch_historical_data(self, symbol, timeframe='1m', since=None, limit=1000):
        """
        Fetch historical OHLCV data from the connected exchange
        
        Parameters:
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            timeframe (str): Timeframe for candlestick data
            since (int/datetime): Start time as timestamp or datetime
            limit (int): Maximum number of candles to fetch
            
        Returns:
            pd.DataFrame: DataFrame with OHLCV data
        """
        if self.exchange is None:
            logger.error("No exchange connected. Use connect_exchange() first.")
            return pd.DataFrame()
            
        try:
            # Convert datetime to timestamp if needed
            if isinstance(since, datetime):
                since = int(since.timestamp() * 1000)  # Convert to milliseconds
                
            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since, limit)
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Add mid price
            df['mid_price'] = (df['high'] + df['low']) / 2
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch historical data: {e}")
            return pd.DataFrame()
            
    def load_from_file(self, filename):
        """
        Load market data from file
        
        Parameters:
            filename (str): File name to load
            
        Returns:
            pd.DataFrame: DataFrame with market data
        """
        try:
            file_path = os.path.join(self.data_dir, filename)
            
            if filename.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif filename.endswith('.pkl'):
                df = pd.read_pickle(file_path)
            elif filename.endswith('.json'):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                df = pd.DataFrame(data)
            else:
                logger.error(f"Unsupported file format: {filename}")
                return pd.DataFrame()
                
            # Convert timestamp to datetime if it exists
            if 'timestamp' in df.columns:
                if df['timestamp'].dtype == 'object':
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                
            return df
            
        except Exception as e:
            logger.error(f"Failed to load data from file {filename}: {e}")
            return pd.DataFrame()
            
    def save_to_file(self, df, filename):
        """
        Save market data to file
        
        Parameters:
            df (pd.DataFrame): DataFrame to save
            filename (str): File name to save
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            file_path = os.path.join(self.data_dir, filename)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save based on file extension
            if filename.endswith('.csv'):
                df.to_csv(file_path)
            elif filename.endswith('.pkl'):
                df.to_pickle(file_path)
            elif filename.endswith('.json'):
                # Reset index to include timestamp in the JSON
                df_json = df.reset_index().to_dict(orient='records')
                with open(file_path, 'w') as f:
                    json.dump(df_json, f)
            else:
                logger.error(f"Unsupported file format: {filename}")
                return False
                
            logger.info(f"Data saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save data to file {filename}: {e}")
            return False
            
    def process_for_market_making(self, df, volatility_window=20, spread_window=20):
        """
        Process raw market data for market making models
        
        Parameters:
            df (pd.DataFrame): Raw market data
            volatility_window (int): Window size for volatility calculation
            spread_window (int): Window size for spread calculation
            
        Returns:
            pd.DataFrame: Processed DataFrame with additional features
        """
        # Make a copy to avoid modifying the original
        data = df.copy()
        
        # Calculate returns
        if 'close' in data.columns:
            data['returns'] = data['close'].pct_change()
        elif 'mid_price' in data.columns:
            data['returns'] = data['mid_price'].pct_change()
        else:
            logger.warning("No price column found for returns calculation")
            return data
            
        # Calculate volatility (annualized)
        data['volatility'] = data['returns'].rolling(window=volatility_window).std() * np.sqrt(252 * 24 * 60)
        
        # Calculate spread if bid/ask not available
        if 'bid' not in data.columns or 'ask' not in data.columns:
            # Estimate spread from volatility if not available
            data['spread'] = data['volatility'] / 10
        else:
            data['spread'] = (data['ask'] - data['bid']) / data['mid_price']
            
        # Calculate spread moving average
        data['spread_ma'] = data['spread'].rolling(window=spread_window).mean()
        
        # Calculate order imbalance (if available)
        if 'bid_volume' in data.columns and 'ask_volume' in data.columns:
            data['order_imbalance'] = (data['bid_volume'] - data['ask_volume']) / (data['bid_volume'] + data['ask_volume'])
        
        # Fill NaN values
        data = data.fillna(method='bfill')
        
        return data
        
    def simulate_market_data(self, n_periods=1000, initial_price=1000, 
                             volatility=0.01, mean_reversion=0.1, 
                             spread_mean=0.001, spread_std=0.0005,
                             timestamp_start=None, interval_seconds=60):
        """
        Simulate market data for testing and development
        
        Parameters:
            n_periods (int): Number of periods to simulate
            initial_price (float): Initial price
            volatility (float): Volatility parameter
            mean_reversion (float): Mean reversion strength
            spread_mean (float): Mean spread
            spread_std (float): Spread standard deviation
            timestamp_start (datetime): Starting timestamp
            interval_seconds (int): Seconds between periods
            
        Returns:
            pd.DataFrame: Simulated market data
        """
        # Initialize price process
        prices = np.zeros(n_periods)
        prices[0] = initial_price
        
        # Initialize spread process
        spreads = np.random.normal(spread_mean, spread_std, n_periods)
        spreads = np.maximum(spreads, 0.0001)  # Ensure positive spreads
        
        # Generate price process (mean-reverting with jumps)
        for i in range(1, n_periods):
            # Mean reversion component
            mean_rev = mean_reversion * (initial_price - prices[i-1])
            
            # Random component
            random_shock = np.random.normal(0, volatility * prices[i-1])
            
            # Jump component (rare large moves)
            jump = 0
            if np.random.random() < 0.01:  # 1% chance of a jump
                jump = np.random.normal(0, volatility * prices[i-1] * 5)
                
            # Update price
            prices[i] = prices[i-1] + mean_rev + random_shock + jump
            
            # Ensure price is positive
            prices[i] = max(prices[i], 0.01)
        
        # Generate timestamps
        if timestamp_start is None:
            timestamp_start = datetime.now()
            
        timestamps = [timestamp_start + timedelta(seconds=i*interval_seconds) for i in range(n_periods)]
        
        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': timestamps,
            'mid_price': prices,
            'spread': spreads
        })
        
        # Calculate bid/ask prices
        df['bid'] = df['mid_price'] * (1 - df['spread']/2)
        df['ask'] = df['mid_price'] * (1 + df['spread']/2)
        
        # Add OHLC data
        df['open'] = df['mid_price']
        df['high'] = df['mid_price'] * (1 + np.random.uniform(0, 0.005, n_periods))
        df['low'] = df['mid_price'] * (1 - np.random.uniform(0, 0.005, n_periods))
        df['close'] = df['mid_price'] * (1 + np.random.normal(0, 0.001, n_periods))
        df['volume'] = np.random.exponential(100, n_periods)
        
        # Set timestamp as index
        df.set_index('timestamp', inplace=True)
        
        # Process for market making
        df = self.process_for_market_making(df)
        
        return df
        
    def sync_cex_with_onchain(self, cex_data, onchain_data, latency=30):
        """
        Synchronize CEX data with onchain data accounting for latency
        
        Parameters:
            cex_data (pd.DataFrame): CEX market data
            onchain_data (pd.DataFrame): Onchain market data
            latency (int): Onchain latency in seconds
            
        Returns:
            pd.DataFrame: Synchronized data
        """
        # Make copies to avoid modifying originals
        cex = cex_data.copy()
        onchain = onchain_data.copy()
        
        # Ensure both have datetime index
        if not isinstance(cex.index, pd.DatetimeIndex):
            logger.error("CEX data must have a datetime index")
            return pd.DataFrame()
            
        if not isinstance(onchain.index, pd.DatetimeIndex):
            logger.error("Onchain data must have a datetime index")
            return pd.DataFrame()
        
        # Shift onchain data to account for latency
        onchain = onchain.shift(periods=int(latency/onchain.index.freq.delta.total_seconds()))
        
        # Resample both to a common frequency if needed
        common_freq = min(onchain.index.freq, cex.index.freq)
        cex = cex.resample(common_freq).interpolate()
        onchain = onchain.resample(common_freq).interpolate()
        
        # Merge the datasets
        merged = pd.merge(cex, onchain, left_index=True, right_index=True, suffixes=('_cex', '_onchain'))
        
        return merged 