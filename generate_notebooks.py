import json
import os

# Create the notebooks directory if it doesn't exist
if not os.path.exists('notebooks'):
    os.makedirs('notebooks')

# Crypto Market Making Notebook
crypto_mm_notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": "# Crypto Market Making Bot for USD+/wETH and USD+/cbBTC\n\nThis notebook implements market making algorithms for Overnight.fi using Avellaneda-Stoikov methodology enhanced with Reinforcement Learning (RL)."
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": "# Import necessary libraries\nimport numpy as np\nimport pandas as pd\nimport matplotlib.pyplot as plt\nimport seaborn as sns\nfrom datetime import datetime, timedelta\nimport sys\n\n# Configure plotting\nplt.style.use('ggplot')\n%matplotlib inline\n\n# Add project root to path\nsys.path.append('..')"
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": "# Import project modules\nfrom src.utils.market_data import MarketDataHandler\nfrom src.models.avellaneda_stoikov import AvellanedaStoikovModel\nfrom src.models.rl_enhanced_model import RLEnhancedModel\nfrom src.backtesting.backtest_engine import BacktestEngine\nfrom src.data.data_processor import DataProcessor"
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": "## 1. Generate Market Data"
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": "# Generate synthetic market data\ndata_processor = DataProcessor()\n\n# Define date range\nstart_date = datetime.now() - timedelta(days=30)\nend_date = datetime.now()\ntimestamps = pd.date_range(start=start_date, end=end_date, freq='1min')\n\n# Generate price data\nnp.random.seed(42)\neth_price = 2000.0\nbtc_price = 50000.0\n\neth_prices = [eth_price]\nbtc_prices = [btc_price]\n\nfor _ in range(len(timestamps) - 1):\n    eth_return = np.random.normal(0, 0.001)\n    btc_return = np.random.normal(0, 0.001)\n    \n    eth_price *= (1 + eth_return)\n    btc_price *= (1 + btc_return)\n    \n    eth_prices.append(eth_price)\n    btc_prices.append(btc_price)\n\n# Create DataFrames\neth_usdt_data = pd.DataFrame({\n    'open': eth_prices,\n    'high': [p * (1 + np.random.uniform(0, 0.002)) for p in eth_prices],\n    'low': [p * (1 - np.random.uniform(0, 0.002)) for p in eth_prices],\n    'close': eth_prices,\n    'volume': np.random.uniform(10, 100, size=len(timestamps))\n}, index=timestamps)\n\n# Add technical features\neth_usdt_data = data_processor.add_technical_features(eth_usdt_data)\n\n# Display data\neth_usdt_data.head()"
        }
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

# RL Enhanced Market Making Notebook
rl_mm_notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": "# RL-Enhanced Market Making for Crypto Assets\n\nThis notebook demonstrates how to enhance the Avellaneda-Stoikov market making model with Reinforcement Learning."
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": "# Import necessary libraries\nimport numpy as np\nimport pandas as pd\nimport matplotlib.pyplot as plt\nimport gym\nfrom datetime import datetime, timedelta\nimport sys\n\n# Configure plotting\nplt.style.use('ggplot')\n%matplotlib inline\n\n# Add project root to path\nsys.path.append('..')"
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": "# Import project modules\nfrom src.models.avellaneda_stoikov import AvellanedaStoikovModel\nfrom src.models.rl_enhanced_model import RLEnhancedModel, MarketMakingEnv\nfrom src.data.data_processor import DataProcessor"
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": "## 1. Set Up RL Environment for Market Making"
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": "# Generate synthetic market data\ndata_processor = DataProcessor()\n\n# Generate date range\nstart_date = datetime.now() - timedelta(days=30)\nend_date = datetime.now()\ntimestamps = pd.date_range(start=start_date, end=end_date, freq='1min')\n\n# Generate price data\nnp.random.seed(42)\nprice = 2000.0  # Starting ETH price\nprices = [price]\n\n# Random walk price process\nfor _ in range(len(timestamps) - 1):\n    returns = np.random.normal(0, 0.001)  # Small random returns\n    price *= (1 + returns)\n    prices.append(price)\n\n# Create DataFrame\nmarket_data = pd.DataFrame({\n    'open': prices,\n    'high': [p * (1 + np.random.uniform(0, 0.002)) for p in prices],\n    'low': [p * (1 - np.random.uniform(0, 0.002)) for p in prices],\n    'close': prices,\n    'volume': np.random.uniform(10, 100, size=len(timestamps))\n}, index=timestamps)\n\n# Add technical features\nmarket_data = data_processor.add_technical_features(market_data)\n\n# Create market making environment\nenv = MarketMakingEnv(\n    market_data=market_data,\n    initial_capital=10000.0,\n    max_inventory=20,\n    transaction_fee=0.001,\n    reward_scaling=1.0,\n    trading_horizon=1000\n)\n\n# Reset and get initial observation\ninitial_obs = env.reset()\nprint(f\"Initial observation: {initial_obs}\")\nprint(f\"Observation space: {env.observation_space}\")\nprint(f\"Action space: {env.action_space}\")"
        }
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

