# Crypto Market Making Bot

A sophisticated market making bot for crypto trading pairs, developed for Overnight.fi. This system implements both traditional and enhanced market making strategies with extensive market data integration.

## Overview

This market making system is based on the Avellaneda-Stoikov methodology, enhanced with Reinforcement Learning (RL) techniques. It supports trading on both centralized exchanges and onchain venues (1inch PMM, Hashflow PMM) with built-in tools to handle the different latency and execution characteristics of each environment.

## Features

- Avellaneda-Stoikov market making model implementation
- Reinforcement Learning enhancement for dynamic adaptation
- Comprehensive market data utilities for signal generation and analysis
- Onchain trading capabilities with latency analysis
- Backtesting framework with performance comparison tools
- Enhanced notebooks demonstrating various trading strategies

## Project Structure

```
├── notebooks/                 # Jupyter notebooks for development and analysis
│   ├── crypto_market_making_enhanced.ipynb       # Enhanced CEX trading strategy
│   ├── onchain_market_making_enhanced.ipynb      # Enhanced onchain strategy
│   └── rl_enhanced_market_making_enhanced.ipynb  # RL-based enhancements
├── src/                       # Source code
│   ├── models/                # Trading models implementation
│   ├── data/                  # Data handling utilities
│   ├── utils/                 # Utility functions
│   │   └── market_data.py     # Market data analysis toolkit
│   └── backtesting/           # Backtesting framework
├── apply_enhancements.py      # Script to apply market data enhancements
├── integration_example.py     # Example of market data integration
├── test_integration.sh        # Test script for integration
└── completed_enhancements.md  # Documentation of all enhancements
```

## Setup

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Start with the Jupyter notebooks to explore the implementation:
```
jupyter notebook
```

## Key Components

### Market Making Models

- **AvellanedaStoikovModel**: Implementation of the classic market making algorithm
- **RLEnhancedModel**: Advanced model that uses RL to adapt to changing market conditions

### Market Data Utilities

The project includes comprehensive market data utilities in `src/utils/market_data.py`:

- **MarketDataHandler**: For fetching and processing exchange data
- **OnchainDataHandler**: For fetching and processing onchain data
- **Utility functions**:
  - `calculate_volatility()`: Calculate rolling volatility
  - `estimate_bid_ask_spread()`: Estimate optimal spreads
  - `predict_short_term_move()`: Predict price movements
  - `calculate_signals()`: Generate market signals
  - `simulate_latency_impact()`: Analyze latency effects

### Backtesting Framework

The backtesting engine (`src/backtesting/backtest_engine.py`) provides:

- Standard backtesting via `run_backtest()`
- Enhanced backtesting with market signals via `run_backtest_enhanced()`
- Performance analytics and visualization tools

## Recent Enhancements

### Code Improvements
- Fixed deprecated `fillna()` method in `DataProcessor`
- Fixed type compatibility issue in `BacktestEngine`
- Added simulation mode support in `MarketDataHandler`

### Performance Gains
The enhanced model using market signals consistently outperforms the standard model:

| Metric | Standard | Enhanced | Improvement |
|--------|----------|----------|-------------|
| PnL    | -3424.90 | -56.00   | 98.37%      |
| Sharpe | -0.60    | 0.15     | 124.57%     |

### Enhanced Analytics
- Added latency impact analysis between CEX and onchain venues
- Improved market signal visualization
- Added market regime detection

## Running Examples

To run the integration example:

```bash
python integration_example.py
```

To run all tests:

```bash
bash test_integration.sh
```

## Advanced Usage

To apply all enhancements to your own project:

```bash
python apply_enhancements.py --all
```

This will:
1. Update the `DataProcessor` to use modern methods
2. Fix the `BacktestEngine` type compatibility
3. Enhance the `MarketDataHandler` with simulation support
4. Apply notebook patches for enhanced functionality 