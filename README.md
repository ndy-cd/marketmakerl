# Crypto Market Making System

A sophisticated market making system for cryptocurrency trading, with integrated market data analysis capabilities.

## Overview

This system provides an enhanced market making solution based on the Avellaneda-Stoikov methodology, with added Reinforcement Learning (RL) capabilities. It supports both centralized exchanges and onchain venues, handling different latency and execution characteristics.

## Key Features

- **Advanced Market Making Models**
  - Avellaneda-Stoikov implementation
  - RL-enhanced dynamic adaptation
  
- **Comprehensive Market Data Integration**
  - Market signal generation and analysis
  - Real-time data processing pipeline
  - Volatility and trend detection
  
- **Multi-Venue Support**
  - Centralized exchange integration
  - Onchain trading capabilities
  - Latency impact analysis
  
- **Robust Testing Tools**
  - Simulation environment
  - Performance comparison framework
  - Visualization utilities

## Project Structure

```
├── docs/                     # Documentation
│   └── completed_enhancements.md  # Details of implemented enhancements
│
├── notebooks/                # Interactive notebooks
│   ├── crypto_market_making_enhanced.ipynb    # CEX trading
│   ├── onchain_market_making_enhanced.ipynb   # Onchain trading
│   └── rl_enhanced_market_making_enhanced.ipynb  # RL-based model
│
├── scripts/                  # Utility scripts
│   └── integration_example.py     # Integration example
│
├── src/                      # Core source code
│   ├── models/               # Trading models 
│   ├── data/                 # Data handling
│   ├── utils/                # Utilities
│   └── backtesting/          # Testing framework
│
├── tests/                    # Testing
│   ├── test_integration.sh        # Integration test script
│   └── test_market_data_integration.py  # Market data tests
│
├── visualizations/           # Performance visualizations
│   ├── backtest_comparison.png    # Backtest results comparison
│   ├── latency_impact.png         # Latency analysis
│   └── market_data_analysis.png   # Market data visualization
│
└── requirements.txt          # Dependencies
```

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run tests to verify your setup:
```bash
bash tests/test_integration.sh
```

3. Start with the enhanced notebooks:
```bash
jupyter notebook notebooks/
```

## Market Data Integration

The project includes robust market data integration:

### Key Components

- **Market Signal Generation**: Advanced indicators for decision making
- **Optimized Data Processing**: Uses modern data handling methods
- **Simulation Mode**: Test in simulated environments without API connections
- **Performance Analytics**: Compare strategy performance

### Performance Improvements

| Metric | Standard | Enhanced | Improvement |
|--------|----------|----------|-------------|
| PnL    | -3184.61 | -1239.22 | 1945.39 (61%) |
| Sharpe | -2.19    | -0.20    | 1.99 (91%) |
| Max DD | 3209.52  | 1850.66  | 1358.86 (42%) |

## Enhanced Notebooks

The notebooks in this repository demonstrate:

1. **CEX Market Making**: Improved market signal integration
2. **Onchain Market Making**: Latency impact analysis
3. **RL Enhanced Making**: Market feature integration with models

## Next Steps

1. Further testing with different market conditions
2. Model parameter tuning
3. Production deployment preparation 