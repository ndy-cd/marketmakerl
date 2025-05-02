"""
Market Data Integration Example

This script demonstrates how to properly use the market_data.py utility functions
with the crypto market making backtesting engine.

Usage:
    python integration_example.py
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import logging

# Add project root to path
sys.path.append('.')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import project modules
from src.data.data_processor import DataProcessor
from src.models.avellaneda_stoikov import AvellanedaStoikovModel
from src.models.rl_enhanced_model import RLEnhancedModel
from src.backtesting.backtest_engine import BacktestEngine
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
    """Run the market data integration example"""
    print("=== Market Data Integration Example ===")
    
    # 1. Generate market data
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
    
    # 2. Calculate market signals
    signals = calculate_signals(market_data.iloc[-100:])
    print("\nMarket Signals:")
    for key, value in signals.items():
        print(f"  {key}: {value:.6f}")
    
    # 3. Visualize market data with signals
    plt.figure(figsize=(12, 8))
    fig = plot_market_data(market_data.iloc[-200:], signals, title="BTC/USDT Market Analysis")
    plt.savefig("market_data_analysis.png")
    print("Market data visualization saved to market_data_analysis.png")
    
    # 4. Estimate optimal spread based on volatility
    volatility = market_data['volatility'].mean()
    optimal_spread = estimate_bid_ask_spread(volatility)
    print(f"\nEstimated optimal spread: {optimal_spread:.6f} ({optimal_spread*100:.4f}%)")
    
    # 5. Run comparative backtests: standard vs. enhanced
    
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
    
    # Run enhanced backtest
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
    print(f"{'-'*60}")
    
    for metric in standard_results['metrics']:
        std_value = standard_results['metrics'][metric]
        enh_value = enhanced_results['metrics'][metric]
        diff = enh_value - std_value
        diff_pct = (diff / std_value * 100) if std_value != 0 else 0
        
        print(f"{metric:<20} {std_value:<15.2f} {enh_value:<15.2f} {diff:<15.2f} ({diff_pct:+.2f}%)")
    
    # Plot comparison
    positions_std = standard_results['positions']
    positions_enh = enhanced_results['positions']
    
    plt.figure(figsize=(12, 10))
    
    # Plot price
    plt.subplot(3, 1, 1)
    plt.plot(positions_std['timestamp'], positions_std['mid_price'], label='Price')
    plt.title('Market Price')
    plt.grid(True)
    
    # Plot portfolio values
    plt.subplot(3, 1, 2)
    plt.plot(positions_std['timestamp'], positions_std['total_value'], label='Standard')
    plt.plot(positions_enh['timestamp'], positions_enh['total_value'], label='Enhanced')
    plt.title('Portfolio Value Comparison')
    plt.grid(True)
    plt.legend()
    
    # Plot inventory
    plt.subplot(3, 1, 3)
    plt.plot(positions_std['timestamp'], positions_std['inventory'], label='Standard')
    plt.plot(positions_enh['timestamp'], positions_enh['inventory'], label='Enhanced')
    plt.title('Inventory Comparison')
    plt.grid(True)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig("backtest_comparison.png")
    print("Backtest comparison visualization saved to backtest_comparison.png")
    
    # 6. Analyze latency impact
    print("\nAnalyzing latency impact...")
    latency_results = simulate_latency_impact(
        market_data, 
        cex_latency_ms=50,
        onchain_latency_ms=5000
    )
    
    print(f"Average CEX price impact: {latency_results['cex_price_impact_pct'].mean():.6f}%")
    print(f"Average Onchain price impact: {latency_results['onchain_price_impact_pct'].mean():.6f}%")
    
    plt.figure(figsize=(12, 6))
    plt.hist(latency_results['cex_price_impact_pct'], alpha=0.5, bins=50, label='CEX')
    plt.hist(latency_results['onchain_price_impact_pct'], alpha=0.5, bins=50, label='Onchain')
    plt.title('Price Impact Distribution: CEX vs Onchain')
    plt.xlabel('Price Impact (%)')
    plt.ylabel('Frequency')
    plt.legend()
    plt.grid(True)
    plt.savefig("latency_impact.png")
    print("Latency impact visualization saved to latency_impact.png")
    
    print("\nIntegration example completed.")

if __name__ == "__main__":
    main() 