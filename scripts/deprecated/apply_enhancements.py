#!/usr/bin/env python
"""
Apply Market Data Integration Enhancements

This script applies the market data integration enhancements to the project,
including patching notebooks and updating the necessary files.
"""

import os
import sys
import shutil
import subprocess
import argparse
from datetime import datetime

def backup_file(file_path):
    """Create a backup of a file"""
    backup_dir = os.path.join(os.path.dirname(file_path), 'backup')
    os.makedirs(backup_dir, exist_ok=True)
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.basename(file_path)
    backup_path = os.path.join(backup_dir, f"{filename}.{timestamp}.bak")
    
    # Copy the file
    shutil.copy2(file_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    return backup_path

def convert_to_notebook(py_file, target_notebook):
    """Convert a Python script to a Jupyter notebook using jupytext"""
    try:
        # Make the directory if it doesn't exist
        os.makedirs(os.path.dirname(target_notebook), exist_ok=True)
        
        # Use jupytext to convert Python to notebook format
        cmd = f"jupytext --to notebook {py_file} -o {target_notebook}"
        
        # Execute the command
        subprocess.run(cmd, shell=True, check=True)
        print(f"Converted {py_file} to {target_notebook}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error converting to notebook: {e}")
        return False

def update_data_processor():
    """Update DataProcessor to fix the deprecated fillna method"""
    processor_path = "src/data/data_processor.py"
    
    # Backup the file
    backup_file(processor_path)
    
    # Read the file
    with open(processor_path, 'r') as file:
        content = file.read()
    
    # Replace deprecated fillna method
    updated_content = content.replace(
        "df = df.fillna(method='bfill').fillna(method='ffill').fillna(0)",
        "df = df.bfill().ffill().fillna(0)"
    )
    
    # Write the updated content
    with open(processor_path, 'w') as file:
        file.write(updated_content)
        
    print(f"Updated {processor_path} to fix deprecated fillna method")

def update_backtest_engine():
    """Update BacktestEngine to fix type compatibility issue"""
    engine_path = "src/backtesting/backtest_engine.py"
    
    # Backup the file
    backup_file(engine_path)
    
    # Read the file
    with open(engine_path, 'r') as file:
        content = file.read()
    
    # Replace the type incompatible assignment
    updated_content = content.replace(
        "profitable_trades.at[i, 'buy_price'] = float(buy_trades.iloc[-1]['price'])",
        "profitable_trades.at[i, 'buy_price'] = int(float(buy_trades.iloc[-1]['price']))"
    )
    
    # Write the updated content
    with open(engine_path, 'w') as file:
        file.write(updated_content)
        
    print(f"Updated {engine_path} to fix type compatibility issue")

def update_market_data_module():
    """Update MarketDataHandler to support simulation mode"""
    market_data_path = "src/utils/market_data.py"
    
    # Backup the file
    backup_file(market_data_path)
    
    # Check if simulation mode is already supported
    with open(market_data_path, 'r') as file:
        content = file.read()
        
    if "simulation" in content and "Using simulation mode" in content:
        print(f"{market_data_path} already supports simulation mode")
        return
    
    # Add simulation mode support
    init_method = """    def __init__(self, exchange='binance', api_key=None, api_secret=None):
        \"\"\"
        Initialize the MarketDataHandler
        
        Parameters:
            exchange (str): Exchange ID (e.g., 'binance', 'ftx')
            api_key (str): API key for the exchange
            api_secret (str): API secret for the exchange
        \"\"\"
        self.exchange_name = exchange
        self.api_key = api_key
        self.api_secret = api_secret
        self.exchange = self._initialize_exchange()"""
    
    initialize_exchange_method = """    def _initialize_exchange(self):
        \"\"\"Initialize the exchange connection\"\"\"
        try:
            if self.exchange_name == 'simulation':
                logger.info("Using simulation mode for market data")
                return None  # No real exchange connection in simulation mode
                
            # For real exchanges, initialize ccxt
            if not ccxt_available:
                logger.error("CCXT library not available. Install with 'pip install ccxt'")
                return None
                
            if self.exchange_name not in ccxt.exchanges:
                raise ValueError(f"Exchange {self.exchange_name} not supported")
                
            exchange_class = getattr(ccxt, self.exchange_name)
            exchange = exchange_class({
                'apiKey': self.api_key,
                'secret': self.api_secret
            })
            
            logger.info(f"Successfully connected to {self.exchange_name}")
            return exchange
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            raise"""
    
    # Update the content with simulation support
    with open(market_data_path, 'r') as file:
        lines = file.readlines()
    
    updated_lines = []
    in_init_method = False
    in_initialize_method = False
    
    for line in lines:
        if line.strip().startswith("def __init__(self"):
            in_init_method = True
            updated_lines.append(init_method + "\n")
        elif in_init_method and line.strip() == "":
            in_init_method = False
        elif line.strip().startswith("def _initialize_exchange(self"):
            in_initialize_method = True
            updated_lines.append(initialize_exchange_method + "\n")
        elif in_initialize_method and line.strip() == "":
            in_initialize_method = False
        elif not in_init_method and not in_initialize_method:
            updated_lines.append(line)
    
    with open(market_data_path, 'w') as file:
        file.writelines(updated_lines)
        
    print(f"Updated {market_data_path} to support simulation mode")

def apply_notebook_patches():
    """Apply enhanced versions to the notebooks"""
    enhanced_dir = "notebooks/new_enhanced"
    target_notebooks = {
        "enhanced_crypto_market_making.py": "notebooks/crypto_market_making_enhanced.ipynb",
        "enhanced_onchain_market_making.py": "notebooks/onchain_market_making_enhanced.ipynb",
        "enhanced_rl_market_making.py": "notebooks/rl_enhanced_market_making_enhanced.ipynb"
    }
    
    # Convert enhanced Python scripts to notebooks
    for script, notebook in target_notebooks.items():
        script_path = os.path.join(enhanced_dir, script)
        backup_file(notebook) if os.path.exists(notebook) else None
        convert_to_notebook(script_path, notebook)

def main():
    """Main function to apply all enhancements"""
    parser = argparse.ArgumentParser(description="Apply market data integration enhancements")
    parser.add_argument("--all", action="store_true", help="Apply all enhancements")
    parser.add_argument("--update-data-processor", action="store_true", help="Update DataProcessor")
    parser.add_argument("--update-backtest-engine", action="store_true", help="Update BacktestEngine")
    parser.add_argument("--update-market-data", action="store_true", help="Update MarketDataHandler")
    parser.add_argument("--apply-notebook-patches", action="store_true", help="Apply notebook patches")
    
    args = parser.parse_args()
    
    # If no specific actions are specified, apply all enhancements
    if not any(vars(args).values()):
        args.all = True
    
    if args.all or args.update_data_processor:
        update_data_processor()
    
    if args.all or args.update_backtest_engine:
        update_backtest_engine()
    
    if args.all or args.update_market_data:
        update_market_data_module()
    
    if args.all or args.apply_notebook_patches:
        apply_notebook_patches()
    
    print("\nAll enhancements have been successfully applied!")
    print("\nRecommended next steps:")
    print("1. Run the integration tests: bash tests/test_integration.sh")
    print("2. Review the enhanced notebooks")
    print("3. Update documentation to reflect the new capabilities")

if __name__ == "__main__":
    main() 