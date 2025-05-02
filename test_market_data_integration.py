"""
Test Market Data Integration

This script tests the integration of market_data.py utility functions with the backtesting engine
and verifies that the enhanced backtesting capabilities work as expected.
"""

import unittest
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Configure logging to suppress output during tests
logging.basicConfig(level=logging.ERROR)

# Import project modules
from src.data.data_processor import DataProcessor
from src.models.avellaneda_stoikov import AvellanedaStoikovModel
from src.models.rl_enhanced_model import RLEnhancedModel
from src.backtesting.backtest_engine import BacktestEngine
from src.utils.market_data import (
    calculate_signals, 
    plot_market_data, 
    simulate_latency_impact,
    estimate_bid_ask_spread,
    calculate_order_book_imbalance,
    predict_short_term_move
)

class TestMarketDataIntegration(unittest.TestCase):
    """Test the integration of market_data.py utility functions"""
    
    def setUp(self):
        """Set up test environment"""
        # Generate test market data
        processor = DataProcessor()
        self.market_data = processor.simulate_market_data(
            n_periods=100,
            initial_price=2000,
            volatility=0.01,
            mean_reversion=0.1,
            spread_mean=0.001,
            spread_std=0.0005
        )
        
        # Create models
        self.standard_model = AvellanedaStoikovModel(risk_aversion=1.0)
        base_model = AvellanedaStoikovModel(risk_aversion=1.0)
        self.rl_model = RLEnhancedModel(base_model=base_model)
        
        # Create backtest engine
        self.backtest_engine = BacktestEngine(
            market_data=self.market_data,
            initial_capital=10000.0,
            transaction_fee=0.001
        )
    
    def test_market_signals_calculation(self):
        """Test that market signals can be calculated from market data"""
        # Ensure we have enough data with the right columns
        # The market data needs to have at least 100 points and contain either 'mid_price' or 'close' column
        if 'mid_price' not in self.market_data.columns and 'close' not in self.market_data.columns:
            # Add mid_price if it doesn't exist
            self.market_data['mid_price'] = (self.market_data['high'] + self.market_data['low']) / 2 if 'high' in self.market_data.columns and 'low' in self.market_data.columns else self.market_data['close']
            
        signals = calculate_signals(self.market_data, lookback=50)  # Using smaller lookback for test
        
        # Verify essential signals are present
        self.assertIn('volatility', signals)
        self.assertIn('trend_strength', signals)
        self.assertIn('momentum', signals)
        self.assertIn('mean_reversion', signals)
        
        # Verify signal values are reasonable
        self.assertGreaterEqual(signals['volatility'], 0)
        self.assertLessEqual(abs(signals['momentum']), 1.0)
    
    def test_bid_ask_spread_estimation(self):
        """Test that bid-ask spread can be estimated from volatility"""
        volatility = self.market_data['volatility'].mean()
        spread = estimate_bid_ask_spread(volatility)
        
        # Verify spread is positive and reasonable
        self.assertGreater(spread, 0)
        self.assertLess(spread, 0.05)  # Spread shouldn't be more than 5% for normal volatility
    
    def test_short_term_prediction(self):
        """Test short-term price movement prediction"""
        price_series = self.market_data['mid_price'].iloc[-20:]
        move_signal = predict_short_term_move(price_series)
        
        # Verify signal is in reasonable range
        self.assertGreaterEqual(move_signal, -1.0)
        self.assertLessEqual(move_signal, 1.0)
    
    def test_standard_backtest(self):
        """Test standard backtest functionality"""
        results = self.backtest_engine.run_backtest(
            model=self.standard_model,
            max_inventory=10,
            volatility_window=10
        )
        
        # Verify results contain expected components
        self.assertIn('metrics', results)
        self.assertIn('trades', results)
        self.assertIn('positions', results)
        
        # Verify metrics contain expected values
        self.assertIn('total_pnl', results['metrics'])
        self.assertIn('sharpe_ratio', results['metrics'])
        self.assertIn('max_drawdown', results['metrics'])
    
    def test_enhanced_backtest(self):
        """Test enhanced backtest functionality"""
        results = self.backtest_engine.run_backtest_enhanced(
            model=self.rl_model,
            max_inventory=10,
            volatility_window=10,
            use_signals=True
        )
        
        # Verify results contain expected components
        self.assertIn('metrics', results)
        self.assertIn('trades', results)
        self.assertIn('positions', results)
        
        # Verify metrics contain expected values
        self.assertIn('total_pnl', results['metrics'])
        self.assertIn('sharpe_ratio', results['metrics'])
        self.assertIn('max_drawdown', results['metrics'])
    
    def test_latency_impact(self):
        """Test latency impact simulation"""
        latency_results = simulate_latency_impact(
            self.market_data, 
            cex_latency_ms=50,
            onchain_latency_ms=5000
        )
        
        # Verify results contain expected columns
        self.assertIn('cex_price_impact_pct', latency_results.columns)
        self.assertIn('onchain_price_impact_pct', latency_results.columns)
        
        # Verify onchain impact is generally higher than CEX impact
        # This might not always be true for short sequences, so we check the mean
        self.assertGreaterEqual(
            abs(latency_results['onchain_price_impact_pct'].mean()), 
            abs(latency_results['cex_price_impact_pct'].mean())
        )
    
    def test_avellaneda_parameters(self):
        """Test that Avellaneda-Stoikov model can handle market_features"""
        # Create market features
        market_features = {
            'volatility': 0.01,
            'trend_strength': 0.05,
            'momentum': 0.02
        }
        
        # Set parameters with market features
        try:
            self.standard_model.set_parameters(
                risk_aversion=1.5,
                volatility=0.02,
                market_features=market_features
            )
            # If we reach here, the test passes
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"set_parameters raised exception {e}")
    
    def test_rl_model_market_features(self):
        """Test that RL model can handle market features"""
        # Create market features
        market_features = {
            'volatility': 0.01,
            'trend_strength': 0.05,
            'momentum': 0.02
        }
        
        # Set parameters with market features
        try:
            self.rl_model.set_parameters(
                volatility=0.02,
                market_features=market_features
            )
            # Use market features in quote calculation
            mid_price = 2000.0
            bid_price, ask_price = self.rl_model.calculate_optimal_quotes(
                mid_price, 
                market_features=market_features
            )
            
            # Verify bid is less than ask
            self.assertLess(bid_price, ask_price)
            # Verify prices are reasonable
            self.assertGreater(bid_price, mid_price * 0.97)
            self.assertLess(ask_price, mid_price * 1.03)
            
        except Exception as e:
            self.fail(f"RL model with market features raised exception {e}")

if __name__ == "__main__":
    # Run the tests
    unittest.main() 