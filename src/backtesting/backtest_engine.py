import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging
import os
from datetime import datetime, timedelta
from src.models.avellaneda_stoikov import AvellanedaStoikovModel
from src.models.rl_enhanced_model import RLEnhancedModel
from src.utils.market_data import calculate_signals, determine_optimal_position, predict_short_term_move

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BacktestEngine:
    """
    Backtesting engine for market making strategies
    
    This engine simulates trading with historical data to evaluate
    the performance of market making algorithms.
    """
    
    def __init__(self, market_data, initial_capital=10000.0, transaction_fee=0.001):
        """
        Initialize the backtest engine
        
        Parameters:
            market_data (pd.DataFrame): Historical market data with timestamps and prices
            initial_capital (float): Initial capital for trading
            transaction_fee (float): Fee per transaction as a fraction
        """
        self.market_data = market_data
        self.initial_capital = initial_capital
        self.transaction_fee = transaction_fee
        self.reset()
        
    def reset(self):
        """Reset the backtest to initial state"""
        self.capital = self.initial_capital
        self.inventory = 0
        self.trades = []
        self.positions = []
        self.metrics = {
            'total_pnl': 0,
            'realized_pnl': 0,
            'unrealized_pnl': 0,
            'max_drawdown': 0,
            'max_inventory': 0,
            'n_trades': 0,
            'sharpe_ratio': 0,
            'win_rate': 0
        }
        
    def run_backtest(self, model, params=None, max_inventory=100, volatility_window=20):
        """
        Run a backtest using the given model
        
        Parameters:
            model: Market making model object (AvellanedaStoikovModel or RLEnhancedModel)
            params (dict): Parameters for the model
            max_inventory (int): Maximum allowed inventory
            volatility_window (int): Window size for volatility calculation
            
        Returns:
            dict: Performance metrics and trading history
        """
        self.reset()
        
        # Set model parameters if provided
        if params and hasattr(model, 'set_parameters'):
            model.set_parameters(**params)
        
        # Calculate volatility if needed
        if 'volatility' not in self.market_data.columns:
            self.market_data['returns'] = self.market_data['mid_price'].pct_change()
            self.market_data['volatility'] = self.market_data['returns'].rolling(window=volatility_window).std()
            
        # Fill NaN values in volatility
        self.market_data['volatility'] = self.market_data['volatility'].fillna(0.01)
        
        logger.info(f"Starting backtest with {len(self.market_data)} data points")
        
        for i, (timestamp, row) in enumerate(self.market_data.iterrows()):
            mid_price = row['mid_price']
            volatility = row['volatility']
            
            # Update model with current inventory and volatility
            model.update_inventory(self.inventory)
            if hasattr(model, 'set_parameters'):
                model.set_parameters(volatility=volatility)
                
            # Get model quotes
            bid_price, ask_price = model.calculate_optimal_quotes(mid_price)
            
            # Simulate market interactions (simple model)
            bid_executed, ask_executed = self._simulate_executions(bid_price, ask_price, row)
            
            # Process trades and update positions
            if bid_executed:
                self._process_trade(timestamp, 'BUY', bid_price, 1, mid_price)
                
            if ask_executed and self.inventory > 0:
                self._process_trade(timestamp, 'SELL', ask_price, 1, mid_price)
            
            # Check inventory limits
            if abs(self.inventory) >= max_inventory:
                # Force liquidation at market price with penalty
                liquidation_size = self.inventory
                liquidation_price = mid_price * (0.98 if self.inventory > 0 else 1.02)
                self._process_trade(timestamp, 'LIQUIDATION', liquidation_price, -liquidation_size, mid_price)
                logger.warning(f"Forced liquidation at step {i}, inventory: {self.inventory}")
                
            # Record position at this step
            self.positions.append({
                'timestamp': timestamp,
                'mid_price': mid_price,
                'inventory': self.inventory,
                'capital': self.capital,
                'unrealized_pnl': self._calculate_unrealized_pnl(mid_price),
                'total_value': self.capital + self._calculate_unrealized_pnl(mid_price)
            })
            
        # Calculate final metrics
        self._calculate_performance_metrics()
        
        logger.info(f"Backtest completed. Final PnL: {self.metrics['total_pnl']:.2f}")
        
        return {
            'metrics': self.metrics,
            'trades': pd.DataFrame(self.trades) if self.trades else pd.DataFrame(),
            'positions': pd.DataFrame(self.positions) if self.positions else pd.DataFrame()
        }
        
    def run_backtest_enhanced(self, model, params=None, max_inventory=100, volatility_window=20, use_signals=True):
        """
        Run an enhanced backtest using the given model with additional market signals
        
        Parameters:
            model: Market making model object (AvellanedaStoikovModel or RLEnhancedModel)
            params (dict): Parameters for the model
            max_inventory (int): Maximum allowed inventory
            volatility_window (int): Window size for volatility calculation
            use_signals (bool): Whether to use additional market signals
            
        Returns:
            dict: Performance metrics and trading history
        """
        self.reset()
        
        # Set model parameters if provided
        if params and hasattr(model, 'set_parameters'):
            model.set_parameters(**params)
        
        # Calculate volatility if needed
        if 'volatility' not in self.market_data.columns:
            self.market_data['returns'] = self.market_data['mid_price'].pct_change()
            self.market_data['volatility'] = self.market_data['returns'].rolling(window=volatility_window).std()
            
        # Fill NaN values in volatility
        self.market_data['volatility'] = self.market_data['volatility'].fillna(0.01)
        
        logger.info(f"Starting enhanced backtest with {len(self.market_data)} data points")
        
        for i, (timestamp, row) in enumerate(self.market_data.iterrows()):
            mid_price = row['mid_price']
            volatility = row['volatility']
            
            # Calculate market signals for a more informed strategy
            market_features = {}
            if use_signals and i >= 100:  # Need enough data for signals
                market_window = self.market_data.iloc[max(0, i-100):i+1]
                try:
                    signals = calculate_signals(market_window, lookback=min(50, i))
                    market_features.update(signals)
                    
                    # Predict short-term price movement
                    price_series = market_window['mid_price'].iloc[-20:]
                    move_prediction = predict_short_term_move(price_series)
                    market_features['price_move_signal'] = move_prediction
                    
                    # Get optimal position based on market conditions
                    risk_aversion = 1.0
                    if hasattr(model, 'risk_aversion'):
                        risk_aversion = model.risk_aversion
                        
                    optimal_position = determine_optimal_position(
                        mid_price=mid_price,
                        inventory=self.inventory,
                        volatility=volatility,
                        risk_aversion=risk_aversion
                    )
                    market_features['optimal_position'] = optimal_position
                except Exception as e:
                    logger.warning(f"Error calculating market signals: {e}")
            
            # Update model with current inventory and volatility
            model.update_inventory(self.inventory)
            if hasattr(model, 'set_parameters'):
                params_update = {'volatility': volatility}
                if market_features:
                    params_update['market_features'] = market_features
                model.set_parameters(**params_update)
                
            # Get model quotes
            bid_price, ask_price = model.calculate_optimal_quotes(mid_price)
            
            # Adjust quotes based on short-term price prediction if available
            if 'price_move_signal' in market_features:
                move_signal = market_features['price_move_signal']
                # Adjust quotes based on predicted price movement (positive = up, negative = down)
                signal_adjustment = move_signal * mid_price * 0.0005  # 0.05% max adjustment
                if move_signal > 0:  # Expected upward move: raise bid more than ask
                    bid_price += signal_adjustment
                    ask_price += signal_adjustment * 0.5
                else:  # Expected downward move: lower ask more than bid
                    bid_price += signal_adjustment * 0.5
                    ask_price += signal_adjustment
            
            # Simulate market interactions (simple model)
            bid_executed, ask_executed = self._simulate_executions(bid_price, ask_price, row)
            
            # Process trades and update positions
            if bid_executed:
                self._process_trade(timestamp, 'BUY', bid_price, 1, mid_price)
                
            if ask_executed and self.inventory > 0:
                self._process_trade(timestamp, 'SELL', ask_price, 1, mid_price)
            
            # Check inventory limits
            if abs(self.inventory) >= max_inventory:
                # Force liquidation at market price with penalty
                liquidation_size = self.inventory
                liquidation_price = mid_price * (0.98 if self.inventory > 0 else 1.02)
                self._process_trade(timestamp, 'LIQUIDATION', liquidation_price, -liquidation_size, mid_price)
                logger.warning(f"Forced liquidation at step {i}, inventory: {self.inventory}")
                
            # Record position at this step
            self.positions.append({
                'timestamp': timestamp,
                'mid_price': mid_price,
                'inventory': self.inventory,
                'capital': self.capital,
                'unrealized_pnl': self._calculate_unrealized_pnl(mid_price),
                'total_value': self.capital + self._calculate_unrealized_pnl(mid_price)
            })
            
        # Calculate final metrics
        self._calculate_performance_metrics()
        
        logger.info(f"Enhanced backtest completed. Final PnL: {self.metrics['total_pnl']:.2f}")
        
        return {
            'metrics': self.metrics,
            'trades': pd.DataFrame(self.trades) if self.trades else pd.DataFrame(),
            'positions': pd.DataFrame(self.positions) if self.positions else pd.DataFrame()
        }
        
    def _simulate_executions(self, bid_price, ask_price, market_data):
        """
        Simulate whether orders are executed based on market data
        
        Parameters:
            bid_price (float): Bid price
            ask_price (float): Ask price
            market_data (pd.Series): Market data for the current step
            
        Returns:
            tuple: (bid_executed, ask_executed)
        """
        mid_price = market_data['mid_price']
        low_price = market_data.get('low', mid_price * 0.995)
        high_price = market_data.get('high', mid_price * 1.005)
        
        # Simple model: orders execute if they cross market prices
        bid_executed = bid_price >= low_price
        ask_executed = ask_price <= high_price
        
        # Add randomness to simulate partial executions
        if bid_price < mid_price and not bid_executed:
            bid_executed = np.random.random() < 0.2 * (bid_price / low_price)
            
        if ask_price > mid_price and not ask_executed:
            ask_executed = np.random.random() < 0.2 * (high_price / ask_price)
            
        return bid_executed, ask_executed
        
    def _process_trade(self, timestamp, side, price, quantity, mid_price):
        """
        Process a trade and update inventory and capital
        
        Parameters:
            timestamp: Trade timestamp
            side (str): Trade side ('BUY' or 'SELL')
            price (float): Execution price
            quantity (int): Trade quantity
            mid_price (float): Current mid price
        """
        fee = abs(price * quantity * self.transaction_fee)
        
        if side == 'BUY':
            self.inventory += quantity
            self.capital -= price * quantity + fee
        elif side == 'SELL':
            self.inventory -= quantity
            self.capital += price * quantity - fee
        elif side == 'LIQUIDATION':
            # For liquidation, quantity is the negative inventory to reset to zero
            self.capital += price * quantity - fee
            self.inventory = 0
            
        # Record the trade
        self.trades.append({
            'timestamp': timestamp,
            'side': side,
            'price': price,
            'quantity': quantity,
            'fee': fee,
            'mid_price': mid_price,
            'inventory': self.inventory,
            'capital': self.capital
        })
        
    def _calculate_unrealized_pnl(self, current_price):
        """
        Calculate unrealized PnL based on current inventory and price
        
        Parameters:
            current_price (float): Current market price
            
        Returns:
            float: Unrealized PnL
        """
        return self.inventory * current_price
        
    def _calculate_performance_metrics(self):
        """Calculate performance metrics for the backtest"""
        if not self.positions:
            return
            
        positions_df = pd.DataFrame(self.positions)
        trades_df = pd.DataFrame(self.trades) if self.trades else pd.DataFrame()
        
        # Calculate total PnL
        initial_value = self.initial_capital
        final_value = positions_df.iloc[-1]['total_value']
        self.metrics['total_pnl'] = final_value - initial_value
        
        # Calculate realized PnL from closed trades
        if not trades_df.empty:
            self.metrics['realized_pnl'] = trades_df[trades_df['side'] == 'SELL']['price'].sum() - \
                                         trades_df[trades_df['side'] == 'BUY']['price'].sum() - \
                                         trades_df['fee'].sum()
        
        # Unrealized PnL
        self.metrics['unrealized_pnl'] = positions_df.iloc[-1]['unrealized_pnl'] if not positions_df.empty else 0
        
        # Max drawdown
        positions_df['drawdown'] = positions_df['total_value'].cummax() - positions_df['total_value']
        self.metrics['max_drawdown'] = positions_df['drawdown'].max()
        
        # Max inventory
        self.metrics['max_inventory'] = max(abs(positions_df['inventory'].max()), abs(positions_df['inventory'].min()))
        
        # Number of trades
        self.metrics['n_trades'] = len(trades_df)
        
        # Sharpe ratio (if we have enough data)
        if len(positions_df) > 1:
            positions_df['returns'] = positions_df['total_value'].pct_change()
            self.metrics['sharpe_ratio'] = positions_df['returns'].mean() / positions_df['returns'].std() * np.sqrt(252) if positions_df['returns'].std() > 0 else 0
        
        # Win rate
        if not trades_df.empty:
            profitable_trades = trades_df[trades_df['side'] == 'SELL'].copy()
            if not profitable_trades.empty:
                profitable_trades['buy_price'] = 0
                for i, row in profitable_trades.iterrows():
                    # Find corresponding buy trade
                    buy_trades = trades_df[(trades_df['side'] == 'BUY') & (trades_df['timestamp'] < row['timestamp'])]
                    if not buy_trades.empty:
                        profitable_trades.at[i, 'buy_price'] = int(float(buy_trades.iloc[-1]['price']))
                
                profitable_trades['profit'] = profitable_trades['price'] - profitable_trades['buy_price']
                wins = len(profitable_trades[profitable_trades['profit'] > 0])
                self.metrics['win_rate'] = wins / len(profitable_trades) if len(profitable_trades) > 0 else 0
    
    def plot_results(self, save_path=None):
        """
        Plot the backtest results
        
        Parameters:
            save_path (str): Path to save the plot image
        """
        if not self.positions:
            logger.warning("No position data to plot")
            return
            
        positions_df = pd.DataFrame(self.positions)
        
        # Create figure with subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
        
        # Plot price and inventory
        ax1.plot(positions_df['timestamp'], positions_df['mid_price'], label='Mid Price')
        ax1.set_ylabel('Price')
        ax1.set_title('Backtest Results')
        ax1.legend(loc='upper left')
        
        # Plot inventory
        ax2.plot(positions_df['timestamp'], positions_df['inventory'], label='Inventory', color='orange')
        ax2.set_ylabel('Inventory')
        ax2.legend(loc='upper left')
        
        # Plot total value
        ax3.plot(positions_df['timestamp'], positions_df['total_value'], label='Portfolio Value', color='green')
        ax3.set_ylabel('Value')
        ax3.set_xlabel('Time')
        ax3.legend(loc='upper left')
        
        # Adjust layout
        plt.tight_layout()
        
        # Save if path provided
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Plot saved to {save_path}")
            
        return fig