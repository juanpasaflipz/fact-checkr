"""
Calibration System for Market Predictions

Tracks prediction accuracy over time and adjusts probabilities
to ensure calibration - when we say 70%, we should be right ~70% of the time.

Key metrics:
- Brier Score: Mean squared error of predictions (lower is better)
- Calibration Curve: Predicted probability vs actual frequency
- Reliability Diagram: Visual representation of calibration
"""

import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import math

from sqlalchemy.orm import Session
from sqlalchemy import text, func

logger = logging.getLogger(__name__)


@dataclass
class CalibrationBucket:
    """A bucket in the calibration curve."""
    predicted_low: float
    predicted_high: float
    predicted_avg: float
    actual_frequency: float
    count: int
    
    @property
    def calibration_error(self) -> float:
        """Difference between predicted and actual."""
        return abs(self.predicted_avg - self.actual_frequency)


@dataclass
class CalibrationReport:
    """Complete calibration report for an agent."""
    agent_id: str
    brier_score: float
    calibration_error: float  # Average calibration error across buckets
    num_predictions: int
    num_resolved: int
    buckets: List[CalibrationBucket]
    overconfidence_bias: float  # Positive = overconfident, negative = underconfident
    time_period_days: int
    generated_at: datetime


class CalibrationTracker:
    """
    Tracks and adjusts prediction calibration.
    
    Maintains historical record of predictions and outcomes to:
    1. Calculate calibration metrics (Brier score, calibration curve)
    2. Automatically adjust future predictions based on past performance
    3. Identify systematic biases (overconfidence, underconfidence)
    """
    
    # Calibration buckets for the calibration curve
    BUCKET_BOUNDARIES = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    
    def __init__(self, db: Session):
        self.db = db
    
    def record_prediction(
        self,
        market_id: int,
        agent_id: str,
        predicted_probability: float,
        confidence: float = None
    ) -> bool:
        """
        Record a prediction for later calibration analysis.
        
        Args:
            market_id: The market being predicted
            agent_id: Identifier for the prediction agent
            predicted_probability: The probability assigned (0-1)
            confidence: Optional confidence score
        
        Returns:
            True if successfully recorded
        """
        try:
            self.db.execute(
                text("""
                    INSERT INTO agent_performance 
                    (agent_id, market_id, predicted_probability, prediction_date)
                    VALUES (:agent_id, :market_id, :predicted_prob, :pred_date)
                    ON CONFLICT (agent_id, market_id) 
                    DO UPDATE SET 
                        predicted_probability = :predicted_prob,
                        prediction_date = :pred_date
                """),
                {
                    "agent_id": agent_id,
                    "market_id": market_id,
                    "predicted_prob": predicted_probability,
                    "pred_date": datetime.utcnow()
                }
            )
            self.db.commit()
            logger.debug(f"Recorded prediction for market {market_id}: {predicted_probability:.3f}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording prediction: {e}")
            self.db.rollback()
            return False
    
    def record_resolution(
        self,
        market_id: int,
        outcome: str  # "yes" or "no"
    ) -> bool:
        """
        Record the resolution of a market and update Brier scores.
        
        Args:
            market_id: The resolved market
            outcome: "yes" or "no"
        
        Returns:
            True if successfully updated
        """
        try:
            # Get actual outcome as 0 or 1
            actual = 1.0 if outcome.lower() == "yes" else 0.0
            
            # Update all predictions for this market
            self.db.execute(
                text("""
                    UPDATE agent_performance
                    SET 
                        actual_outcome = :outcome,
                        resolution_date = :res_date,
                        brier_score = POWER(predicted_probability - :actual, 2)
                    WHERE market_id = :market_id
                      AND actual_outcome IS NULL
                """),
                {
                    "outcome": outcome.lower(),
                    "res_date": datetime.utcnow(),
                    "actual": actual,
                    "market_id": market_id
                }
            )
            self.db.commit()
            logger.info(f"Recorded resolution for market {market_id}: {outcome}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording resolution: {e}")
            self.db.rollback()
            return False
    
    def calculate_brier_score(
        self,
        agent_id: str,
        timeframe_days: int = 90
    ) -> float:
        """
        Calculate Brier score for an agent over a time period.
        
        Brier score = mean((predicted - actual)^2)
        Perfect score = 0, worst score = 1
        
        Args:
            agent_id: The agent to evaluate
            timeframe_days: Number of days to look back
        
        Returns:
            Brier score (0-1, lower is better)
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=timeframe_days)
            
            result = self.db.execute(
                text("""
                    SELECT AVG(brier_score) as avg_brier
                    FROM agent_performance
                    WHERE agent_id = :agent_id
                      AND actual_outcome IS NOT NULL
                      AND resolution_date >= :cutoff
                      AND brier_score IS NOT NULL
                """),
                {"agent_id": agent_id, "cutoff": cutoff}
            ).fetchone()
            
            if result and result.avg_brier is not None:
                return float(result.avg_brier)
            
            return 0.25  # Default (equivalent to always predicting 0.5)
            
        except Exception as e:
            logger.error(f"Error calculating Brier score: {e}")
            return 0.25
    
    def get_calibration_curve(
        self,
        agent_id: str,
        timeframe_days: int = 90
    ) -> List[CalibrationBucket]:
        """
        Calculate calibration curve - predicted vs actual frequency.
        
        Groups predictions into buckets and compares predicted
        probability to actual resolution frequency.
        
        Args:
            agent_id: The agent to evaluate
            timeframe_days: Number of days to look back
        
        Returns:
            List of CalibrationBucket objects
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=timeframe_days)
            
            # Get all resolved predictions
            results = self.db.execute(
                text("""
                    SELECT 
                        predicted_probability,
                        actual_outcome
                    FROM agent_performance
                    WHERE agent_id = :agent_id
                      AND actual_outcome IS NOT NULL
                      AND resolution_date >= :cutoff
                """),
                {"agent_id": agent_id, "cutoff": cutoff}
            ).fetchall()
            
            if not results:
                return []
            
            # Group into buckets
            buckets = []
            for i in range(len(self.BUCKET_BOUNDARIES) - 1):
                low = self.BUCKET_BOUNDARIES[i]
                high = self.BUCKET_BOUNDARIES[i + 1]
                
                # Get predictions in this bucket
                bucket_preds = [
                    r for r in results
                    if low <= r.predicted_probability < high
                ]
                
                if bucket_preds:
                    predicted_avg = sum(r.predicted_probability for r in bucket_preds) / len(bucket_preds)
                    actual_yes = sum(1 for r in bucket_preds if r.actual_outcome == "yes")
                    actual_freq = actual_yes / len(bucket_preds)
                    
                    buckets.append(CalibrationBucket(
                        predicted_low=low,
                        predicted_high=high,
                        predicted_avg=predicted_avg,
                        actual_frequency=actual_freq,
                        count=len(bucket_preds)
                    ))
            
            return buckets
            
        except Exception as e:
            logger.error(f"Error calculating calibration curve: {e}")
            return []
    
    def adjust_probability(
        self,
        raw_prob: float,
        agent_id: str,
        timeframe_days: int = 90
    ) -> float:
        """
        Adjust a raw probability based on historical calibration.
        
        Uses Platt scaling / isotonic regression concepts to adjust
        predictions toward better calibration.
        
        Args:
            raw_prob: The unadjusted prediction (0-1)
            agent_id: The agent making the prediction
            timeframe_days: Historical period for calibration
        
        Returns:
            Calibrated probability (0-1)
        """
        try:
            # Get calibration curve
            buckets = self.get_calibration_curve(agent_id, timeframe_days)
            
            if not buckets or len(buckets) < 3:
                # Not enough data for calibration, return raw
                return raw_prob
            
            # Find the bucket this prediction falls into
            for bucket in buckets:
                if bucket.predicted_low <= raw_prob < bucket.predicted_high:
                    # Calculate adjustment
                    # If actual > predicted historically, adjust up
                    # If actual < predicted historically, adjust down
                    
                    if bucket.count < 5:
                        # Not enough samples in this bucket, use weighted adjustment
                        adjustment = (bucket.actual_frequency - bucket.predicted_avg) * 0.5
                    else:
                        adjustment = (bucket.actual_frequency - bucket.predicted_avg) * 0.8
                    
                    calibrated = raw_prob + adjustment
                    
                    # Clamp to valid range
                    calibrated = max(0.02, min(0.98, calibrated))
                    
                    logger.debug(
                        f"Calibration adjustment for {raw_prob:.3f}: "
                        f"{adjustment:+.3f} -> {calibrated:.3f}"
                    )
                    
                    return calibrated
            
            # Fallback: no matching bucket
            return raw_prob
            
        except Exception as e:
            logger.error(f"Error adjusting probability: {e}")
            return raw_prob
    
    def get_calibration_report(
        self,
        agent_id: str,
        timeframe_days: int = 90
    ) -> CalibrationReport:
        """
        Generate a complete calibration report for an agent.
        
        Args:
            agent_id: The agent to evaluate
            timeframe_days: Historical period
        
        Returns:
            CalibrationReport with all metrics
        """
        brier = self.calculate_brier_score(agent_id, timeframe_days)
        buckets = self.get_calibration_curve(agent_id, timeframe_days)
        
        # Calculate overall calibration error
        if buckets:
            weighted_error = sum(b.calibration_error * b.count for b in buckets)
            total_count = sum(b.count for b in buckets)
            calibration_error = weighted_error / total_count if total_count > 0 else 0
        else:
            calibration_error = 0
        
        # Calculate overconfidence bias
        # Positive = predictions are too extreme (overconfident)
        # Negative = predictions are too moderate (underconfident)
        overconfidence = 0.0
        if buckets:
            # Check extreme buckets (0-0.3 and 0.7-1.0)
            extreme_buckets = [b for b in buckets if b.predicted_avg < 0.3 or b.predicted_avg > 0.7]
            if extreme_buckets:
                # If predicted extremes are more extreme than actual, overconfident
                bias_sum = sum(
                    (abs(b.predicted_avg - 0.5) - abs(b.actual_frequency - 0.5)) * b.count
                    for b in extreme_buckets
                )
                total = sum(b.count for b in extreme_buckets)
                overconfidence = bias_sum / total if total > 0 else 0
        
        # Count predictions
        try:
            cutoff = datetime.utcnow() - timedelta(days=timeframe_days)
            counts = self.db.execute(
                text("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(actual_outcome) as resolved
                    FROM agent_performance
                    WHERE agent_id = :agent_id
                      AND prediction_date >= :cutoff
                """),
                {"agent_id": agent_id, "cutoff": cutoff}
            ).fetchone()
            
            num_predictions = counts.total if counts else 0
            num_resolved = counts.resolved if counts else 0
        except Exception:
            num_predictions = 0
            num_resolved = 0
        
        return CalibrationReport(
            agent_id=agent_id,
            brier_score=brier,
            calibration_error=calibration_error,
            num_predictions=num_predictions,
            num_resolved=num_resolved,
            buckets=buckets,
            overconfidence_bias=overconfidence,
            time_period_days=timeframe_days,
            generated_at=datetime.utcnow()
        )
    
    def get_agent_comparison(
        self,
        agent_ids: List[str],
        timeframe_days: int = 90
    ) -> Dict[str, CalibrationReport]:
        """
        Compare calibration metrics across multiple agents.
        
        Args:
            agent_ids: List of agents to compare
            timeframe_days: Historical period
        
        Returns:
            Dictionary mapping agent_id to CalibrationReport
        """
        return {
            agent_id: self.get_calibration_report(agent_id, timeframe_days)
            for agent_id in agent_ids
        }


def calculate_brier_score_simple(predictions: List[Tuple[float, bool]]) -> float:
    """
    Calculate Brier score from a list of (prediction, actual) tuples.
    
    Useful for quick calculations without database.
    
    Args:
        predictions: List of (predicted_probability, actual_outcome_bool) tuples
    
    Returns:
        Brier score (0-1, lower is better)
    """
    if not predictions:
        return 0.25  # Default
    
    squared_errors = [
        (pred - (1.0 if actual else 0.0)) ** 2
        for pred, actual in predictions
    ]
    
    return sum(squared_errors) / len(squared_errors)


def calculate_log_loss(predictions: List[Tuple[float, bool]], epsilon: float = 1e-15) -> float:
    """
    Calculate log loss (cross-entropy) from predictions.
    
    More sensitive to confident wrong predictions than Brier score.
    
    Args:
        predictions: List of (predicted_probability, actual_outcome_bool) tuples
        epsilon: Small value to avoid log(0)
    
    Returns:
        Log loss (lower is better)
    """
    if not predictions:
        return 0.693  # log(0.5), equivalent to random guessing
    
    losses = []
    for pred, actual in predictions:
        pred = max(epsilon, min(1 - epsilon, pred))  # Clamp
        if actual:
            losses.append(-math.log(pred))
        else:
            losses.append(-math.log(1 - pred))
    
    return sum(losses) / len(losses)
