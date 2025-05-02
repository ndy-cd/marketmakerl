"""
Enhanced Crypto Market Making

This script demonstrates how to use the market_data.py utility functions with the 
crypto market making backtesting engine. It will serve as a template for updating
the existing notebooks.
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
    simulate_latency_impact,
    estimate_bid_ask_spread,
    calculate_order_book_imbalance,
    predict_short_term_move
)

def main():
    """Run the enhanced crypto market making example"""
    print("=== Enhanced Crypto Market Making ===")
    
    # 1. Initialize market data handler
    data_handler = MarketDataHandler(exchange='simulation', api_key=None, api_secret=None)
    
    # 2. Generate market data
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
    
    # 3. Calculate market signals
    signals = calculate_signals(market_data.iloc[-100:])
    print("\nMarket Signals:")
    for key, value in signals.items():
        print(f"  {key}: {value:.6f}")
    
    # 4. Visualize market data with signals
    plt.figure(figsize=(12, 8))
    plot_market_data(market_data.iloc[-200:], signals, title="BTC/USDT Market Analysis")
    plt.savefig("enhanced_market_data_analysis.png")
    
    # 5. Estimate optimal spread based on volatility
    volatility = market_data['volatility'].mean()
    optimal_spread = estimate_bid_ask_spread(volatility)
    print(f"\nEstimated optimal spread: {optimal_spread:.6f} ({optimal_spread*100:.4f}%)")
    
    # 6. Run comparative backtests: standard vs. enhanced
    
    # Initialize models
    standard_model = AvellanedaStoikovModel(risk_aversion=1.0)
    
    # Create base model for RL enhanced version
    base_model = AvellanedaStoikovModel(risk_aversion=1.0)
    rl_model = RLEnhancedModel(base_model=base_model)
    
    # Initialize backtest engine
    backtest_engine = BacktestEngine(
        market_data=market_data,
        initial_capital=10000.0,
        transaction_fee=0.001
    )
    
    # Run standard backtest
    print("\nRunning standard backtest...")
    standard_results = backtest_engine.run_backtest(
        model=standard_model,
        max_inventory=20,
        volatility_window=20
    )
    
    # Run enhanced backtest with market signals
    print("\nRunning enhanced backtest with market signals...")
    enhanced_results = backtest_engine.run_backtest_enhanced(
        model=rl_model,
        max_inventory=20,
        volatility_window=20,
        use_signals=True
    )
    
    # Compare results
    print("\nBacktest Results Comparison:")
    print(f"{'Metric':<20} {'Standard':<15} {'Enhanced':<15} {'Difference':<15}")
    print(f"{'-'*65}")
    
    for metric in standard_results['metrics']:
        std_value = standard_results['metrics'][metric]
        enh_value = enhanced_results['metrics'][metric]
        diff = enh_value - std_value
        diff_pct = (diff / std_value * 100) if std_value != 0 else 0
        
        print(f"{metric:<20} {std_value:<15.2f} {enh_value:<15.2f} {diff:<15.2f} ({diff_pct:+.2f}%)")
    
    print("\nEnhanced crypto market making demonstration completed successfully.")

if __name__ == "__main__":
    main() 