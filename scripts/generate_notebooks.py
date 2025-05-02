import json
import os
import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell
import importlib.util

# Create the notebooks directory if it doesn't exist
if not os.path.exists('notebooks'):
    os.makedirs('notebooks')

# Crypto Market Making Notebook
def generate_crypto_mm_notebook():
    cells = [
        new_markdown_cell("""# Crypto Market Making Bot for USD+/wETH and USD+/cbBTC

This notebook implements market making algorithms for Overnight.fi using Avellaneda-Stoikov methodology enhanced with Reinforcement Learning (RL)."""),
        
        new_code_cell("""# Import necessary libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import sys
import os
import importlib.util

# Configure plotting
plt.style.use('ggplot')
%matplotlib inline

# Add project root to path - use absolute path to ensure reliability
project_root = os.path.abspath('..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added {project_root} to Python path")"""),
        
        new_code_cell("""# Import project modules using a more robust approach
# Import the market_data module directly using importlib
market_data_path = os.path.join(project_root, 'src', 'utils', 'market_data.py')
print(f"Loading market_data.py from: {market_data_path}")

if os.path.exists(market_data_path):
    # Import the module using importlib
    spec = importlib.util.spec_from_file_location("market_data", market_data_path)
    market_data = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(market_data)
    
    # Get MarketDataHandler class from the module
    MarketDataHandler = getattr(market_data, 'MarketDataHandler')
    OnchainDataHandler = getattr(market_data, 'OnchainDataHandler')
    
    print(f"Successfully imported MarketDataHandler")
else:
    print(f"Error: market_data.py not found at {market_data_path}")

# Import other project modules
from src.models.avellaneda_stoikov import AvellanedaStoikovModel
from src.models.rl_enhanced_model import RLEnhancedModel
from src.backtesting.backtest_engine import BacktestEngine
from src.data.data_processor import DataProcessor"""),
        
        new_markdown_cell("## 1. Generate Market Data"),
        
        new_code_cell("""# Generate synthetic market data
data_processor = DataProcessor()

# Define date range
start_date = datetime.now() - timedelta(days=30)
end_date = datetime.now()
timestamps = pd.date_range(start=start_date, end=end_date, freq='1min')

# Generate price data
np.random.seed(42)
eth_price = 2000.0
btc_price = 50000.0

eth_prices = [eth_price]
btc_prices = [btc_price]

for _ in range(len(timestamps) - 1):
    eth_return = np.random.normal(0, 0.001)
    btc_return = np.random.normal(0, 0.001)
    
    eth_price *= (1 + eth_return)
    btc_price *= (1 + btc_return)
    
    eth_prices.append(eth_price)
    btc_prices.append(btc_price)

# Create DataFrames
eth_usdt_data = pd.DataFrame({
    'open': eth_prices,
    'high': [p * (1 + np.random.uniform(0, 0.002)) for p in eth_prices],
    'low': [p * (1 - np.random.uniform(0, 0.002)) for p in eth_prices],
    'close': eth_prices,
    'volume': np.random.uniform(10, 100, size=len(timestamps))
}, index=timestamps)

# Add technical features
eth_usdt_data = data_processor.add_technical_features(eth_usdt_data)

# Display data
eth_usdt_data.head()"""),

        new_markdown_cell("## 2. Implement Avellaneda-Stoikov Market Making Model"),
        
        new_code_cell("""# Initialize the market making model
market_maker = AvellanedaStoikovModel(
    risk_aversion=1.0,  # Risk aversion parameter
    time_horizon=1.0,   # Time horizon in days
    volatility=eth_usdt_data['volatility'].mean()  # Use mean volatility from data
)

# Calculate quotes for a specific time
sample_time = eth_usdt_data.index[100]
sample_data = eth_usdt_data.loc[sample_time]
mid_price = sample_data['mid_price']

# Set model parameters
market_maker.set_parameters(volatility=sample_data['volatility'])
market_maker.update_inventory(0)  # Start with zero inventory

# Calculate optimal quotes
bid_price, ask_price = market_maker.calculate_optimal_quotes(mid_price)

print(f"Mid Price: ${mid_price:.2f}")
print(f"Bid Price: ${bid_price:.2f}")
print(f"Ask Price: ${ask_price:.2f}")
print(f"Spread: ${ask_price - bid_price:.2f} ({(ask_price - bid_price) / mid_price * 100:.4f}%)")"""),

        new_markdown_cell("## 3. Backtest the Market Making Strategy"),
        
        new_code_cell("""# Initialize backtest engine
backtest_engine = BacktestEngine(
    market_data=eth_usdt_data,
    initial_capital=10000.0,
    transaction_fee=0.001
)

# Run backtest with the market making model
backtest_results = backtest_engine.run_backtest(
    model=market_maker,
    params={
        'risk_aversion': 1.0,
        'time_horizon': 1.0
    },
    max_inventory=50,
    volatility_window=20
)

# Display performance metrics
print("Performance Metrics:")
for key, value in backtest_results['metrics'].items():
    print(f"{key}: {value}")"""),

        new_markdown_cell("## 4. Visualize Backtest Results"),
        
        new_code_cell("""# Extract performance data
if backtest_results['positions'] is not None and not backtest_results['positions'].empty:
    performance_data = backtest_results['positions']
    
    # Plot equity curve
    plt.figure(figsize=(12, 6))
    plt.plot(performance_data['timestamp'], performance_data['total_value'], label='Portfolio Value')
    plt.title('Portfolio Value Over Time')
    plt.xlabel('Time')
    plt.ylabel('Value ($)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()
    
    # Plot inventory
    plt.figure(figsize=(12, 6))
    plt.plot(performance_data['timestamp'], performance_data['inventory'], label='Inventory')
    plt.title('Inventory Over Time')
    plt.xlabel('Time')
    plt.ylabel('Inventory')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()
else:
    print("No position data available for plotting")"""),

        new_markdown_cell("## 5. Enhance with Reinforcement Learning"),
        
        new_code_cell("""# Initialize the RL-enhanced model
rl_model = RLEnhancedModel(base_model=market_maker)

# Run backtest with the enhanced model
rl_backtest_results = backtest_engine.run_backtest(
    model=rl_model,
    max_inventory=50,
    volatility_window=20
)

# Compare performance
if backtest_results['positions'] is not None and rl_backtest_results['positions'] is not None:
    base_performance = backtest_results['metrics']['total_pnl']
    rl_performance = rl_backtest_results['metrics']['total_pnl']
    
    print(f"Base Model PnL: ${base_performance:.2f}")
    print(f"RL-Enhanced Model PnL: ${rl_performance:.2f}")
    print(f"Improvement: {(rl_performance - base_performance) / abs(base_performance) * 100:.2f}%")
else:
    print("Insufficient data for comparison")""")
    ]
    
    # Create notebook
    nb = new_notebook(cells=cells, metadata={
        'kernelspec': {
            'display_name': 'Python 3',
            'language': 'python',
            'name': 'python3'
        },
        'language_info': {
            'codemirror_mode': {'name': 'ipython', 'version': 3},
            'file_extension': '.py',
            'mimetype': 'text/x-python',
            'name': 'python',
            'nbconvert_exporter': 'python',
            'pygments_lexer': 'ipython3',
            'version': '3.8.0'
        }
    })
    
    return nb

