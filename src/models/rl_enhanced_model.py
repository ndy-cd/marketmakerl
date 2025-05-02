import numpy as np
import pandas as pd
import gym
from gym import spaces
import logging
import time
from datetime import datetime
from src.models.avellaneda_stoikov import AvellanedaStoikovModel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarketMakingEnv(gym.Env):
    """
    Market Making Environment for Reinforcement Learning
    
    This environment simulates a market making scenario based on historical
    or simulated market data where an agent can place bid and ask orders.
    """
    
    def __init__(self, market_data, initial_capital=10000.0, max_inventory=100, 
                 transaction_fee=0.001, reward_scaling=1.0, trading_horizon=100):
        """
        Initialize the market making environment
        
        Parameters:
            market_data (pd.DataFrame): Historical market data with columns for timestamp, mid_price, etc.
            initial_capital (float): Initial capital for the agent
            max_inventory (int): Maximum allowed inventory (positive or negative)
            transaction_fee (float): Fee per transaction as a fraction of order value
            reward_scaling (float): Scaling factor for rewards
            trading_horizon (int): Number of steps in one episode
        """
        super(MarketMakingEnv, self).__init__()
        
        self.market_data = market_data
        self.initial_capital = initial_capital
        self.max_inventory = max_inventory
        self.transaction_fee = transaction_fee
        self.reward_scaling = reward_scaling
        self.trading_horizon = trading_horizon
        
        # Environment state
        self.capital = initial_capital
        self.inventory = 0
        self.current_step = 0
        self.current_price = None
        self.current_timestamp = None
        self.done = False
        self.history = []
        
        # Base model for guidance
        self.base_model = AvellanedaStoikovModel()
        
        # Define action and observation spaces
        # Actions: [bid_price_offset, ask_price_offset, bid_size, ask_size]
        self.action_space = spaces.Box(
            low=np.array([-0.05, -0.05, 0.0, 0.0]),  # 5% max offset, min size 0
            high=np.array([0.05, 0.05, 1.0, 1.0]),   # 5% max offset, max size as fraction of max inventory
            dtype=np.float32
        )
        
        # Observations: [normalized_mid_price, normalized_inventory, volatility, spread, time_remaining]
        self.observation_space = spaces.Box(
            low=np.array([0, -1, 0, 0, 0]),
            high=np.array([np.inf, 1, np.inf, np.inf, 1]),
            dtype=np.float32
        )
        
    def reset(self):
        """
        Reset the environment to initial state
        
        Returns:
            np.array: Initial observation
        """
        self.capital = self.initial_capital
        self.inventory = 0
        self.current_step = 0
        self.done = False
        self.history = []
        
        # Get first market state
        self._update_market_state()
        
        return self._get_observation()
        
    def _update_market_state(self):
        """Update the current market state from market data"""
        if self.current_step < len(self.market_data):
            data = self.market_data.iloc[self.current_step]
            self.current_price = data.get('mid_price', data.get('close', 0))
            self.current_timestamp = data.name if isinstance(data.name, datetime) else datetime.now()
            self.current_volatility = data.get('volatility', 0.01)
            self.current_spread = data.get('spread', 0.002)
        else:
            self.done = True
            
    def _get_observation(self):
        """
        Get the current observation state
        
        Returns:
            np.array: Current observation
        """
        # Normalize the mid price (relative to initial price)
        norm_price = self.current_price / self.market_data.iloc[0].get('mid_price', self.market_data.iloc[0].get('close', 1))
        
        # Normalize inventory to -1 to 1 based on max inventory
        norm_inventory = self.inventory / self.max_inventory if self.max_inventory > 0 else 0
        
        # Time remaining in the episode
        time_remaining = 1 - (self.current_step / self.trading_horizon)
        
        return np.array([
            norm_price,
            norm_inventory,
            self.current_volatility,
            self.current_spread,
            time_remaining
        ], dtype=np.float32)
        
    def step(self, action):
        """
        Execute one step in the environment
        
        Parameters:
            action (np.array): Agent's action [bid_price_offset, ask_price_offset, bid_size, ask_size]
            
        Returns:
            tuple: (observation, reward, done, info)
        """
        if self.done:
            return self._get_observation(), 0, True, {}
            
        # Parse action
        bid_offset, ask_offset, bid_size_norm, ask_size_norm = action
        
        # Calculate actual bid and ask prices
        base_bid, base_ask = self.base_model.calculate_optimal_quotes(self.current_price)
        
        # Apply RL adjustments to the base model prices
        bid_price = base_bid * (1 + bid_offset)
        ask_price = base_ask * (1 + ask_offset)
        
        # Ensure bid < ask
        if bid_price >= ask_price:
            mid = (base_bid + base_ask) / 2
            bid_price = mid * 0.999
            ask_price = mid * 1.001
        
        # Calculate order sizes
        bid_size = int(bid_size_norm * self.max_inventory)
        ask_size = int(ask_size_norm * self.max_inventory)
        
        # Limit ask size to current inventory (can't sell what you don't have)
        ask_size = min(ask_size, self.inventory + self.max_inventory)
        
        # Limit bid size to max inventory constraint
        bid_size = min(bid_size, self.max_inventory - self.inventory)
        
        # Simulate market response (whether orders are filled)
        bid_fill, ask_fill = self._simulate_order_fills(bid_price, ask_price, bid_size, ask_size)
        
        # Calculate reward based on P&L
        reward, pnl = self._calculate_reward(bid_price, ask_price, bid_fill, ask_fill)
        
        # Update inventory and capital
        self.inventory += bid_fill - ask_fill
        
        # Store step history
        self.history.append({
            'step': self.current_step,
            'timestamp': self.current_timestamp,
            'mid_price': self.current_price,
            'bid_price': bid_price,
            'ask_price': ask_price,
            'bid_fill': bid_fill,
            'ask_fill': ask_fill,
            'inventory': self.inventory,
            'capital': self.capital,
            'pnl': pnl
        })
        
        # Move to next step
        self.current_step += 1
        self._update_market_state()
        
        # Check if episode is done
        if self.current_step >= min(len(self.market_data), self.trading_horizon):
            self.done = True
            
            # Liquidate remaining inventory at mid price with a penalty
            if self.inventory != 0:
                liquidation_price = self.current_price * (0.98 if self.inventory > 0 else 1.02)
                liquidation_pnl = self.inventory * (liquidation_price - self.current_price)
                self.capital += liquidation_pnl
        
        return self._get_observation(), reward, self.done, {'pnl': pnl, 'inventory': self.inventory}
        
    def _simulate_order_fills(self, bid_price, ask_price, bid_size, ask_size):
        """
        Simulate whether orders get filled based on market data
        
        Parameters:
            bid_price (float): Bid price
            ask_price (float): Ask price
            bid_size (int): Bid size
            ask_size (int): Ask size
            
        Returns:
            tuple: (bid_fill, ask_fill) number of units filled
        """
        # Simple model: orders are filled if price is favorable enough
        # This should be enhanced with more realistic market simulation
        
        # If our bid is above market bid, it may get filled
        bid_threshold = self.current_price * 0.997  # Just below mid price
        bid_fill_prob = max(0, min(1, (bid_price - bid_threshold) / (self.current_price * 0.01)))
        bid_fill = int(bid_size * bid_fill_prob) if np.random.random() < bid_fill_prob else 0
        
        # If our ask is below market ask, it may get filled
        ask_threshold = self.current_price * 1.003  # Just above mid price
        ask_fill_prob = max(0, min(1, (ask_threshold - ask_price) / (self.current_price * 0.01)))
        ask_fill = int(ask_size * ask_fill_prob) if np.random.random() < ask_fill_prob else 0
        
        return bid_fill, ask_fill
        
    def _calculate_reward(self, bid_price, ask_price, bid_fill, ask_fill):
        """
        Calculate reward for the current step
        
        Parameters:
            bid_price (float): Bid price
            ask_price (float): Ask price
            bid_fill (int): Number of bid units filled
            ask_fill (int): Number of ask units filled
            
        Returns:
            tuple: (reward, pnl)
        """
        # Calculate P&L from filled orders
        bid_cost = bid_fill * bid_price * (1 + self.transaction_fee)
        ask_revenue = ask_fill * ask_price * (1 - self.transaction_fee)
        
        # Update capital
        self.capital -= bid_cost
        self.capital += ask_revenue
        
        # Calculate P&L (excluding inventory value changes)
        pnl = ask_revenue - bid_cost
        
        # Inventory risk penalty
        inventory_risk = 0.1 * self.current_volatility * abs(self.inventory) / self.max_inventory
        
        # Reward is P&L minus inventory risk
        reward = (pnl / self.current_price - inventory_risk) * self.reward_scaling
        
        return reward, pnl
        
    def render(self, mode='human'):
        """Render the environment state"""
        if mode == 'human':
            if len(self.history) > 0:
                last_step = self.history[-1]
                print(f"Step: {last_step['step']}, "
                      f"Price: {last_step['mid_price']:.2f}, "
                      f"Inventory: {last_step['inventory']}, "
                      f"PnL: {last_step['pnl']:.2f}, "
                      f"Capital: {last_step['capital']:.2f}")
        return None
        
    def get_performance_metrics(self):
        """
        Calculate performance metrics for the episode
        
        Returns:
            dict: Performance metrics
        """
        if not self.history:
            return {}
            
        df = pd.DataFrame(self.history)
        
        total_pnl = df['pnl'].sum()
        sharpe_ratio = df['pnl'].mean() / (df['pnl'].std() + 1e-10) * np.sqrt(252)  # Annualized
        max_drawdown = (df['capital'].cummax() - df['capital']).max()
        max_inventory = df['inventory'].abs().max()
        
        return {
            'total_pnl': total_pnl,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'max_inventory': max_inventory,
            'final_capital': self.capital,
            'final_inventory': self.inventory
        }

