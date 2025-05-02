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