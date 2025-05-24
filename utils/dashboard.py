"""
Performance Dashboard
Real-time monitoring of the swarm trading system
"""

import asyncio
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import Dict, List
import numpy as np

class PerformanceDashboard:
    """
    Tracks and visualizes:
    - Capital growth curve
    - Win rate by strategy
    - Agent performance metrics
    - Risk metrics
    """
    
    def __init__(self):
        self.metrics = {
            "capital_history": [],
            "trades": [],
            "agent_performance": {},
            "strategy_performance": {},
            "risk_metrics": []
        }
        
    def update_capital(self, capital: float, timestamp: datetime):
        """Update capital tracking"""
        self.metrics["capital_history"].append({
            "timestamp": timestamp.isoformat(),
            "capital": capital,
            "phase": self._get_phase(capital)
        })
        
    def _get_phase(self, capital: float) -> str:
        """Determine current phase based on capital"""
        if capital < 1000:
            return "MICRO"
        elif capital < 10000:
            return "GROWTH"
        else:
            return "SCALE"
            
    def record_trade(self, trade: Dict):
        """Record trade details"""
        self.metrics["trades"].append({
            "timestamp": datetime.now().isoformat(),
            "strategy": trade["strategy"],
            "profit": trade["profit"],
            "agent": trade["agent"],
            "phase": self._get_phase(trade["capital_before"])
        })