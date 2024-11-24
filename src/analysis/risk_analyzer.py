from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime

class RiskAnalyzer:
    def __init__(self):
        """Initialize RiskAnalyzer with risk assessment parameters"""
        self.volatility_weight = 0.3
        self.liquidity_weight = 0.25
        self.market_cap_weight = 0.2
        self.volume_stability_weight = 0.15
        self.correlation_weight = 0.1

    def calculate_risk_metrics(self, market_data: pd.DataFrame, 
                             order_book: Dict,
                             volume_profile: Dict) -> Dict:
        """
        Calculate comprehensive risk metrics for a trading pair
        Args:
            market_data: OHLCV DataFrame
            order_book: Order book analysis results
            volume_profile: Volume profile analysis results
        Returns:
            Dictionary containing risk metrics
        """
        try:
            risk_metrics = {
                'volatility_risk': self._calculate_volatility_risk(market_data),
                'liquidity_risk': self._calculate_liquidity_risk(order_book),
                'volume_stability': self._calculate_volume_stability(market_data),
                'price_stability': self._calculate_price_stability(market_data),
                'market_depth': self._analyze_market_depth(order_book),
                'support_resistance_strength': self._calculate_sr_strength(volume_profile)
            }

            # Calculate overall risk score (0-100, lower is better)
            risk_score = (
                risk_metrics['volatility_risk'] * self.volatility_weight +
                risk_metrics['liquidity_risk'] * self.liquidity_weight +
                (1 - risk_metrics['volume_stability']) * self.volume_stability_weight +
                (1 - risk_metrics['market_depth']['strength']) * self.market_cap_weight
            ) * 100

            risk_metrics['overall_risk_score'] = min(max(risk_score, 0), 100)
            risk_metrics['risk_level'] = self._classify_risk_level(risk_metrics['overall_risk_score'])
            
            return risk_metrics
        except Exception as e:
            print(f"Error calculating risk metrics: {str(e)}")
            return None

    def _calculate_volatility_risk(self, data: pd.DataFrame) -> float:
        """Calculate volatility-based risk using ATR and standard deviation"""
        try:
            # Calculate daily returns
            returns = data['close'].pct_change().dropna()
            
            # Calculate ATR-based volatility
            high_low = data['high'] - data['low']
            high_close = abs(data['high'] - data['close'].shift())
            low_close = abs(data['low'] - data['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            atr = true_range.rolling(window=14).mean().iloc[-1]
            
            # Combine with standard deviation of returns
            volatility = np.std(returns) * np.sqrt(252)  # Annualized volatility
            
            # Normalize and combine metrics
            normalized_atr = min(atr / data['close'].iloc[-1], 1)
            normalized_vol = min(volatility, 1)
            
            return (normalized_atr + normalized_vol) / 2
        except Exception as e:
            print(f"Error calculating volatility risk: {str(e)}")
            return 1.0

    def _calculate_liquidity_risk(self, order_book: Dict) -> float:
        """Calculate liquidity risk based on order book metrics"""
        try:
            if not order_book:
                return 1.0

            # Calculate bid-ask spread risk
            spread_risk = min(order_book['spread_percentage'] / 100, 1)
            
            # Calculate depth risk
            total_liquidity = order_book['bid_volume'] + order_book['ask_volume']
            depth_risk = 1 / (1 + total_liquidity / 1000000)  # Normalize based on $1M depth
            
            # Calculate imbalance risk
            imbalance = abs(0.5 - (order_book['bid_volume'] / total_liquidity if total_liquidity > 0 else 0.5))
            
            # Combine risks (weighted average)
            liquidity_risk = (
                spread_risk * 0.4 +
                depth_risk * 0.4 +
                imbalance * 0.2
            )
            
            return min(max(liquidity_risk, 0), 1)
        except Exception as e:
            print(f"Error calculating liquidity risk: {str(e)}")
            return 1.0

    def _calculate_volume_stability(self, data: pd.DataFrame) -> float:
        """Calculate volume stability score"""
        try:
            # Calculate volume moving average
            volume_sma = data['volume'].rolling(window=20).mean()
            
            # Calculate volume volatility
            volume_volatility = data['volume'].rolling(window=20).std() / volume_sma
            
            # Calculate stability score (inverse of volatility)
            stability = 1 / (1 + volume_volatility.mean())
            
            return min(max(stability, 0), 1)
        except Exception as e:
            print(f"Error calculating volume stability: {str(e)}")
            return 0.0

    def _calculate_price_stability(self, data: pd.DataFrame) -> Dict:
        """Calculate price stability metrics"""
        try:
            # Calculate price moving averages
            sma_20 = data['close'].rolling(window=20).mean()
            sma_50 = data['close'].rolling(window=50).mean()
            
            # Calculate price deviation from moving averages
            deviation_20 = abs(data['close'] - sma_20) / sma_20
            deviation_50 = abs(data['close'] - sma_50) / sma_50
            
            # Calculate stability scores
            short_term_stability = 1 / (1 + deviation_20.mean())
            long_term_stability = 1 / (1 + deviation_50.mean())
            
            return {
                'short_term': float(short_term_stability),
                'long_term': float(long_term_stability),
                'overall': float((short_term_stability + long_term_stability) / 2)
            }
        except Exception as e:
            print(f"Error calculating price stability: {str(e)}")
            return {'short_term': 0.0, 'long_term': 0.0, 'overall': 0.0}

    def _analyze_market_depth(self, order_book: Dict) -> Dict:
        """Analyze market depth and liquidity distribution"""
        try:
            if not order_book:
                return {'strength': 0.0, 'balance': 0.0}

            # Calculate total depth
            total_depth = order_book['bid_volume'] + order_book['ask_volume']
            
            # Calculate depth distribution
            depth_balance = min(
                order_book['bid_volume'],
                order_book['ask_volume']
            ) / (total_depth / 2) if total_depth > 0 else 0
            
            # Calculate wall strength
            bid_walls = sum(wall['quantity'] for wall in order_book['bid_walls'])
            ask_walls = sum(wall['quantity'] for wall in order_book['ask_walls'])
            wall_strength = (bid_walls + ask_walls) / total_depth if total_depth > 0 else 0
            
            # Combine metrics
            depth_strength = 1 / (1 + np.exp(-total_depth / 1000000))  # Sigmoid normalization
            
            return {
                'strength': float(depth_strength),
                'balance': float(depth_balance),
                'wall_strength': float(wall_strength)
            }
        except Exception as e:
            print(f"Error analyzing market depth: {str(e)}")
            return {'strength': 0.0, 'balance': 0.0, 'wall_strength': 0.0}

    def _calculate_sr_strength(self, volume_profile: Dict) -> Dict:
        """Calculate strength of support and resistance levels"""
        try:
            if not volume_profile:
                return {'support_strength': 0.0, 'resistance_strength': 0.0}

            # Calculate relative volume at value area
            total_volume = volume_profile.get('total_volume', 0)
            if total_volume == 0:
                return {'support_strength': 0.0, 'resistance_strength': 0.0}

            # Calculate volume concentration at support/resistance
            value_area_volume = sum(
                vol for vol, price in zip(
                    volume_profile.get('volume_profile', []),
                    volume_profile.get('price_levels', [])
                )
                if volume_profile['value_area_low'] <= price <= volume_profile['value_area_high']
            )
            
            value_area_strength = value_area_volume / total_volume if total_volume > 0 else 0
            
            return {
                'support_strength': float(value_area_strength),
                'resistance_strength': float(value_area_strength),
                'overall_strength': float(value_area_strength)
            }
        except Exception as e:
            print(f"Error calculating S/R strength: {str(e)}")
            return {'support_strength': 0.0, 'resistance_strength': 0.0, 'overall_strength': 0.0}

    def _classify_risk_level(self, risk_score: float) -> str:
        """Classify risk level based on risk score"""
        if risk_score < 20:
            return 'Very Low'
        elif risk_score < 40:
            return 'Low'
        elif risk_score < 60:
            return 'Moderate'
        elif risk_score < 80:
            return 'High'
        else:
            return 'Very High'

    def compare_trading_pairs(self, pairs_analysis: Dict[str, Dict]) -> List[Dict]:
        """
        Compare risk metrics across multiple trading pairs
        Args:
            pairs_analysis: Dictionary of analysis results for multiple pairs
        Returns:
            List of pairs sorted by risk (lowest to highest)
        """
        try:
            pair_risks = []
            
            for symbol, analysis in pairs_analysis.items():
                if 'risk_metrics' in analysis:
                    metrics = analysis['risk_metrics']
                    pair_risks.append({
                        'symbol': symbol,
                        'risk_score': metrics['overall_risk_score'],
                        'risk_level': metrics['risk_level'],
                        'volatility_risk': metrics['volatility_risk'],
                        'liquidity_risk': metrics['liquidity_risk'],
                        'volume_stability': metrics['volume_stability'],
                        'market_depth': metrics['market_depth']['strength']
                    })
            
            # Sort by risk score (ascending)
            return sorted(pair_risks, key=lambda x: x['risk_score'])
        except Exception as e:
            print(f"Error comparing trading pairs: {str(e)}")
            return []