class RLEnhancedModel:
    """
    Reinforcement Learning enhanced market making model
    
    This model combines traditional Avellaneda-Stoikov approach with
    RL-based adjustments to optimize market making performance.
    """
    
    def __init__(self, base_model=None, model_path=None):
        """
        Initialize the RL-enhanced market making model
        
        Parameters:
            base_model (AvellanedaStoikovModel): Base market making model
            model_path (str): Path to saved RL model weights
        """
        self.base_model = base_model or AvellanedaStoikovModel()
        self.rl_model = None  # This would be loaded from a trained model
        self.current_inventory = 0
        self.current_state = None
        
        # In a real implementation, we would load the RL model here
        # For example, using stable-baselines3:
        # from stable_baselines3 import PPO
        # if model_path:
        #     self.rl_model = PPO.load(model_path)
        
    def update_inventory(self, inventory):
        """
        Update the current inventory
        
        Parameters:
            inventory (float): Current inventory level
        """
        self.current_inventory = inventory
        self.base_model.update_inventory(inventory)
        
    def set_parameters(self, **kwargs):
        """
        Update model parameters
        
        Parameters:
            **kwargs: Parameters to update
        """
        self.base_model.set_parameters(**kwargs)
        
        # Store market features if provided
        if 'market_features' in kwargs:
            self.market_features = kwargs['market_features']
        
    def calculate_optimal_quotes(self, mid_price, market_features=None):
        """
        Calculate optimal bid and ask prices using RL enhancement
        
        Parameters:
            mid_price (float): Current mid price
            market_features (dict): Additional market features for RL input
            
        Returns:
            tuple: (bid_price, ask_price)
        """
        # Use market_features from parameters if not provided directly
        if market_features is None and hasattr(self, 'market_features'):
            market_features = self.market_features
            
        # Get base model quotes
        base_bid, base_ask = self.base_model.calculate_optimal_quotes(mid_price)
        
        # If we have a trained RL model, use it to adjust the quotes
        if self.rl_model is not None and market_features is not None:
            # Prepare state for RL model
            state = self._prepare_state(mid_price, market_features)
            self.current_state = state
            
            # Get action from RL model
            action = self.rl_model.predict(state)[0]
            
            # Parse action (bid offset, ask offset, bid size, ask size)
            bid_offset, ask_offset, bid_size_norm, ask_size_norm = action
            
            # Apply adjustments
            bid_price = base_bid * (1 + bid_offset)
            ask_price = base_ask * (1 + ask_offset)
            
            # Consider market signals for further adjustments
            if 'trend_strength' in market_features and 'momentum' in market_features:
                trend = market_features['trend_strength']
                momentum = market_features['momentum']
                
                # If strong trend with momentum, adjust quotes to capture movement
                if abs(momentum) > 0.002 and trend > 0.001:
                    adjustment = min(0.001, abs(momentum)) * (1 if momentum > 0 else -1)
                    bid_price += mid_price * adjustment
                    ask_price += mid_price * adjustment
            
            # Handle volatility-based spread adjustments
            if 'volatility' in market_features:
                volatility = market_features['volatility']
                # During high volatility, widen spread to reduce risk
                if volatility > 0.02:  # Higher than normal volatility
                    volatility_factor = min(1.5, 1 + (volatility - 0.02) * 10)  # Cap at 50% increase
                    mid = (bid_price + ask_price) / 2
                    half_spread = (ask_price - bid_price) / 2
                    new_half_spread = half_spread * volatility_factor
                    bid_price = mid - new_half_spread
                    ask_price = mid + new_half_spread
            
            # Handle mean reversion signals
            if 'mean_reversion' in market_features:
                mean_rev = market_features['mean_reversion']
                if abs(mean_rev) > 0.005:  # Strong mean reversion signal
                    # Adjust both bid and ask in direction of expected reversion
                    # but maintain spread
                    adjustment = mid_price * min(0.001, abs(mean_rev) / 10) * np.sign(mean_rev)
                    bid_price += adjustment
                    ask_price += adjustment
            
            # If price_move_signal is available, use it for short-term prediction
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
            
            return bid_price, ask_price
        
        # If no RL model, return base model prices
        return base_bid, base_ask
        
    def _prepare_state(self, mid_price, market_features):
        """
        Prepare state input for RL model
        
        Parameters:
            mid_price (float): Current mid price
            market_features (dict): Additional market features
            
        Returns:
            np.array: State representation for RL model
        """
        # Normalize inventory
        norm_inventory = self.current_inventory / 100  # Assuming max inventory is 100
        
        # Get volatility and spread from market features
        volatility = market_features.get('volatility', 0.01)
        spread = market_features.get('spread', 0.002)
        time_remaining = market_features.get('time_remaining', 0.5)
        
        # Combined state
        state = np.array([
            1.0,  # Normalized price (assuming this is already handled elsewhere)
            norm_inventory,
            volatility,
            spread,
            time_remaining
        ], dtype=np.float32)
        
        return state 