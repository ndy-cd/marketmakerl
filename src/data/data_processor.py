import numpy as np
import pandas as pd
import logging
import os
import json
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Optional, Union, Tuple

try:
    import ccxt

    CCXT_AVAILABLE = True
except ImportError:
    ccxt = None
    CCXT_AVAILABLE = False

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
            if not CCXT_AVAILABLE:
                raise ImportError("ccxt is not installed; install dependencies or use simulation mode")
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
            logger.warning("No suitable price column found for calculating returns")
            
        # Add technical features
        return self.add_technical_features(data, volatility_window)
        
    def add_technical_features(self, data, window=20):
        """
        Add technical analysis features to market data
        
        Parameters:
            data (pd.DataFrame): Market data with OHLCV columns
            window (int): Window size for calculations
            
        Returns:
            pd.DataFrame: DataFrame with added technical features
        """
        # Make a copy to avoid modifying the original
        df = data.copy()
        
        # Ensure we have a price column for calculations
        if 'close' in df.columns:
            price_col = 'close'
        elif 'mid_price' in df.columns:
            price_col = 'mid_price'
        else:
            logger.warning("No suitable price column found for technical analysis")
            return df
            
        # Calculate basic returns if not already present
        if 'returns' not in df.columns:
            df['returns'] = df[price_col].pct_change()
            
        # Volatility (standard deviation of returns)
        df['volatility'] = df['returns'].rolling(window=window).std()
        
        # Add mid price if not present
        if 'mid_price' not in df.columns:
            if all(col in df.columns for col in ['high', 'low']):
                df['mid_price'] = (df['high'] + df['low']) / 2
            else:
                df['mid_price'] = df[price_col]
                
        # Moving averages
        df['ma_20'] = df[price_col].rolling(window=20).mean()
        df['ma_50'] = df[price_col].rolling(window=50).mean()
        
        # Relative Strength Index (RSI)
        delta = df[price_col].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df[price_col].rolling(window=20).mean()
        df['bb_std'] = df[price_col].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + 2 * df['bb_std']
        df['bb_lower'] = df['bb_middle'] - 2 * df['bb_std']
        
        # MACD
        df['ema_12'] = df[price_col].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df[price_col].ewm(span=26, adjust=False).mean()
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # Spread calculations if bid/ask available
        if all(col in df.columns for col in ['bid_price', 'ask_price']):
            df['spread'] = (df['ask_price'] - df['bid_price']) / df['mid_price']
            df['spread_ma'] = df['spread'].rolling(window=window).mean()
            df['spread_std'] = df['spread'].rolling(window=window).std()
            df['spread_z'] = (df['spread'] - df['spread_ma']) / df['spread_std']
        
        # Add custom features for market making
        # Market regime detection (simplified)
        df['regime'] = np.where(df['volatility'] > df['volatility'].rolling(window=50).mean(), 'high_vol', 'low_vol')
        
        # Trend detection
        df['trend'] = np.where(df['ma_20'] > df['ma_50'], 'uptrend', 'downtrend')
        
        # Fill NaN values that result from window calculations
        df = df.bfill().ffill().fillna(0)
        
        return df
        
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
        Synchronize CEX data with onchain data, accounting for latency
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
        
    def simulate_onchain_data(self, cex_data, latency_range=(300, 800), fee_range=(0.002, 0.008), gas_cost_factor=1.2):
        """
        Simulate onchain data based on CEX data with added latency and fees
        
        Parameters:
            cex_data (pd.DataFrame): CEX market data
            latency_range (tuple): Range of latency in milliseconds (min, max)
            fee_range (tuple): Range of fees as fraction (min, max)
            gas_cost_factor (float): Factor to account for gas costs
            
        Returns:
            pd.DataFrame: Simulated onchain data
        """
        # Make a copy to avoid modifying the original
        onchain_data = cex_data.copy()
        
        # Add random latency to timestamps (simulate that onchain data is delayed)
        # This is just for simulation purposes - in reality timestamps would reflect when data is received
        min_latency, max_latency = latency_range
        latency_ms = np.random.uniform(min_latency, max_latency, size=len(onchain_data))
        latency_offsets = pd.TimedeltaIndex(latency_ms, unit='ms')
        
        # Adjust prices to account for wider spreads and fees
        min_fee, max_fee = fee_range
        fees = np.random.uniform(min_fee, max_fee, size=len(onchain_data))
        
        # Add columns for onchain-specific data
        onchain_data['cex_price'] = onchain_data['close'].copy()
        onchain_data['latency_ms'] = latency_ms
        onchain_data['fee_pct'] = fees * 100  # Convert to percentage
        
        # Adjust bid/ask to account for wider spreads on-chain
        # In onchain markets, spreads are typically wider due to gas costs, MEV, etc.
        if 'spread' in onchain_data.columns:
            # If spread already exists, widen it
            onchain_data['spread'] = onchain_data['spread'] * gas_cost_factor
        else:
            # Create a synthetic spread
            base_spread = 0.001  # 0.1% base spread
            onchain_data['spread'] = base_spread * gas_cost_factor * (1 + fees)
        
        # Calculate bid and ask prices
        onchain_data['mid_price'] = onchain_data['close']
        onchain_data['bid_price'] = onchain_data['mid_price'] * (1 - onchain_data['spread']/2)
        onchain_data['ask_price'] = onchain_data['mid_price'] * (1 + onchain_data['spread']/2)
        
        # Add gas cost estimates (simplified version)
        avg_gas_price = 50  # Gwei
        avg_gas_used = 150000  # For a swap
        eth_price = onchain_data['close'].mean()  # Use as approximation
        gas_cost_usd = (avg_gas_price * 1e-9) * avg_gas_used * eth_price
        onchain_data['gas_cost_usd'] = gas_cost_usd
        
        # Add simulated slippage based on trade size
        # This is a placeholder for a more sophisticated slippage model
        onchain_data['slippage_1eth_pct'] = 0.05  # 0.05% slippage for 1 ETH trade
        onchain_data['slippage_10eth_pct'] = 0.2   # 0.2% slippage for 10 ETH trade
        
        # Calculate effective price after all costs for different trade sizes
        onchain_data['effective_buy_price_1eth'] = onchain_data['ask_price'] * (1 + onchain_data['slippage_1eth_pct']/100) + (gas_cost_usd / 1)
        onchain_data['effective_buy_price_10eth'] = onchain_data['ask_price'] * (1 + onchain_data['slippage_10eth_pct']/100) + (gas_cost_usd / 10)
        
        logger.info(f"Generated onchain data with latency range {latency_range}ms and fee range {fee_range}")
        
        return onchain_data 
