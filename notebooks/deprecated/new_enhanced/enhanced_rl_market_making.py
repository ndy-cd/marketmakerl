"""
Enhanced RL Market Making

This script demonstrates how to use the market_data.py utility functions with the 
reinforcement learning enhanced market making model, focusing on how market signals
can be incorporated into the RL decision making process.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.append('../..')

# Import project modules
from src.models.avellaneda_stoikov import AvellanedaStoikovModel
from src.models.rl_enhanced_model import RLEnhancedModel
from src.backtesting.backtest_engine import BacktestEngine
from src.data.data_processor import DataProcessor
from src.utils.market_data import (
    MarketDataHandler,
    calculate_signals, 
    plot_market_data, 
    estimate_bid_ask_spread,
    calculate_order_book_imbalance,
    predict_short_term_move,
    determine_optimal_position
)

def main():
    """Run the enhanced RL market making example"""
    print("=== Enhanced RL Market Making ===")
    
    # 1. Initialize market data handler
    data_handler = MarketDataHandler(exchange='simulation', api_key=None, api_secret=None)
    
    # Generate market data
    processor = DataProcessor()
    market_data = processor.simulate_market_data(
        n_periods=1000,
        initial_price=2000,
        volatility=0.01,
        mean_reversion=0.1,
        spread_mean=0.001,
        spread_std=0.0005
    )
    
    print(f"Generated market data: {len(market_data)} samples")
    
    # 2. Calculate market signals and use them for optimal strategy
    signals = calculate_signals(market_data.iloc[-100:])
    print("\nMarket Signals:")
    for key, value in signals.items():
        print(f"  {key}: {value:.6f}")
    
    # 3. Use market_data utilities to analyze trading environment
    
    # Estimate optimal spread based on volatility
    volatility = market_data['volatility'].mean()
    optimal_spread = estimate_bid_ask_spread(volatility)
    print(f"\nEstimated optimal spread based on volatility: {optimal_spread:.6f} ({optimal_spread*100:.4f}%)")
    
    # Calculate order book imbalance (simulated for demonstration)
    bids = {1990: 10, 1995: 15, 1998: 5}  # price: size
    asks = {2002: 7, 2005: 12, 2010: 8}   # price: size
    imbalance = calculate_order_book_imbalance(bids, asks)
    print(f"Order book imbalance: {imbalance:.4f} ({'+' if imbalance > 0 else ''}{imbalance*100:.2f}% towards {'bids' if imbalance > 0 else 'asks'})")
    
    # Predict short-term price move
    move_signal = predict_short_term_move(market_data['mid_price'].iloc[-20:])
    print(f"Short-term price move prediction signal: {move_signal:.4f} ({'upward' if move_signal > 0 else 'downward'} momentum)")
    
    # 4. Setup RL-enhanced model with market signals
    
    # Create base model
    base_model = AvellanedaStoikovModel(risk_aversion=1.0)
    
    # Create RL-enhanced model
    rl_model = RLEnhancedModel(base_model=base_model)
    
    # Set parameters with market features
    market_features = {
        'volatility': signals['volatility'],
        'trend_strength': signals['trend_strength'],
        'momentum': signals['momentum'],
        'mean_reversion': signals['mean_reversion']
    }
    
    # Update the model with market features
    rl_model.set_parameters(
        risk_aversion=1.0,
        volatility=volatility,
        market_features=market_features
    )
    
    # Generate quotes with market features
    mid_price = market_data['mid_price'].iloc[-1]
    bid_price, ask_price = rl_model.calculate_optimal_quotes(
        mid_price, 
        market_features=market_features
    )
    
    print(f"\nOptimal quotes with market features:")
    print(f"  Mid price: {mid_price:.2f}")
    print(f"  Bid price: {bid_price:.2f} (spread: {(mid_price - bid_price) / mid_price * 100:.4f}%)")
    print(f"  Ask price: {ask_price:.2f} (spread: {(ask_price - mid_price) / mid_price * 100:.4f}%)")
    print(f"  Total spread: {(ask_price - bid_price) / mid_price * 100:.4f}%")
    
    # 5. Run comparative backtests
    
    # Initialize backtest engine
    backtest_engine = BacktestEngine(
        market_data=market_data,
        initial_capital=10000.0,
        transaction_fee=0.001
    )
    
    # Create standard model for comparison
    standard_model = AvellanedaStoikovModel(risk_aversion=1.0)
    
    # Run standard backtest
    print("\nRunning standard backtest...")
    standard_results = backtest_engine.run_backtest(
        model=standard_model,
        max_inventory=20,
        volatility_window=20
    )
    
    # Run RL-enhanced backtest with market signals
    print("\nRunning RL-enhanced backtest with market signals...")
    rl_results = backtest_engine.run_backtest_enhanced(
        model=rl_model,
        max_inventory=20,
        volatility_window=20,
        use_signals=True
    )
    
    # Compare results
    print("\nBacktest Results Comparison:")
    print(f"{'Metric':<20} {'Standard':<15} {'RL-Enhanced':<15} {'Difference':<15}")
    print(f"{'-'*65}")
    
    for metric in standard_results['metrics']:
        std_value = standard_results['metrics'][metric]
        rl_value = rl_results['metrics'][metric]
        diff = rl_value - std_value
        diff_pct = (diff / std_value * 100) if std_value != 0 else 0
        
        print(f"{metric:<20} {std_value:<15.2f} {rl_value:<15.2f} {diff:<15.2f} ({diff_pct:+.2f}%)")
    
    print("\nEnhanced RL market making demonstration completed successfully.")

if __name__ == "__main__":
    main() 