# Onchain Market Making Notebook
onchain_mm_notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": "# Onchain Market Making for USD+/wETH and USD+/cbBTC\n\nThis notebook focuses on implementing market making strategies for onchain trading via 1inch PMM and Hashflow PMM."
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": "# Import necessary libraries\nimport numpy as np\nimport pandas as pd\nimport matplotlib.pyplot as plt\nfrom datetime import datetime, timedelta\nimport sys\n\n# Configure plotting\nplt.style.use('ggplot')\n%matplotlib inline\n\n# Add project root to path\nsys.path.append('..')"
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": "# Import project modules\nfrom src.utils.market_data import MarketDataHandler, OnchainDataHandler\nfrom src.models.avellaneda_stoikov import AvellanedaStoikovModel\nfrom src.backtesting.backtest_engine import BacktestEngine\nfrom src.data.data_processor import DataProcessor"
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": "## 1. Simulating Onchain Market Data"
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": "# Generate base CEX data\ndata_processor = DataProcessor()\n\n# Define date range\nstart_date = datetime.now() - timedelta(days=30)\nend_date = datetime.now()\ntimestamps = pd.date_range(start=start_date, end=end_date, freq='1min')\n\n# Generate price data\nnp.random.seed(42)\neth_price = 2000.0\neth_prices = [eth_price]\n\nfor _ in range(len(timestamps) - 1):\n    eth_return = np.random.normal(0, 0.001)\n    eth_price *= (1 + eth_return)\n    eth_prices.append(eth_price)\n\n# Create DataFrame for CEX data\ncex_data = pd.DataFrame({\n    'open': eth_prices,\n    'high': [p * (1 + np.random.uniform(0, 0.002)) for p in eth_prices],\n    'low': [p * (1 - np.random.uniform(0, 0.002)) for p in eth_prices],\n    'close': eth_prices,\n    'volume': np.random.uniform(10, 100, size=len(timestamps))\n}, index=timestamps)\n\n# Add technical features\ncex_data = data_processor.add_technical_features(cex_data)\n\n# Simulate onchain data with higher latency and wider spreads\nonchain_data = data_processor.simulate_onchain_data(\n    cex_data, \n    latency_range=(300, 800),  # Higher latency for onchain\n    fee_range=(0.002, 0.008),  # Higher fees\n    gas_cost_factor=1.2\n)\n\n# Display onchain data\nprint(\"Onchain ETH/USD+ Data:\")\nonchain_data.head()"
        }
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

# Write notebooks to files
with open('notebooks/crypto_market_making.ipynb', 'w') as f:
    json.dump(crypto_mm_notebook, f, indent=1)

with open('notebooks/rl_enhanced_market_making.ipynb', 'w') as f:
    json.dump(rl_mm_notebook, f, indent=1)

with open('notebooks/onchain_market_making.ipynb', 'w') as f:
    json.dump(onchain_mm_notebook, f, indent=1)

print("Notebooks generated successfully!") 