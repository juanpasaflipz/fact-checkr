"""
Prediction Market AMM (Automated Market Maker) Service

Implements a Constant Product Market Maker (CPMM) for binary YES/NO prediction markets.
This is similar to Polymarket's pricing mechanism.

The CPMM maintains a constant product: yes_liquidity * no_liquidity = k
When someone buys YES shares, yes_liquidity increases and no_liquidity decreases.
The price per share is determined by the ratio of liquidity pools.

Key assumptions:
- Initial liquidity: 1000 YES, 1000 NO (50/50 probability)
- Constant product formula: k = yes_liquidity * no_liquidity
- Shares are priced based on marginal liquidity changes
- Each share pays out 1 credit when the market resolves in favor of that outcome
"""

from typing import Tuple
from sqlalchemy.orm import Session
from app.database.models import Market


def yes_probability(market: Market) -> float:
    """
    Calculate the implied probability of YES outcome.
    
    Formula: yes_probability = yes_liquidity / (yes_liquidity + no_liquidity)
    
    Args:
        market: Market instance with liquidity values
        
    Returns:
        Float between 0.0 and 1.0 representing YES probability
    """
    total_liquidity = market.yes_liquidity + market.no_liquidity
    if total_liquidity == 0:
        return 0.5  # Default to 50/50 if no liquidity
    
    return market.yes_liquidity / total_liquidity


def no_probability(market: Market) -> float:
    """
    Calculate the implied probability of NO outcome.
    
    Formula: no_probability = 1.0 - yes_probability
    
    Args:
        market: Market instance with liquidity values
        
    Returns:
        Float between 0.0 and 1.0 representing NO probability
    """
    return 1.0 - yes_probability(market)


def buy_yes(market: Market, amount: float, db: Session) -> Tuple[float, Market]:
    """
    Buy YES shares using constant product market maker.
    
    When buying YES shares:
    1. Calculate new yes_liquidity after adding amount
    2. Maintain constant product: yes_liquidity * no_liquidity = k
    3. Calculate shares received based on liquidity change
    4. Update market liquidity
    
    Formula:
    - k = yes_liquidity * no_liquidity (constant product)
    - new_yes_liquidity = yes_liquidity + amount
    - new_no_liquidity = k / new_yes_liquidity
    - shares = no_liquidity - new_no_liquidity
    
    Args:
        market: Market instance to trade on
        amount: Credits to spend
        db: Database session
        
    Returns:
        Tuple of (shares_bought, updated_market)
    """
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    # Store initial constant product
    k = market.yes_liquidity * market.no_liquidity
    
    # Calculate new liquidity after adding amount to YES pool
    new_yes_liquidity = market.yes_liquidity + amount
    
    # Maintain constant product: adjust NO liquidity
    if new_yes_liquidity == 0:
        raise ValueError("Cannot buy YES shares: insufficient liquidity")
    
    new_no_liquidity = k / new_yes_liquidity
    
    # Shares received = reduction in NO liquidity
    # This represents how many YES shares can be bought
    shares = market.no_liquidity - new_no_liquidity
    
    if shares <= 0:
        raise ValueError("Insufficient liquidity to complete trade")
    
    # Update market liquidity
    market.yes_liquidity = new_yes_liquidity
    market.no_liquidity = new_no_liquidity
    
    db.commit()
    db.refresh(market)
    
    return shares, market


def buy_no(market: Market, amount: float, db: Session) -> Tuple[float, Market]:
    """
    Buy NO shares using constant product market maker.
    
    Mirror of buy_yes, but for NO outcome:
    1. Calculate new no_liquidity after adding amount
    2. Maintain constant product: yes_liquidity * no_liquidity = k
    3. Calculate shares received based on liquidity change
    4. Update market liquidity
    
    Formula:
    - k = yes_liquidity * no_liquidity (constant product)
    - new_no_liquidity = no_liquidity + amount
    - new_yes_liquidity = k / new_no_liquidity
    - shares = yes_liquidity - new_yes_liquidity
    
    Args:
        market: Market instance to trade on
        amount: Credits to spend
        db: Database session
        
    Returns:
        Tuple of (shares_bought, updated_market)
    """
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    # Store initial constant product
    k = market.yes_liquidity * market.no_liquidity
    
    # Calculate new liquidity after adding amount to NO pool
    new_no_liquidity = market.no_liquidity + amount
    
    # Maintain constant product: adjust YES liquidity
    if new_no_liquidity == 0:
        raise ValueError("Cannot buy NO shares: insufficient liquidity")
    
    new_yes_liquidity = k / new_no_liquidity
    
    # Shares received = reduction in YES liquidity
    # This represents how many NO shares can be bought
    shares = market.yes_liquidity - new_yes_liquidity
    
    if shares <= 0:
        raise ValueError("Insufficient liquidity to complete trade")
    
    # Update market liquidity
    market.yes_liquidity = new_yes_liquidity
    market.no_liquidity = new_no_liquidity
    
    db.commit()
    db.refresh(market)
    
    return shares, market


def calculate_volume(market: Market, db: Session) -> float:
    """
    Calculate total trading volume for a market.
    
    Volume = sum of all trade costs (credits spent)
    
    Args:
        market: Market instance
        db: Database session
        
    Returns:
        Total volume in credits
    """
    from app.database.models import MarketTrade
    from sqlalchemy import func
    
    result = db.query(func.sum(MarketTrade.cost)).filter(
        MarketTrade.market_id == market.id
    ).scalar()
    
    return float(result) if result else 0.0

