"""
Enhanced Onchain Market Making

This script demonstrates how to use the market_data.py utility functions with the 
onchain market making backtesting engine, particularly focusing on latency impact
and order execution differences between CEX and onchain venues.
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
    OnchainDataHandler,
    calculate_signals, 
    plot_market_data, 
    simulate_latency_impact,
    estimate_bid_ask_spread,
    calculate_order_book_imbalance,
    predict_short_term_move
)

def main():
    """Run the enhanced onchain market making example"""
    print("=== Enhanced Onchain Market Making ===")
    
    # 1. Initialize data handlers
    market_handler = MarketDataHandler(exchange='simulation', api_key=None, api_secret=None)
    onchain_handler = OnchainDataHandler(provider_url=None)
    
    # 2. Generate synthetic market data
    processor = DataProcessor()
    
    # Generate CEX market data
    cex_data = processor.simulate_market_data(
        n_periods=1000,
        initial_price=2000,
        volatility=0.01,
        mean_reversion=0.1,
        spread_mean=0.001,
        spread_std=0.0005
    )
    
    # Generate onchain data based on CEX data
    onchain_data = processor.simulate_onchain_data(
        cex_data=cex_data,
        latency_range=(300, 800),  # 300-800ms latency
        fee_range=(0.002, 0.008)    # 0.2-0.8% fees
    )
    
    print(f"Generated data: {len(cex_data)} CEX samples, {len(onchain_data)} onchain samples")
    
    # 3. Calculate market signals for both sources
    cex_signals = calculate_signals(cex_data.iloc[-100:])
    onchain_signals = calculate_signals(onchain_data.iloc[-100:])
    
    print("\nCEX Market Signals:")
    for key, value in cex_signals.items():
        print(f"  {key}: {value:.6f}")
        
    print("\nOnchain Market Signals:")
    for key, value in onchain_signals.items():
        print(f"  {key}: {value:.6f}")
    
    # 4. Analyze latency impact
    print("\nAnalyzing latency impact...")
    latency_comparison = simulate_latency_impact(
        cex_data, 
        cex_latency_ms=50,  # 50ms latency for centralized exchange
        onchain_latency_ms=5000  # 5 seconds latency for onchain
    )
    
    # Display latency impact results
    print("\nLatency Impact Analysis:")
    print(f"Average CEX price impact: {latency_comparison['cex_price_impact_pct'].mean():.4f}%")
    print(f"Average Onchain price impact: {latency_comparison['onchain_price_impact_pct'].mean():.4f}%")
    print(f"Price impact difference: {latency_comparison['onchain_price_impact_pct'].mean() - latency_comparison['cex_price_impact_pct'].mean():.4f}%")
    
    # 5. Plot latency impact
    plt.figure(figsize=(12, 6))
    plt.hist(latency_comparison['cex_price_impact_pct'], alpha=0.5, bins=50, label='CEX')
    plt.hist(latency_comparison['onchain_price_impact_pct'], alpha=0.5, bins=50, label='Onchain')
    plt.title('Price Impact Distribution: CEX vs Onchain')
    plt.xlabel('Price Impact (%)')
    plt.ylabel('Frequency')
    plt.legend()
    plt.grid(True)
    plt.savefig("onchain_latency_impact.png")
    
    # 6. Run comparative backtests: CEX vs onchain
    
    # Initialize models with adapted parameters for onchain
    cex_model = AvellanedaStoikovModel(risk_aversion=1.0)
    onchain_model = AvellanedaStoikovModel(risk_aversion=2.0)  # Higher risk aversion for onchain
    
    # Initialize backtest engines
    cex_engine = BacktestEngine(
        market_data=cex_data,
        initial_capital=10000.0,
        transaction_fee=0.001  # 0.1% fee for CEX
    )
    
    onchain_engine = BacktestEngine(
        market_data=onchain_data,
        initial_capital=10000.0,
        transaction_fee=0.005  # 0.5% fee for onchain (includes gas)
    )
    
    # Run backtests
    print("\nRunning CEX backtest...")
    cex_results = cex_engine.run_backtest(
        model=cex_model,
        max_inventory=20,
        volatility_window=20
    )
    
    print("\nRunning onchain backtest...")
    onchain_results = onchain_engine.run_backtest(
        model=onchain_model,
        max_inventory=10,  # Lower inventory for onchain due to higher risk
        volatility_window=20
    )
    
    # Compare results
    print("\nBacktest Results Comparison: CEX vs Onchain")
    print(f"{'Metric':<20} {'CEX':<15} {'Onchain':<15} {'Difference':<15}")
    print(f"{'-'*65}")
    
    for metric in cex_results['metrics']:
        cex_value = cex_results['metrics'][metric]
        onchain_value = onchain_results['metrics'][metric]
        diff = onchain_value - cex_value
        diff_pct = (diff / cex_value * 100) if cex_value != 0 else 0
        
        print(f"{metric:<20} {cex_value:<15.2f} {onchain_value:<15.2f} {diff:<15.2f} ({diff_pct:+.2f}%)")
    
    print("\nOnchain market making strategies generally need to account for:")
    print("  1. Higher latency (slower execution)")
    print("  2. Higher transaction costs (gas fees)")
    print("  3. Greater price impact")
    print("  4. Lower trading frequency")
    print("  5. Higher inventory risk")
    
    print("\nEnhanced onchain market making demonstration completed successfully.")

if __name__ == "__main__":
    main() 