# RL Enhanced Market Making Notebook
def generate_rl_mm_notebook():
    cells = [
        new_markdown_cell("""# RL-Enhanced Market Making for Crypto Assets

This notebook demonstrates how to enhance the Avellaneda-Stoikov market making model with Reinforcement Learning."""),
        
        new_code_cell("""# Import necessary libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import gym
from datetime import datetime, timedelta
import sys
import os
import importlib.util

# Configure plotting
plt.style.use('ggplot')
%matplotlib inline

# Add project root to path - use absolute path to ensure reliability
project_root = os.path.abspath('..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added {project_root} to Python path")"""),
        
        new_code_cell("""# Import project modules using a more robust approach
# Import the market_data module directly using importlib
market_data_path = os.path.join(project_root, 'src', 'utils', 'market_data.py')
print(f"Loading market_data.py from: {market_data_path}")

if os.path.exists(market_data_path):
    # Import the module using importlib
    spec = importlib.util.spec_from_file_location("market_data", market_data_path)
    market_data = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(market_data)
    
    # Get MarketDataHandler class from the module
    MarketDataHandler = getattr(market_data, 'MarketDataHandler')
    print(f"Successfully imported MarketDataHandler")
else:
    print(f"Error: market_data.py not found at {market_data_path}")

# Import other project modules
from src.models.avellaneda_stoikov import AvellanedaStoikovModel
from src.models.rl_enhanced_model import RLEnhancedModel, MarketMakingEnv
from src.data.data_processor import DataProcessor"""),
        
        new_markdown_cell("## 1. Set Up RL Environment for Market Making"),
        
        new_code_cell("""# Generate synthetic market data
data_processor = DataProcessor()

# Generate date range
start_date = datetime.now() - timedelta(days=30)
end_date = datetime.now()
timestamps = pd.date_range(start=start_date, end=end_date, freq='1min')

# Generate price data
np.random.seed(42)
price = 2000.0  # Starting ETH price
prices = [price]

# Random walk price process
for _ in range(len(timestamps) - 1):
    returns = np.random.normal(0, 0.001)  # Small random returns
    price *= (1 + returns)
    prices.append(price)

# Create DataFrame
market_data = pd.DataFrame({
    'open': prices,
    'high': [p * (1 + np.random.uniform(0, 0.002)) for p in prices],
    'low': [p * (1 - np.random.uniform(0, 0.002)) for p in prices],
    'close': prices,
    'volume': np.random.uniform(10, 100, size=len(timestamps))
}, index=timestamps)

# Add technical features
market_data = data_processor.add_technical_features(market_data)

# Create market making environment
env = MarketMakingEnv(
    market_data=market_data,
    initial_capital=10000.0,
    max_inventory=20,
    transaction_fee=0.001,
    reward_scaling=1.0,
    trading_horizon=1000
)

# Reset and get initial observation
initial_obs = env.reset()
print(f"Initial observation: {initial_obs}")
print(f"Observation space: {env.observation_space}")
print(f"Action space: {env.action_space}")"""),

        new_markdown_cell("## 2. Implement Q-Learning for Market Making"),
        
        new_code_cell("""# Simple Q-learning implementation (simplified for demonstration)
import numpy as np
from collections import defaultdict

class QLearningAgent:
    def __init__(self, action_space, alpha=0.1, gamma=0.99, epsilon=0.1):
        self.action_space = action_space
        self.alpha = alpha  # Learning rate
        self.gamma = gamma  # Discount factor
        self.epsilon = epsilon  # Exploration rate
        self.q_table = defaultdict(lambda: np.zeros(action_space.shape[0] * 10))  # Discretized action space
        
    def discretize_state(self, state):
        # Discretize continuous state space
        # This is a simplified version - in practice, would use better discretization
        return tuple(np.round(state, 1))
    
    def discretize_action(self, action_idx):
        # Convert discrete action index to continuous action
        # Simplified discretization of the continuous action space
        n_actions = self.action_space.shape[0] * 10
        discretized = np.zeros(self.action_space.shape[0])
        
        # Map index to multi-dimensional action
        for i in range(self.action_space.shape[0]):
            bin_size = 10
            action_comp = (action_idx % bin_size) / bin_size
            discretized[i] = self.action_space.low[i] + action_comp * (self.action_space.high[i] - self.action_space.low[i])
            action_idx = action_idx // bin_size
            
        return discretized
    
    def select_action(self, state):
        # Epsilon-greedy action selection
        state_key = self.discretize_state(state)
        
        if np.random.random() < self.epsilon:
            # Explore: random action
            action_idx = np.random.randint(0, len(self.q_table[state_key]))
        else:
            # Exploit: best action
            action_idx = np.argmax(self.q_table[state_key])
            
        return self.discretize_action(action_idx), action_idx
    
    def update(self, state, action_idx, reward, next_state, done):
        # Q-learning update
        state_key = self.discretize_state(state)
        next_state_key = self.discretize_state(next_state)
        
        # Calculate TD target
        if done:
            target = reward
        else:
            target = reward + self.gamma * np.max(self.q_table[next_state_key])
            
        # Update Q-value
        self.q_table[state_key][action_idx] += self.alpha * (target - self.q_table[state_key][action_idx])

# Note: This is a simplified implementation for demonstration purposes.
# In practice, would use more sophisticated RL algorithms like DQN, PPO, etc.
# The state and action discretization is also simplified.

# Train the agent
agent = QLearningAgent(env.action_space, alpha=0.1, gamma=0.99, epsilon=0.3)
n_episodes = 10
max_steps = 100

for episode in range(n_episodes):
    state = env.reset()
    total_reward = 0
    
    for step in range(max_steps):
        # Select action
        action, action_idx = agent.select_action(state)
        
        # Take action
        next_state, reward, done, info = env.step(action)
        
        # Update agent
        agent.update(state, action_idx, reward, next_state, done)
        
        # Update state and reward
        state = next_state
        total_reward += reward
        
        if done:
            break
            
    print(f"Episode {episode+1}: Total Reward = {total_reward:.2f}, Final Inventory = {info['inventory']}")"""),

        new_markdown_cell("## 3. Compare Base Model vs RL-Enhanced Model"),
        
        new_code_cell("""# Initialize models
base_model = AvellanedaStoikovModel(risk_aversion=1.0, time_horizon=1.0, volatility=0.01)
rl_model = RLEnhancedModel(base_model=base_model)

# Test both models on the same price series
test_points = 100
mid_prices = market_data['mid_price'].iloc[:test_points].values
volatility = market_data['volatility'].iloc[:test_points].values

# Store quotes for comparison
base_quotes = []
rl_quotes = []

for i in range(test_points):
    # Update both models with current volatility
    base_model.set_parameters(volatility=volatility[i])
    
    # Calculate quotes
    base_bid, base_ask = base_model.calculate_optimal_quotes(mid_prices[i])
    rl_bid, rl_ask = rl_model.calculate_optimal_quotes(mid_prices[i], {'volatility': volatility[i]})
    
    base_quotes.append((base_bid, base_ask))
    rl_quotes.append((rl_bid, rl_ask))

# Convert to arrays for easier analysis
base_quotes = np.array(base_quotes)
rl_quotes = np.array(rl_quotes)

# Plot the spreads
plt.figure(figsize=(12, 6))
plt.plot(base_quotes[:, 1] - base_quotes[:, 0], label='Base Model Spread')
plt.plot(rl_quotes[:, 1] - rl_quotes[:, 0], label='RL-Enhanced Spread')
plt.title('Spread Comparison: Base vs RL-Enhanced Model')
plt.xlabel('Time Step')
plt.ylabel('Spread')
plt.legend()
plt.grid(True)
plt.show()

# Calculate average spreads
base_avg_spread = np.mean(base_quotes[:, 1] - base_quotes[:, 0])
rl_avg_spread = np.mean(rl_quotes[:, 1] - rl_quotes[:, 0])

print(f"Base Model - Average Spread: {base_avg_spread:.6f}")
print(f"RL-Enhanced Model - Average Spread: {rl_avg_spread:.6f}")
print(f"Difference: {(rl_avg_spread - base_avg_spread) / base_avg_spread * 100:.2f}%")""")
    ]
    
    # Create notebook
    nb = new_notebook(cells=cells, metadata={
        'kernelspec': {
            'display_name': 'Python 3',
            'language': 'python',
            'name': 'python3'
        },
        'language_info': {
            'codemirror_mode': {'name': 'ipython', 'version': 3},
            'file_extension': '.py',
            'mimetype': 'text/x-python',
            'name': 'python',
            'nbconvert_exporter': 'python',
            'pygments_lexer': 'ipython3',
            'version': '3.8.0'
        }
    })
    
    return nb

