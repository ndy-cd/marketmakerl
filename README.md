# Crypto Market Making Bot

This repository contains a market making bot for USD+/wETH and USD+/cbBTC pairs, developed for Overnight.fi.

## Overview

The market making algorithm is based on the Avellaneda-Stoikov methodology, enhanced with Reinforcement Learning (RL) techniques to optimize market-making strategies both onchain (1inch PMM, Hashflow PMM) and based on centralized exchange data.

## Features

- Implementation of Avellaneda-Stoikov market making model
- Reinforcement Learning enhancement for dynamic adaptation
- Onchain trading capabilities (1inch PMM, Hashflow PMM)
- Integration with CEX data (Binance) with adjustments for onchain latency

## Project Structure

- `notebooks/`: Jupyter notebooks for development and analysis
- `src/`: Source code for the market making bot
  - `models/`: Implementation of trading models
  - `data/`: Data handling utilities
  - `utils/`: Utility functions
  - `backtesting/`: Backtesting framework

## Setup

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Start with the Jupyter notebooks to explore the implementation:
```
jupyter notebook
```

## Main Components

1. Data Collection and Preprocessing
2. Market Making Model Implementation
3. Reinforcement Learning Integration
4. Backtesting Framework
5. Performance Evaluation

## Market Data Utilities

The project includes comprehensive market data utilities in `src/utils/market_data.py` that provide powerful functionality for market analysis and trading:

- `MarketDataHandler`: Class for fetching and processing market data from exchanges
- `OnchainDataHandler`: Class for fetching and processing data from onchain sources
- Utility functions:
  - `calculate_volatility()`: Calculate rolling volatility of price series
  - `estimate_bid_ask_spread()`: Estimate bid-ask spread from volatility
  - `calculate_order_book_imbalance()`: Calculate order book imbalance
  - `calculate_market_impact()`: Calculate market impact of an order
  - `predict_short_term_move()`: Simple predictor for short-term price moves
  - `determine_optimal_position()`: Determine optimal inventory position
  - `calculate_signals()`: Calculate various market signals from data
  - `plot_market_data()`: Plot market data with signals
  - `simulate_latency_impact()`: Simulate impact of latency on trading execution

### Integration Example

An integration example is provided in `integration_example.py` that demonstrates how to use the market data utilities with the backtesting engine. This example:

1. Generates market data
2. Calculates market signals
3. Visualizes market data with signals
4. Estimates optimal spreads based on volatility
5. Runs comparative backtests (standard vs. enhanced with market signals)
6. Analyzes latency impact on trading performance

To run the example:

```bash
python integration_example.py
```

The enhanced backtest engine (`run_backtest_enhanced`) integrates market signals from the utility functions to improve trading performance. 