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
    
    def __init__(
        self,
        market_data,
        initial_capital=10000.0,
        transaction_fee=0.001,
        random_seed=42,
        min_edge_bps=0.0,
        cooldown_steps=1,
        execution_sensitivity=120.0,
    ):
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
        self.random_seed = int(random_seed)
        self.min_edge_bps = float(min_edge_bps)
        self.cooldown_steps = int(max(0, cooldown_steps))
        self.execution_sensitivity = float(max(1.0, execution_sensitivity))
        self.rng = np.random.default_rng(self.random_seed)
        self.reset()

    def _current_total_value(self, mid_price):
        return float(self.capital + self._calculate_unrealized_pnl(mid_price))

    def _normalize_return(self, row):
        if "returns" not in row:
            return 0.0
        value = row["returns"]
        if pd.isna(value):
            return 0.0
        return float(value)

    def _apply_risk_overlays(
        self,
        row,
        mid_price,
        volatility,
        peak_value,
        spread_constraint,
        spread_constraint_bps,
        min_edge_bps,
        soft_limit,
        params,
    ):
        current_value = self._current_total_value(mid_price)
        peak_value = max(float(peak_value), current_value)
        drawdown_pct = (peak_value - current_value) / max(1e-9, peak_value)

        hard_drawdown_stop_pct = float(params.get("hard_drawdown_stop_pct", 1.0)) if isinstance(params, dict) else 1.0
        soft_drawdown_risk_pct = float(params.get("soft_drawdown_risk_pct", 1.0)) if isinstance(params, dict) else 1.0
        target_volatility = float(params.get("target_volatility", 0.0)) if isinstance(params, dict) else 0.0
        vol_spread_scale = float(params.get("vol_spread_scale", 0.0)) if isinstance(params, dict) else 0.0
        risk_off_inventory_scale = float(params.get("risk_off_inventory_scale", 0.5)) if isinstance(params, dict) else 0.5

        hard_drawdown_stop_pct = min(max(hard_drawdown_stop_pct, 0.0), 1.0)
        soft_drawdown_risk_pct = min(max(soft_drawdown_risk_pct, 0.0), 1.0)
        risk_off_inventory_scale = min(max(risk_off_inventory_scale, 0.1), 1.0)

        hard_stop_triggered = bool(drawdown_pct >= hard_drawdown_stop_pct)
        risk_off = bool(drawdown_pct >= soft_drawdown_risk_pct)

        effective_spread_constraint = spread_constraint
        if spread_constraint_bps is not None:
            eff_bps = float(spread_constraint_bps)
            if target_volatility > 0 and volatility > 0:
                vol_ratio = min(5.0, max(0.5, float(volatility) / target_volatility))
                eff_bps *= (1.0 + (vol_spread_scale * max(0.0, vol_ratio - 1.0)))
            if risk_off:
                eff_bps *= 1.25
            effective_spread_constraint = mid_price * (eff_bps / 10_000.0)

        effective_min_edge_bps = float(min_edge_bps)
        if risk_off:
            effective_min_edge_bps += 0.5

        effective_soft_limit = float(soft_limit) * (risk_off_inventory_scale if risk_off else 1.0)
        effective_soft_limit = max(1e-9, effective_soft_limit)

        adverse_return_bps = float(params.get("adverse_return_bps", 0.0)) if isinstance(params, dict) else 0.0
        row_return = self._normalize_return(row)
        adverse_buy_block = bool(adverse_return_bps > 0 and row_return <= -(adverse_return_bps / 10_000.0))
        adverse_sell_block = bool(adverse_return_bps > 0 and row_return >= (adverse_return_bps / 10_000.0))

        return {
            "peak_value": peak_value,
            "current_value": current_value,
            "drawdown_pct": float(drawdown_pct),
            "hard_stop_triggered": hard_stop_triggered,
            "risk_off": risk_off,
            "effective_spread_constraint": effective_spread_constraint,
            "effective_min_edge_bps": effective_min_edge_bps,
            "effective_soft_limit": effective_soft_limit,
            "adverse_buy_block": adverse_buy_block,
            "adverse_sell_block": adverse_sell_block,
        }
        
    def reset(self):
        """Reset the backtest to initial state"""
        self.capital = self.initial_capital
        self.inventory = 0
        self.trades = []
        self.positions = []
        self._cooldown_remaining = 0
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
        
        spread_constraint = params.get("spread_constraint") if isinstance(params, dict) else None
        spread_constraint_bps = params.get("spread_constraint_bps") if isinstance(params, dict) else None
        min_edge_bps = float(params.get("min_edge_bps", self.min_edge_bps)) if isinstance(params, dict) else self.min_edge_bps
        inventory_soft_limit_ratio = float(params.get("inventory_soft_limit_ratio", 0.8)) if isinstance(params, dict) else 0.8
        cooldown_steps = int(params.get("cooldown_steps", self.cooldown_steps)) if isinstance(params, dict) else self.cooldown_steps
        order_notional_pct = float(params.get("order_notional_pct", 0.02)) if isinstance(params, dict) else 0.02
        min_order_qty = float(params.get("min_order_qty", 0.0001)) if isinstance(params, dict) else 0.0001
        max_order_qty = float(params.get("max_order_qty", 10.0)) if isinstance(params, dict) else 10.0
        order_notional_pct = min(max(order_notional_pct, 0.001), 0.5)
        min_order_qty = max(min_order_qty, 1e-8)
        max_order_qty = max(max_order_qty, min_order_qty)
        first_mid = float(self.market_data.iloc[0]['mid_price']) if len(self.market_data) > 0 else 1.0
        base_order_qty = (self.initial_capital * order_notional_pct) / max(1e-9, first_mid)
        base_order_qty = float(np.clip(base_order_qty, min_order_qty, max_order_qty))
        inventory_soft_limit_ratio = min(max(inventory_soft_limit_ratio, 0.1), 0.99)
        soft_limit = max(base_order_qty, (max_inventory * inventory_soft_limit_ratio * base_order_qty))
        max_inventory_units = max(base_order_qty, (max_inventory * base_order_qty))
        peak_value = float(self.initial_capital)

        for i, (timestamp, row) in enumerate(self.market_data.iterrows()):
            mid_price = row['mid_price']
            volatility = row['volatility']
            
            # Update model with current inventory and volatility
            model.update_inventory(self.inventory)
            if hasattr(model, 'set_parameters'):
                model.set_parameters(volatility=volatility)
                
            # Get model quotes
            overlays = self._apply_risk_overlays(
                row=row,
                mid_price=mid_price,
                volatility=volatility,
                peak_value=peak_value,
                spread_constraint=spread_constraint,
                spread_constraint_bps=spread_constraint_bps,
                min_edge_bps=min_edge_bps,
                soft_limit=soft_limit,
                params=params,
            )
            peak_value = overlays["peak_value"]

            if overlays["hard_stop_triggered"]:
                if self.inventory != 0:
                    liquidation_price = mid_price * (0.995 if self.inventory > 0 else 1.005)
                    self._process_trade(
                        timestamp,
                        "LIQUIDATION",
                        liquidation_price,
                        self.inventory,
                        mid_price,
                    )
                self.positions.append({
                    'timestamp': timestamp,
                    'mid_price': mid_price,
                    'inventory': self.inventory,
                    'capital': self.capital,
                    'unrealized_pnl': self._calculate_unrealized_pnl(mid_price),
                    'total_value': self.capital + self._calculate_unrealized_pnl(mid_price)
                })
                logger.warning(f"Hard drawdown stop triggered at step {i}; stopping backtest run")
                break

            spread_for_step = overlays["effective_spread_constraint"]
            bid_price, ask_price = model.calculate_optimal_quotes(mid_price, spread_constraint=spread_for_step)

            gross_spread_frac = max(0.0, (ask_price - bid_price) / max(1e-9, mid_price))
            net_edge_bps = (gross_spread_frac - (2 * self.transaction_fee)) * 10_000
            effective_min_edge_bps = overlays["effective_min_edge_bps"]
            if effective_min_edge_bps > 0 and net_edge_bps < effective_min_edge_bps:
                bid_executed, ask_executed = False, False
            elif self._cooldown_remaining > 0:
                self._cooldown_remaining -= 1
                bid_executed, ask_executed = False, False
            else:
                bid_executed, ask_executed = self._simulate_executions(bid_price, ask_price, row)

            effective_soft_limit = overlays["effective_soft_limit"]
            if self.inventory >= effective_soft_limit:
                bid_executed = False
            if self.inventory <= -effective_soft_limit:
                ask_executed = False
            if overlays["adverse_buy_block"]:
                bid_executed = False
            if overlays["adverse_sell_block"] and self.inventory <= 0:
                ask_executed = False
            
            # Process trades and update positions
            if bid_executed:
                affordable_qty = self.capital / max(1e-9, (bid_price * (1.0 + self.transaction_fee)))
                trade_qty = min(base_order_qty, max(0.0, float(affordable_qty)))
                if trade_qty >= min_order_qty:
                    self._process_trade(timestamp, 'BUY', bid_price, trade_qty, mid_price)
                    self._cooldown_remaining = cooldown_steps
                
            if ask_executed and self.inventory > 0:
                trade_qty = min(base_order_qty, max(0.0, float(self.inventory)))
                if trade_qty >= min_order_qty:
                    self._process_trade(timestamp, 'SELL', ask_price, trade_qty, mid_price)
                    self._cooldown_remaining = cooldown_steps
            
            # Check inventory limits
            if abs(self.inventory) >= max_inventory_units:
                # Force liquidation at market price with penalty
                inventory_before_liquidation = self.inventory
                liquidation_price = mid_price * (0.98 if inventory_before_liquidation > 0 else 1.02)
                self._process_trade(
                    timestamp,
                    'LIQUIDATION',
                    liquidation_price,
                    inventory_before_liquidation,
                    mid_price,
                )
                logger.warning(
                    f"Forced liquidation at step {i}, inventory_before: {inventory_before_liquidation}"
                )
                
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
        
        spread_constraint = params.get("spread_constraint") if isinstance(params, dict) else None
        spread_constraint_bps = params.get("spread_constraint_bps") if isinstance(params, dict) else None
        min_edge_bps = float(params.get("min_edge_bps", self.min_edge_bps)) if isinstance(params, dict) else self.min_edge_bps
        inventory_soft_limit_ratio = float(params.get("inventory_soft_limit_ratio", 0.8)) if isinstance(params, dict) else 0.8
        cooldown_steps = int(params.get("cooldown_steps", self.cooldown_steps)) if isinstance(params, dict) else self.cooldown_steps
        order_notional_pct = float(params.get("order_notional_pct", 0.02)) if isinstance(params, dict) else 0.02
        min_order_qty = float(params.get("min_order_qty", 0.0001)) if isinstance(params, dict) else 0.0001
        max_order_qty = float(params.get("max_order_qty", 10.0)) if isinstance(params, dict) else 10.0
        order_notional_pct = min(max(order_notional_pct, 0.001), 0.5)
        min_order_qty = max(min_order_qty, 1e-8)
        max_order_qty = max(max_order_qty, min_order_qty)
        first_mid = float(self.market_data.iloc[0]['mid_price']) if len(self.market_data) > 0 else 1.0
        base_order_qty = (self.initial_capital * order_notional_pct) / max(1e-9, first_mid)
        base_order_qty = float(np.clip(base_order_qty, min_order_qty, max_order_qty))
        inventory_soft_limit_ratio = min(max(inventory_soft_limit_ratio, 0.1), 0.99)
        soft_limit = max(base_order_qty, (max_inventory * inventory_soft_limit_ratio * base_order_qty))
        max_inventory_units = max(base_order_qty, (max_inventory * base_order_qty))
        peak_value = float(self.initial_capital)

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
            overlays = self._apply_risk_overlays(
                row=row,
                mid_price=mid_price,
                volatility=volatility,
                peak_value=peak_value,
                spread_constraint=spread_constraint,
                spread_constraint_bps=spread_constraint_bps,
                min_edge_bps=min_edge_bps,
                soft_limit=soft_limit,
                params=params,
            )
            peak_value = overlays["peak_value"]

            if overlays["hard_stop_triggered"]:
                if self.inventory != 0:
                    liquidation_price = mid_price * (0.995 if self.inventory > 0 else 1.005)
                    self._process_trade(
                        timestamp,
                        "LIQUIDATION",
                        liquidation_price,
                        self.inventory,
                        mid_price,
                    )
                self.positions.append({
                    'timestamp': timestamp,
                    'mid_price': mid_price,
                    'inventory': self.inventory,
                    'capital': self.capital,
                    'unrealized_pnl': self._calculate_unrealized_pnl(mid_price),
                    'total_value': self.capital + self._calculate_unrealized_pnl(mid_price)
                })
                logger.warning(f"Hard drawdown stop triggered at step {i}; stopping enhanced backtest run")
                break

            spread_for_step = overlays["effective_spread_constraint"]
            bid_price, ask_price = model.calculate_optimal_quotes(mid_price, spread_constraint=spread_for_step)
            
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
            
            gross_spread_frac = max(0.0, (ask_price - bid_price) / max(1e-9, mid_price))
            net_edge_bps = (gross_spread_frac - (2 * self.transaction_fee)) * 10_000
            effective_min_edge_bps = overlays["effective_min_edge_bps"]
            if effective_min_edge_bps > 0 and net_edge_bps < effective_min_edge_bps:
                bid_executed, ask_executed = False, False
            elif self._cooldown_remaining > 0:
                self._cooldown_remaining -= 1
                bid_executed, ask_executed = False, False
            else:
                bid_executed, ask_executed = self._simulate_executions(bid_price, ask_price, row)

            effective_soft_limit = overlays["effective_soft_limit"]
            if self.inventory >= effective_soft_limit:
                bid_executed = False
            if self.inventory <= -effective_soft_limit:
                ask_executed = False
            if overlays["adverse_buy_block"]:
                bid_executed = False
            if overlays["adverse_sell_block"] and self.inventory <= 0:
                ask_executed = False
            
            # Process trades and update positions
            if bid_executed:
                affordable_qty = self.capital / max(1e-9, (bid_price * (1.0 + self.transaction_fee)))
                trade_qty = min(base_order_qty, max(0.0, float(affordable_qty)))
                if trade_qty >= min_order_qty:
                    self._process_trade(timestamp, 'BUY', bid_price, trade_qty, mid_price)
                    self._cooldown_remaining = cooldown_steps
                
            if ask_executed and self.inventory > 0:
                trade_qty = min(base_order_qty, max(0.0, float(self.inventory)))
                if trade_qty >= min_order_qty:
                    self._process_trade(timestamp, 'SELL', ask_price, trade_qty, mid_price)
                    self._cooldown_remaining = cooldown_steps
            
            # Check inventory limits
            if abs(self.inventory) >= max_inventory_units:
                # Force liquidation at market price with penalty
                inventory_before_liquidation = self.inventory
                liquidation_price = mid_price * (0.98 if inventory_before_liquidation > 0 else 1.02)
                self._process_trade(
                    timestamp,
                    'LIQUIDATION',
                    liquidation_price,
                    inventory_before_liquidation,
                    mid_price,
                )
                logger.warning(
                    f"Forced liquidation at step {i}, inventory_before: {inventory_before_liquidation}"
                )
                
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
        
        bid_prob = self._execution_probability(
            quote_price=bid_price,
            mid_price=mid_price,
            side='BUY',
            low_price=low_price,
            high_price=high_price,
        )
        ask_prob = self._execution_probability(
            quote_price=ask_price,
            mid_price=mid_price,
            side='SELL',
            low_price=low_price,
            high_price=high_price,
        )

        bid_executed = bool(self.rng.random() < bid_prob)
        ask_executed = bool(self.rng.random() < ask_prob)

        if bid_executed and ask_executed:
            if self.inventory > 0:
                bid_executed = False
            elif self.inventory < 0:
                ask_executed = False
            elif self.rng.random() < 0.5:
                ask_executed = False
            else:
                bid_executed = False

        return bid_executed, ask_executed

    def _execution_probability(self, quote_price, mid_price, side, low_price, high_price):
        if mid_price <= 0:
            return 0.0

        if side == 'BUY':
            if quote_price >= mid_price:
                return 0.95
            distance_bps = max(0.0, (mid_price - quote_price) / mid_price * 10_000)
            touch_bonus = 0.25 if quote_price >= low_price else 0.0
        else:
            if quote_price <= mid_price:
                return 0.95
            distance_bps = max(0.0, (quote_price - mid_price) / mid_price * 10_000)
            touch_bonus = 0.25 if quote_price <= high_price else 0.0

        decay = np.exp(-distance_bps / self.execution_sensitivity)
        base_prob = 0.05 + (0.55 * decay) + touch_bonus
        return float(np.clip(base_prob, 0.01, 0.95))
        
    def _process_trade(self, timestamp, side, price, quantity, mid_price):
        """
        Process a trade and update inventory and capital
        
        Parameters:
            timestamp: Trade timestamp
            side (str): Trade side ('BUY' or 'SELL')
            price (float): Execution price
            quantity (float): Trade quantity
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
            # Quantity is signed inventory before liquidation. Positive means sell, negative means buy-to-cover.
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
            sell_value = (trades_df[trades_df['side'] == 'SELL']['price'] * trades_df[trades_df['side'] == 'SELL']['quantity']).sum()
            buy_value = (trades_df[trades_df['side'] == 'BUY']['price'] * trades_df[trades_df['side'] == 'BUY']['quantity']).sum()
            self.metrics['realized_pnl'] = sell_value - buy_value - trades_df['fee'].sum()
        
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
                profitable_trades['buy_price'] = 0.0
                for i, row in profitable_trades.iterrows():
                    # Find corresponding buy trade
                    buy_trades = trades_df[(trades_df['side'] == 'BUY') & (trades_df['timestamp'] < row['timestamp'])]
                    if not buy_trades.empty:
                        profitable_trades.at[i, 'buy_price'] = float(buy_trades.iloc[-1]['price'])
                
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
