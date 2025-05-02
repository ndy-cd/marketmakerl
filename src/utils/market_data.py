import numpy as np
import pandas as pd
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple
import time
import ccxt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarketDataHandler:
    """Handler for fetching and processing market data from exchanges"""
    
    def __init__(self, exchange='binance', api_key=None, api_secret=None):
        """
        Initialize the MarketDataHandler
        
        Parameters:
            exchange (str): Exchange ID (e.g., 'binance', 'ftx')
            api_key (str): API key for the exchange
            api_secret (str): API secret for the exchange
        """
        self.exchange_name = exchange
        self.api_key = api_key
        self.api_secret = api_secret
        self.exchange = self._initialize_exchange()
        
    def _initialize_exchange(self):
        """Initialize the exchange connection"""
        try:
            if self.exchange_name == 'simulation':
                logger.info("Using simulation mode for market data")
                return None  # No real exchange connection in simulation mode
                
            # For real exchanges, initialize ccxt
            if not ccxt_available:
                logger.error("CCXT library not available. Install with 'pip install ccxt'")
                return None
                
            if self.exchange_name not in ccxt.exchanges:
                raise ValueError(f"Exchange {self.exchange_name} not supported")
                
            exchange_class = getattr(ccxt, self.exchange_name)
            exchange = exchange_class({
                'apiKey': self.api_key,
                'secret': self.api_secret
            })
            
            logger.info(f"Successfully connected to {self.exchange_name}")
            return exchange
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            raise
            
    def fetch_ohlcv(self, symbol, timeframe='1m', limit=1000, since=None):
        """
        Fetch OHLCV data for a symbol
        
        Parameters:
            symbol (str): Trading pair symbol
            timeframe (str): Timeframe for the data
            limit (int): Number of candles to fetch
            since (int): Timestamp in milliseconds for start time
            
        Returns:
            pd.DataFrame: DataFrame with OHLCV data
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit, since=since)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            logger.error(f"Error fetching OHLCV data for {symbol}: {e}")
            return pd.DataFrame()
            
    def fetch_order_book(self, symbol, limit=100):
        """
        Fetch order book data for a symbol
        
        Parameters:
            symbol (str): Trading pair symbol
            limit (int): Depth of the order book
            
        Returns:
            dict: Order book with bids and asks
        """
        try:
            order_book = self.exchange.fetch_order_book(symbol, limit)
            return {
                'bids': pd.DataFrame(order_book['bids'], columns=['price', 'amount']),
                'asks': pd.DataFrame(order_book['asks'], columns=['price', 'amount']),
                'timestamp': datetime.fromtimestamp(order_book['timestamp']/1000) if 'timestamp' in order_book else datetime.now()
            }
        except Exception as e:
            logger.error(f"Error fetching order book for {symbol}: {e}")
            return {'bids': pd.DataFrame(), 'asks': pd.DataFrame(), 'timestamp': datetime.now()}
            
    def calculate_market_metrics(self, symbol, lookback_periods=20):
        """
        Calculate key market metrics for a symbol
        
        Parameters:
            symbol (str): Trading pair symbol
            lookback_periods (int): Number of periods to look back
            
        Returns:
            dict: Dictionary of market metrics
        """
        try:
            # Fetch recent data
            ohlcv = self.fetch_ohlcv(symbol, limit=lookback_periods)
            
            # Calculate volatility (standard deviation of returns)
            returns = ohlcv['close'].pct_change().dropna()
            volatility = returns.std()
            
            # Calculate average volume
            avg_volume = ohlcv['volume'].mean()
            
            # Get current order book
            order_book = self.fetch_order_book(symbol)
            
            # Calculate bid-ask spread
            if not order_book['bids'].empty and not order_book['asks'].empty:
                best_bid = order_book['bids']['price'].iloc[0]
                best_ask = order_book['asks']['price'].iloc[0]
                spread = (best_ask - best_bid) / best_bid
            else:
                best_bid = best_ask = spread = np.nan
                
            return {
                'volatility': volatility,
                'avg_volume': avg_volume,
                'best_bid': best_bid,
                'best_ask': best_ask,
                'spread': spread,
                'mid_price': (best_bid + best_ask) / 2 if not np.isnan(best_bid) and not np.isnan(best_ask) else np.nan
            }
        except Exception as e:
            logger.error(f"Error calculating market metrics for {symbol}: {e}")
            return {
                'volatility': np.nan,
                'avg_volume': np.nan,
                'best_bid': np.nan,
                'best_ask': np.nan,
                'spread': np.nan,
                'mid_price': np.nan
            }
            
    def simulate_latency(self, base_latency=100, jitter=50):
        """
        Simulate network latency for onchain trading
        
        Parameters:
            base_latency (int): Base latency in milliseconds
            jitter (int): Random jitter range in milliseconds
            
        Returns:
            None: Just sleeps for the simulated latency
        """
        latency = base_latency + np.random.randint(-jitter, jitter)
        time.sleep(max(0, latency/1000))  # Convert to seconds and sleep

class OnchainDataHandler:
    """Handler for fetching and processing data from onchain sources"""
    
    def __init__(self, provider_url=None):
        """
        Initialize the onchain data handler
        
        Parameters:
            provider_url (str): Ethereum provider URL
        """
        self.provider_url = provider_url
        # This would be expanded with real onchain data handling using web3.py
        
    def fetch_pool_data(self, pool_address):
        """
        Fetch data for a specific liquidity pool
        
        Parameters:
            pool_address (str): Contract address of the pool
            
        Returns:
            dict: Pool data including reserves, fees, etc.
        """
        # This is a placeholder. In a real implementation, this would use web3.py to query the pool
        return {
            'reserves': [0, 0],
            'fees': 0.003,
            'price': 0,
            'timestamp': datetime.now()
        }

def calculate_volatility(prices, window=20, annualize=True):
    """
    Calculate rolling volatility of price series
    
    Parameters:
        prices (pd.Series): Price series
        window (int): Window size for calculation
        annualize (bool): Whether to annualize the result
        
    Returns:
        pd.Series: Volatility series
    """
    # Calculate returns
    returns = prices.pct_change().dropna()
    
    # Calculate rolling standard deviation
    vol = returns.rolling(window=window).std()
    
    # Annualize if requested (assuming daily data)
    if annualize:
        # For minute data, annualization factor is sqrt(525600)
        # For hourly data, annualization factor is sqrt(8760)
        # For daily data, annualization factor is sqrt(252)
        # Try to infer the frequency
        if isinstance(prices.index, pd.DatetimeIndex) and len(prices) > 1:
            avg_timedelta = (prices.index[-1] - prices.index[0]) / (len(prices) - 1)
            if avg_timedelta < timedelta(minutes=10):
                # Minute data
                vol = vol * np.sqrt(525600)
            elif avg_timedelta < timedelta(hours=1):
                # Minute data but with gaps
                vol = vol * np.sqrt(525600)
            elif avg_timedelta < timedelta(days=1):
                # Hourly data
                vol = vol * np.sqrt(8760)
            else:
                # Daily data
                vol = vol * np.sqrt(252)
        else:
            # Default to daily data
            vol = vol * np.sqrt(252)
    
    return vol

def estimate_bid_ask_spread(volatility, lob_depth=None, impact_coef=1.0):
    """
    Estimate bid-ask spread from volatility
    
    Parameters:
        volatility (float): Price volatility
        lob_depth (float): Order book depth (optional)
        impact_coef (float): Market impact coefficient
        
    Returns:
        float: Estimated spread
    """
    # Base spread estimate from volatility
    base_spread = volatility / 10
    
    # Adjust for market depth if provided
    if lob_depth is not None and lob_depth > 0:
        depth_factor = np.exp(-impact_coef * lob_depth)
        return base_spread * (1 + depth_factor)
    
    return base_spread

def calculate_order_book_imbalance(bids, asks):
    """
    Calculate order book imbalance
    
    Parameters:
        bids (dict): Bid side of the order book (price -> size)
        asks (dict): Ask side of the order book (price -> size)
        
    Returns:
        float: Order book imbalance (-1 to 1)
    """
    # Calculate total sizes
    total_bid_size = sum(bids.values())
    total_ask_size = sum(asks.values())
    
    # Calculate imbalance
    if total_bid_size + total_ask_size == 0:
        return 0
        
    return (total_bid_size - total_ask_size) / (total_bid_size + total_ask_size)

def calculate_market_impact(order_size, market_liquidity):
    """
    Calculate market impact of an order
    
    Parameters:
        order_size (float): Size of the order
        market_liquidity (float): Market liquidity measure
        
    Returns:
        float: Estimated market impact as a fraction of price
    """
    # Simple square-root model for market impact
    return 0.1 * np.sqrt(order_size / market_liquidity)

def predict_short_term_move(prices, order_flow=None):
    """
    Simple predictor for short-term price moves
    
    Parameters:
        prices (pd.Series): Recent price series
        order_flow (pd.Series): Recent order flow (optional)
        
    Returns:
        float: Predicted price move direction (-1 to 1)
    """
    # Extract recent momentum
    if len(prices) < 5:
        return 0
        
    # Calculate momentum signal
    returns = prices.pct_change().dropna()
    momentum = returns.iloc[-3:].mean() / returns.std()
    
    # Combine with order flow if available
    if order_flow is not None and len(order_flow) > 0:
        flow_signal = order_flow.iloc[-1] * 0.5  # Scale to -0.5 to 0.5
        return np.clip(momentum + flow_signal, -1, 1)
        
    return np.clip(momentum, -1, 1)

def determine_optimal_position(mid_price, inventory, volatility, risk_aversion):
    """
    Determine optimal inventory position
    
    Parameters:
        mid_price (float): Current mid price
        inventory (float): Current inventory
        volatility (float): Market volatility
        risk_aversion (float): Risk aversion parameter
        
    Returns:
        float: Optimal inventory position
    """
    # Using Avellaneda-Stoikov framework for optimal inventory
    return -inventory * risk_aversion * volatility**2

def calculate_signals(market_data, lookback=100):
    """
    Calculate various market signals from data
    
    Parameters:
        market_data (pd.DataFrame): Market data
        lookback (int): Lookback period for calculations
        
    Returns:
        dict: Dictionary of calculated signals
    """
    # Ensure we have enough data
    if len(market_data) < lookback:
        logger.warning(f"Not enough data for signal calculation. Need {lookback} points, got {len(market_data)}.")
        return {}
        
    # Use the most recent data
    data = market_data.iloc[-lookback:].copy()
    
    # Extract price series
    if 'mid_price' in data.columns:
        prices = data['mid_price']
    elif 'close' in data.columns:
        prices = data['close']
    else:
        logger.warning("No suitable price column found for signal calculation")
        return {}
    
    # Calculate signals
    signals = {}
    
    # Volatility
    signals['volatility'] = calculate_volatility(prices, window=min(20, lookback//2)).iloc[-1]
    
    # Trend strength (absolute value of moving average slope)
    ma = prices.rolling(window=min(20, lookback//2)).mean()
    signals['trend_strength'] = abs((ma.iloc[-1] - ma.iloc[-min(5, lookback//10)]) / prices.iloc[-1])
    
    # Price momentum
    signals['momentum'] = (prices.iloc[-1] / prices.iloc[-min(10, lookback//5)] - 1)
    
    # Mean reversion signal
    ma20 = prices.rolling(window=min(20, lookback//2)).mean()
    signals['mean_reversion'] = (ma20.iloc[-1] - prices.iloc[-1]) / prices.iloc[-1]
    
    # Spread data if available
    if 'spread' in data.columns:
        spread = data['spread']
        signals['spread'] = spread.iloc[-1]
        signals['spread_percentile'] = (spread.rank().iloc[-1] / len(spread))
        signals['spread_z_score'] = (spread.iloc[-1] - spread.mean()) / spread.std() if spread.std() > 0 else 0
    
    # Volume data if available
    if 'volume' in data.columns:
        volume = data['volume']
        signals['volume_percentile'] = (volume.rank().iloc[-1] / len(volume))
    
    return signals

def plot_market_data(market_data, signals=None, title="Market Data Analysis"):
    """
    Plot market data with signals
    
    Parameters:
        market_data (pd.DataFrame): Market data
        signals (dict): Optional signals to plot
        title (str): Plot title
        
    Returns:
        plt.Figure: Matplotlib figure
    """
    # Create figure
    fig, axs = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    
    # Extract data
    if 'mid_price' in market_data.columns:
        price_col = 'mid_price'
    elif 'close' in market_data.columns:
        price_col = 'close'
    else:
        logger.warning("No suitable price column found for plotting")
        plt.close(fig)
        return None
    
    # Plot price
    axs[0].plot(market_data.index, market_data[price_col], label='Price')
    axs[0].set_title(title)
    axs[0].legend()
    axs[0].grid(True)
    
    # Plot volatility if available
    if 'volatility' in market_data.columns:
        axs[1].plot(market_data.index, market_data['volatility'], color='orange', label='Volatility')
        axs[1].legend()
        axs[1].grid(True)
    elif signals and 'volatility' in signals:
        # Plot horizontal line for signal volatility
        axs[1].axhline(y=signals['volatility'], color='orange', linestyle='--', label='Volatility')
        axs[1].legend()
        axs[1].grid(True)
    
    # Plot spread if available
    if 'spread' in market_data.columns:
        axs[2].plot(market_data.index, market_data['spread'], color='green', label='Spread')
        axs[2].legend()
        axs[2].grid(True)
    
    # Adjust layout
    plt.tight_layout()
    
    return fig

def simulate_latency_impact(data, cex_latency_ms=50, onchain_latency_ms=5000):
    """
    Simulate impact of latency on trading execution
    
    Parameters:
        data (pd.DataFrame): Market data with timestamps
        cex_latency_ms (int): CEX latency in milliseconds
        onchain_latency_ms (int): Onchain latency in milliseconds
        
    Returns:
        pd.DataFrame: DataFrame with latency impact metrics
    """
    # Ensure data has a datetime index
    if not isinstance(data.index, pd.DatetimeIndex):
        logger.error("Data must have a datetime index for latency simulation")
        return pd.DataFrame()
    
    # Calculate price movement over latency periods
    results = []
    
    # Calculate timedeltas
    cex_delta = timedelta(milliseconds=cex_latency_ms)
    onchain_delta = timedelta(milliseconds=onchain_latency_ms)
    
    for i in range(len(data) - 1):
        row = data.iloc[i]
        current_time = data.index[i]
        
        # Find future prices after latency periods
        cex_future_time = current_time + cex_delta
        onchain_future_time = current_time + onchain_delta
        
        # Find closest future data points
        cex_future_idx = data.index.searchsorted(cex_future_time)
        onchain_future_idx = data.index.searchsorted(onchain_future_time)
        
        # Ensure we don't go out of bounds
        if cex_future_idx >= len(data):
            cex_future_idx = len(data) - 1
        if onchain_future_idx >= len(data):
            onchain_future_idx = len(data) - 1
        
        # Get future prices
        if 'mid_price' in data.columns:
            price_col = 'mid_price'
        elif 'close' in data.columns:
            price_col = 'close'
        else:
            logger.warning("No suitable price column found for latency simulation")
            return pd.DataFrame()
        
        current_price = row[price_col]
        cex_future_price = data.iloc[cex_future_idx][price_col]
        onchain_future_price = data.iloc[onchain_future_idx][price_col]
        
        # Calculate price impacts
        cex_price_impact = (cex_future_price - current_price) / current_price
        onchain_price_impact = (onchain_future_price - current_price) / current_price
        
        results.append({
            'timestamp': current_time,
            'current_price': current_price,
            'cex_future_price': cex_future_price,
            'onchain_future_price': onchain_future_price, 
            'cex_price_impact_pct': cex_price_impact * 100,
            'onchain_price_impact_pct': onchain_price_impact * 100,
            'cex_latency_ms': cex_latency_ms,
            'onchain_latency_ms': onchain_latency_ms
        })
    
    return pd.DataFrame(results) 