# Onchain Market Making Notebook
def generate_onchain_mm_notebook():
    cells = [
        new_markdown_cell("""# Onchain Market Making for USD+/wETH and USD+/cbBTC

This notebook focuses on implementing market making strategies for onchain trading via 1inch PMM and Hashflow PMM."""),
        
        new_code_cell("""# Import necessary libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import sys
import os
import importlib.util

# Configure plotting
plt.style.use('ggplot')
%matplotlib inline

# Add project root to path - use absolute path to ensure reliability
project_root = os.path.abspath('..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added {project_root} to Python path")"""),
        
        new_code_cell("""# Import project modules using a more robust approach
# Import the market_data module directly using importlib
market_data_path = os.path.join(project_root, 'src', 'utils', 'market_data.py')
print(f"Loading market_data.py from: {market_data_path}")

if os.path.exists(market_data_path):
    # Import the module using importlib
    spec = importlib.util.spec_from_file_location("market_data", market_data_path)
    market_data = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(market_data)
    
    # Get MarketDataHandler and OnchainDataHandler classes from the module
    MarketDataHandler = getattr(market_data, 'MarketDataHandler')
    OnchainDataHandler = getattr(market_data, 'OnchainDataHandler')
    print(f"Successfully imported MarketDataHandler and OnchainDataHandler")
else:
    print(f"Error: market_data.py not found at {market_data_path}")

# Import other project modules
from src.models.avellaneda_stoikov import AvellanedaStoikovModel
from src.backtesting.backtest_engine import BacktestEngine
from src.data.data_processor import DataProcessor"""),
        
        new_markdown_cell("## 1. Simulating Onchain Market Data"),
        
        new_code_cell("""# Generate base CEX data
data_processor = DataProcessor()

# Define date range
start_date = datetime.now() - timedelta(days=30)
end_date = datetime.now()
timestamps = pd.date_range(start=start_date, end=end_date, freq='1min')

# Generate price data
np.random.seed(42)
eth_price = 2000.0
eth_prices = [eth_price]

for _ in range(len(timestamps) - 1):
    eth_return = np.random.normal(0, 0.001)
    eth_price *= (1 + eth_return)
    eth_prices.append(eth_price)

# Create DataFrame for CEX data
cex_data = pd.DataFrame({
    'open': eth_prices,
    'high': [p * (1 + np.random.uniform(0, 0.002)) for p in eth_prices],
    'low': [p * (1 - np.random.uniform(0, 0.002)) for p in eth_prices],
    'close': eth_prices,
    'volume': np.random.uniform(10, 100, size=len(timestamps))
}, index=timestamps)

# Add technical features
cex_data = data_processor.add_technical_features(cex_data)

# Simulate onchain data with higher latency and wider spreads
onchain_data = data_processor.simulate_onchain_data(
    cex_data, 
    latency_range=(300, 800),  # Higher latency for onchain (ms)
    fee_range=(0.002, 0.008),  # Higher fees
    gas_cost_factor=1.2
)

# Display onchain data
print("Onchain ETH/USD+ Data:")
onchain_data.head()"""),

        new_markdown_cell("## 2. Analyzing Onchain vs CEX Data"),
        
        new_code_cell("""# Compare spreads between CEX and onchain
plt.figure(figsize=(12, 6))
plt.hist(onchain_data['spread'] * 100, bins=50, alpha=0.5, label='Onchain Spread (%)')
plt.axvline(onchain_data['spread'].mean() * 100, color='r', linestyle='--', label=f'Mean Onchain Spread: {onchain_data["spread"].mean()*100:.4f}%')
plt.title('Distribution of Onchain Spreads')
plt.xlabel('Spread (%)')
plt.ylabel('Frequency')
plt.legend()
plt.grid(True)
plt.show()

# Compare latency impact
plt.figure(figsize=(12, 6))
plt.scatter(onchain_data['latency_ms'], onchain_data['fee_pct'], alpha=0.5)
plt.title('Relationship Between Latency and Fees in Onchain Data')
plt.xlabel('Latency (ms)')
plt.ylabel('Fee (%)')
plt.grid(True)
plt.show()

# Compare gas costs
plt.figure(figsize=(12, 6))
plt.plot(onchain_data.index, onchain_data['gas_cost_usd'], label='Gas Cost (USD)')
plt.title('Gas Costs Over Time')
plt.xlabel('Time')
plt.ylabel('Cost (USD)')
plt.legend()
plt.grid(True)
plt.show()"""),

        new_markdown_cell("## 3. Adapting Market Making for Onchain Trading"),
        
        new_code_cell("""# Modify Avellaneda-Stoikov parameters for onchain trading
onchain_market_maker = AvellanedaStoikovModel(
    risk_aversion=1.5,  # Higher risk aversion for onchain
    time_horizon=0.5,   # Shorter time horizon due to higher volatility
    volatility=onchain_data['volatility'].mean() * 1.2  # Increase volatility estimate for safety
)

# Calculate quotes for onchain trading
sample_time = onchain_data.index[100]
sample_data = onchain_data.loc[sample_time]
mid_price = sample_data['mid_price']

# Set model parameters
onchain_market_maker.set_parameters(volatility=sample_data['volatility'] * 1.2)
onchain_market_maker.update_inventory(0)  # Start with zero inventory

# Calculate optimal quotes
bid_price, ask_price = onchain_market_maker.calculate_optimal_quotes(mid_price)

# Add gas cost adjustment to ask price and subtract from bid price
gas_cost_per_unit = sample_data['gas_cost_usd'] / 1.0  # Assuming 1 ETH trade
adjusted_bid = bid_price - gas_cost_per_unit
adjusted_ask = ask_price + gas_cost_per_unit

print(f"Mid Price: ${mid_price:.2f}")
print(f"Base Bid Price: ${bid_price:.2f}, Base Ask Price: ${ask_price:.2f}")
print(f"Gas Cost per Unit: ${gas_cost_per_unit:.2f}")
print(f"Gas-Adjusted Bid Price: ${adjusted_bid:.2f}, Gas-Adjusted Ask Price: ${adjusted_ask:.2f}")
print(f"Base Spread: ${ask_price - bid_price:.2f} ({(ask_price - bid_price) / mid_price * 100:.4f}%)")
print(f"Gas-Adjusted Spread: ${adjusted_ask - adjusted_bid:.2f} ({(adjusted_ask - adjusted_bid) / mid_price * 100:.4f}%)")"""),

        new_markdown_cell("## 4. Backtesting Onchain Market Making Strategy"),
        
        new_code_cell("""# Initialize backtest engine for onchain trading
onchain_backtest_engine = BacktestEngine(
    market_data=onchain_data,
    initial_capital=10000.0,
    transaction_fee=0.003  # Higher fee for onchain
)

# Custom function to adjust quotes with gas costs
def gas_adjusted_quotes(model, mid_price, gas_cost):
    # Get base quotes from model
    bid_price, ask_price = model.calculate_optimal_quotes(mid_price)
    
    # Adjust for gas costs
    adjusted_bid = bid_price - gas_cost
    adjusted_ask = ask_price + gas_cost
    
    return adjusted_bid, adjusted_ask

# Prepare for backtesting
gas_costs = onchain_data['gas_cost_usd'].values
mid_prices = onchain_data['mid_price'].values

# Simulate trades with gas-adjusted quotes
trades = []
inventory = 0
capital = 10000.0
transaction_fee = 0.003

for i in range(len(onchain_data) - 1):
    # Get current data
    current_data = onchain_data.iloc[i]
    next_data = onchain_data.iloc[i+1]
    
    # Calculate gas-adjusted quotes
    gas_cost_per_unit = current_data['gas_cost_usd'] / 1.0  # For 1 ETH trade
    bid_price, ask_price = onchain_market_maker.calculate_optimal_quotes(current_data['mid_price'])
    adjusted_bid = max(0, bid_price - gas_cost_per_unit)  # Ensure non-negative
    adjusted_ask = ask_price + gas_cost_per_unit
    
    # Check if bid is executed (price falls below our bid)
    bid_executed = next_data['low'] <= adjusted_bid
    if bid_executed and inventory < 10:  # Limit inventory
        # Buy 1 unit
        inventory += 1
        capital -= adjusted_bid * (1 + transaction_fee)
        trades.append({
            'timestamp': next_data.name,
            'type': 'BUY',
            'price': adjusted_bid,
            'inventory': inventory,
            'capital': capital
        })
    
    # Check if ask is executed (price rises above our ask)
    ask_executed = next_data['high'] >= adjusted_ask
    if ask_executed and inventory > 0:
        # Sell 1 unit
        inventory -= 1
        capital += adjusted_ask * (1 - transaction_fee)
        trades.append({
            'timestamp': next_data.name,
            'type': 'SELL',
            'price': adjusted_ask,
            'inventory': inventory,
            'capital': capital
        })

# Convert to DataFrame
trades_df = pd.DataFrame(trades)

if not trades_df.empty:
    # Calculate final P&L
    final_price = onchain_data['mid_price'].iloc[-1]
    final_value = capital + inventory * final_price
    initial_value = 10000.0
    total_pnl = final_value - initial_value
    
    print(f"Total Trades: {len(trades_df)}")
    print(f"Final Inventory: {inventory}")
    print(f"Final Capital: ${capital:.2f}")
    print(f"Final Portfolio Value: ${final_value:.2f}")
    print(f"Total P&L: ${total_pnl:.2f} ({total_pnl/initial_value*100:.2f}%)")
    
    # Plot trades and performance
    if len(trades_df) > 0:
        plt.figure(figsize=(12, 8))
        plt.subplot(211)
        plt.plot(onchain_data.index, onchain_data['mid_price'], label='Mid Price')
        
        # Plot buy and sell points
        buys = trades_df[trades_df['type'] == 'BUY']
        sells = trades_df[trades_df['type'] == 'SELL']
        
        if not buys.empty:
            plt.scatter(buys['timestamp'], buys['price'], marker='^', color='g', label='Buy')
        if not sells.empty:
            plt.scatter(sells['timestamp'], sells['price'], marker='v', color='r', label='Sell')
            
        plt.title('Onchain Market Making: Trading Activity')
        plt.legend()
        plt.grid(True)
        
        # Plot portfolio value
        plt.subplot(212)
        plt.plot(trades_df['timestamp'], trades_df['capital'], label='Capital')
        plt.title('Capital Over Time')
        plt.grid(True)
        
        plt.tight_layout()
        plt.show()
else:
    print("No trades were executed in the simulation period.")""")
    ]
    
    # Create notebook
    nb = new_notebook(cells=cells, metadata={
        'kernelspec': {
            'display_name': 'Python 3',
            'language': 'python',
            'name': 'python3'
        },
        'language_info': {
            'codemirror_mode': {'name': 'ipython', 'version': 3},
            'file_extension': '.py',
            'mimetype': 'text/x-python',
            'name': 'python',
            'nbconvert_exporter': 'python',
            'pygments_lexer': 'ipython3',
            'version': '3.8.0'
        }
    })
    
    return nb

# Write updated notebooks to files
with open('notebooks/crypto_market_making.ipynb', 'w') as f:
    nbformat.write(generate_crypto_mm_notebook(), f)

with open('notebooks/rl_enhanced_market_making.ipynb', 'w') as f:
    nbformat.write(generate_rl_mm_notebook(), f)

with open('notebooks/onchain_market_making.ipynb', 'w') as f:
    nbformat.write(generate_onchain_mm_notebook(), f)

print("Enhanced notebooks generated successfully!") 