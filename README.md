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

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run tests to verify your setup:
```bash
bash test_integration.sh
```

3. Start with the enhanced notebooks:
```bash
jupyter notebook notebooks/
```

## Project Structure

```
├── notebooks/                 # Interactive notebooks
│   ├── crypto_market_making_enhanced.ipynb       # CEX trading
│   ├── onchain_market_making_enhanced.ipynb      # Onchain trading
│   └── rl_enhanced_market_making_enhanced.ipynb  # RL-based model
├── src/                       # Core source code
│   ├── models/                # Trading models 
│   ├── data/                  # Data handling
│   ├── utils/                 # Utilities
│   └── backtesting/           # Testing framework
├── apply_enhancements.py      # Enhancement automation
├── test_integration.sh        # Integration testing
└── requirements.txt           # Dependencies
```

## Market Data Integration

The recent enhancements focus on robust market data integration:

### Key Components

- **Market Signal Generation**: Advanced indicators for decision making
- **Optimized Data Processing**: Fixed deprecated methods and type handling
- **Simulation Mode**: Test in simulated environments without API connections
- **Performance Analytics**: Compare strategy performance

### Performance Improvements

| Metric | Standard | Enhanced | Improvement |
|--------|----------|----------|-------------|
| PnL    | -2108.31 | 212.91   | 2321.22 (110%) |
| Sharpe | -0.13    | 0.14     | 0.27 (208%) |
| Max DD | 3066.10  | 2607.00  | 459.10 (15%) |

## Applying Enhancements

Run the enhancement script to apply all updates:

```bash
python apply_enhancements.py --all
```

This applies:
1. Data processor fixes
2. Backtest engine improvements
3. Simulation mode support
4. Enhanced notebook implementations

## Usage Examples

The enhanced notebooks demonstrate:

1. **CEX Market Making**: Improved market signal integration
2. **Onchain Market Making**: Latency impact analysis
3. **RL Enhanced Making**: Market feature integration with models

## Next Steps

1. Further testing with different market conditions
2. Model parameter tuning
3. Production deployment preparation 