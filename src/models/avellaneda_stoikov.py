import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AvellanedaStoikovModel:
    """
    Implementation of the Avellaneda-Stoikov market making model
    
    The model determines optimal bid and ask prices based on inventory risk,
    volatility, and time horizon for market makers.
    """
    
    def __init__(self, risk_aversion=1.0, time_horizon=1.0, volatility=None):
        """
        Initialize the Avellaneda-Stoikov model
        
        Parameters:
            risk_aversion (float): Risk aversion parameter (γ)
            time_horizon (float): Time horizon in days
            volatility (float): Market volatility estimate
        """
        self.risk_aversion = risk_aversion
        self.time_horizon = time_horizon
        self.volatility = volatility or 0.01  # Default volatility if not provided
        self.current_inventory = 0
        self.initial_time = datetime.now()
        
    def set_parameters(self, risk_aversion=None, time_horizon=None, volatility=None):
        """
        Update model parameters
        
        Parameters:
            risk_aversion (float): Risk aversion parameter
            time_horizon (float): Time horizon in days
            volatility (float): Market volatility estimate
        """
        if risk_aversion is not None:
            self.risk_aversion = risk_aversion
        if time_horizon is not None:
            self.time_horizon = time_horizon
        if volatility is not None:
            self.volatility = volatility
            
    def update_inventory(self, inventory):
        """
        Update the current inventory
        
        Parameters:
            inventory (float): Current inventory level
        """
        self.current_inventory = inventory
        
    def _calculate_time_remaining(self):
        """
        Calculate the time remaining in the trading horizon
        
        Returns:
            float: Time remaining as a fraction of the total horizon
        """
        elapsed = (datetime.now() - self.initial_time).total_seconds() / (86400)  # Convert to days
        remaining = max(0, self.time_horizon - elapsed)
        return remaining / self.time_horizon if self.time_horizon > 0 else 0
        
    def _calculate_reservation_price(self, mid_price):
        """
        Calculate the reservation price
        
        Parameters:
            mid_price (float): Current mid price
            
        Returns:
            float: Reservation price
        """
        time_remaining = self._calculate_time_remaining()
        if time_remaining <= 0:
            return mid_price
            
        inventory_risk = self.risk_aversion * self.volatility**2 * self.current_inventory * time_remaining
        reservation_price = mid_price - inventory_risk
        
        return reservation_price
        
    def calculate_optimal_quotes(self, mid_price, spread_constraint=None):
        """
        Calculate optimal bid and ask prices
        
        Parameters:
            mid_price (float): Current mid price
            spread_constraint (float): Minimum spread constraint
            
        Returns:
            tuple: (bid_price, ask_price)
        """
        try:
            # Calculate reservation price
            reservation_price = self._calculate_reservation_price(mid_price)
            
            # Calculate time remaining in the horizon
            time_remaining = self._calculate_time_remaining()
            
            # Default spread if at the end of trading horizon
            if time_remaining <= 0:
                if spread_constraint:
                    return mid_price - spread_constraint/2, mid_price + spread_constraint/2
                else:
                    return mid_price * 0.999, mid_price * 1.001
            
            # Calculate optimal spread based on the model
            gamma_sigma_squared = self.risk_aversion * self.volatility**2
            optimal_half_spread = (gamma_sigma_squared * time_remaining + (2/self.risk_aversion) * np.log(1 + self.risk_aversion/2)) / 2
            
            # Apply spread constraint if provided
            if spread_constraint and 2 * optimal_half_spread < spread_constraint:
                optimal_half_spread = spread_constraint / 2
                
            # Calculate optimal bid and ask
            bid_price = reservation_price - optimal_half_spread
            ask_price = reservation_price + optimal_half_spread
            
            logger.debug(f"Mid price: {mid_price}, Reservation price: {reservation_price}, Bid: {bid_price}, Ask: {ask_price}")
            
            return bid_price, ask_price
            
        except Exception as e:
            logger.error(f"Error calculating optimal quotes: {e}")
            # Fallback to a simple spread around mid price
            if spread_constraint:
                return mid_price * (1 - spread_constraint/2), mid_price * (1 + spread_constraint/2)
            else:
                return mid_price * 0.995, mid_price * 1.005
                
    def expected_pnl(self, mid_price, bid_price, ask_price, arrival_rate_bid=1.0, arrival_rate_ask=1.0, time_period=1.0):
        """
        Calculate expected P&L for the given quotes
        
        Parameters:
            mid_price (float): Current mid price
            bid_price (float): Bid price
            ask_price (float): Ask price
            arrival_rate_bid (float): Order arrival rate for bids
            arrival_rate_ask (float): Order arrival rate for asks
            time_period (float): Time period for calculation
            
        Returns:
            float: Expected P&L
        """
        # Probability of order execution
        prob_bid = arrival_rate_bid * time_period * np.exp(-self.risk_aversion * (mid_price - bid_price))
        prob_ask = arrival_rate_ask * time_period * np.exp(-self.risk_aversion * (ask_price - mid_price))
        
        # Expected P&L from bid and ask
        pnl_bid = prob_bid * (mid_price - bid_price)
        pnl_ask = prob_ask * (ask_price - mid_price)
        
        # Inventory risk cost
        inventory_cost = 0.5 * self.risk_aversion * self.volatility**2 * (self.current_inventory**2) * time_period
        
        return pnl_bid + pnl_ask - inventory_cost 