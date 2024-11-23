import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

class HistoricalAnalyzer:
    # Constants
    MIN_DATA_POINTS = 50  # Minimum number of data points required for analysis
    MIN_PREDICTION_POINTS = 24  # Minimum points needed for prediction validation
    
    def __init__(self):
        self.predictions = []
        self.actual_results = []
        
    def analyze_historical_data(self, market_data: pd.DataFrame, 
                              analysis_results: Dict,
                              start_date: datetime,
                              end_date: datetime) -> Dict:
        """
        Analyze historical data and compare AI predictions with actual outcomes
        
        Args:
            market_data: DataFrame with historical market data
            analysis_results: Current AI analysis results
            start_date: Start date for analysis
            end_date: End date for analysis
        """
        results = {
            'predictions': [],
            'accuracy_metrics': {
                'overall_accuracy': 0,
                'long_accuracy': 0,
                'short_accuracy': 0,
                'high_confidence_accuracy': 0,
                'low_confidence_accuracy': 0
            },
            'roi_metrics': {
                'total_roi': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0
            },
            'detailed_analysis': [],
            'error_analysis': {
                'high_volatility_fails': 0,
                'trend_misalignment': 0,
                'false_breakouts': 0,
                'stop_loss_hits': 0
            }
        }
        
        try:
            # Validate input data
            if market_data is None or market_data.empty:
                raise ValueError("No market data provided")
                
            if not isinstance(market_data.index, pd.DatetimeIndex):
                market_data.index = pd.to_datetime(market_data.index)
            
            # Ensure dates are pandas Timestamp objects
            start_ts = pd.Timestamp(start_date)
            end_ts = pd.Timestamp(end_date)
            
            # Filter data for date range
            period_data = market_data.loc[start_ts:end_ts].copy()
            
            # Validate data points
            if len(period_data) < self.MIN_DATA_POINTS:
                raise ValueError(f"Insufficient data points in selected date range. Minimum required: {self.MIN_DATA_POINTS}, Got: {len(period_data)}")
            
            # Clean data
            period_data = self._clean_market_data(period_data)
            
            # Generate predictions for each point
            valid_predictions = 0
            for i in range(len(period_data)):
                # Ensure we have enough future data for validation
                if i + self.MIN_PREDICTION_POINTS > len(period_data):
                    break
                    
                historical_slice = period_data.iloc[:i]
                if len(historical_slice) < self.MIN_DATA_POINTS:
                    continue
                    
                # Generate prediction
                prediction = self._generate_prediction(historical_slice, analysis_results)
                
                # Get actual outcome
                actual = self._get_actual_outcome(period_data, i)
                
                if prediction and actual:
                    results['predictions'].append({
                        'timestamp': period_data.index[i],
                        'predicted': prediction,
                        'actual': actual,
                        'success': self._evaluate_prediction(prediction, actual)
                    })
                    valid_predictions += 1
            
            if valid_predictions < 1:
                raise ValueError(f"No valid predictions could be generated. Need at least {self.MIN_PREDICTION_POINTS} future data points for validation.")
            
            # Calculate metrics
            if results['predictions']:
                results['accuracy_metrics'] = self._calculate_accuracy_metrics(results['predictions'])
                results['roi_metrics'] = self._calculate_roi_metrics(results['predictions'])
                results['detailed_analysis'] = self._generate_detailed_analysis(results)
                results['error_analysis'] = self._analyze_errors(results['predictions'])
            
            return results
            
        except Exception as e:
            print(f"Error in historical analysis: {str(e)}")
            return results

    def _clean_market_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate market data"""
        try:
            # Convert price columns to numeric
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in data.columns:
                    data[col] = pd.to_numeric(data[col], errors='coerce')
            
            # Handle missing values
            data = data.fillna(method='ffill').fillna(method='bfill')
            
            # Remove any remaining invalid data
            data = data.replace([np.inf, -np.inf], np.nan).dropna()
            
            return data
        except Exception as e:
            print(f"Error cleaning market data: {str(e)}")
            return data
            
    def _generate_prediction(self, data: pd.DataFrame, analysis_results: Dict) -> Dict:
        """Generate a prediction for a specific point in time"""
        try:
            if len(data) < self.MIN_DATA_POINTS:
                return None
                
            # Apply current AI analysis logic to historical data point
            prediction = {
                'direction': 'long' if analysis_results.get('trade_signals', {}).get('direction') == 'long' else 'short',
                'confidence': float(analysis_results.get('trade_signals', {}).get('confidence', 0)),
                'price_levels': {
                    'entry': float(data['close'].iloc[-1]),
                    'tp': float(data['close'].iloc[-1]) * (1.02 if analysis_results.get('trade_signals', {}).get('direction') == 'long' else 0.98),
                    'sl': float(data['close'].iloc[-1]) * (0.99 if analysis_results.get('trade_signals', {}).get('direction') == 'long' else 1.01)
                },
                'market_conditions': self._analyze_market_conditions(data)
            }
            return prediction
        except Exception as e:
            print(f"Error generating prediction: {str(e)}")
            return None
            
    def _get_actual_outcome(self, data: pd.DataFrame, index: int) -> Dict:
        """Get the actual market outcome after a prediction"""
        try:
            future_data = data.iloc[index:index + self.MIN_PREDICTION_POINTS]
            if len(future_data) < self.MIN_PREDICTION_POINTS:
                return None
                
            return {
                'high': float(future_data['high'].max()),
                'low': float(future_data['low'].min()),
                'close': float(future_data['close'].iloc[-1]),
                'trend': self._calculate_trend(future_data)
            }
        except Exception as e:
            print(f"Error getting actual outcome: {str(e)}")
            return None
            
    def _evaluate_prediction(self, prediction: Dict, actual: Dict) -> bool:
        """Evaluate if a prediction was successful"""
        try:
            if prediction['direction'] == 'long':
                return float(actual['high']) >= float(prediction['price_levels']['tp']) and \
                       float(actual['low']) >= float(prediction['price_levels']['sl'])
            else:
                return float(actual['low']) <= float(prediction['price_levels']['tp']) and \
                       float(actual['high']) <= float(prediction['price_levels']['sl'])
        except Exception as e:
            print(f"Error evaluating prediction: {str(e)}")
            return False
            
    def _calculate_accuracy_metrics(self, predictions: List[Dict]) -> Dict:
        """Calculate accuracy metrics for predictions"""
        try:
            if not predictions:
                return {
                    'overall_accuracy': 0,
                    'long_accuracy': 0,
                    'short_accuracy': 0,
                    'high_confidence_accuracy': 0,
                    'low_confidence_accuracy': 0
                }
                
            successful = len([p for p in predictions if p['success']])
            long_predictions = [p for p in predictions if p['predicted']['direction'] == 'long']
            short_predictions = [p for p in predictions if p['predicted']['direction'] == 'short']
            
            successful_long = len([p for p in long_predictions if p['success']])
            successful_short = len([p for p in short_predictions if p['success']])
            
            # Analyze confidence levels
            high_confidence = [p for p in predictions if p['predicted']['confidence'] >= 75]
            low_confidence = [p for p in predictions if p['predicted']['confidence'] < 75]
            
            successful_high_conf = len([p for p in high_confidence if p['success']])
            successful_low_conf = len([p for p in low_confidence if p['success']])
            
            return {
                'overall_accuracy': (successful / len(predictions)) * 100 if predictions else 0,
                'long_accuracy': (successful_long / len(long_predictions)) * 100 if long_predictions else 0,
                'short_accuracy': (successful_short / len(short_predictions)) * 100 if short_predictions else 0,
                'high_confidence_accuracy': (successful_high_conf / len(high_confidence)) * 100 if high_confidence else 0,
                'low_confidence_accuracy': (successful_low_conf / len(low_confidence)) * 100 if low_confidence else 0
            }
        except Exception as e:
            print(f"Error calculating accuracy metrics: {str(e)}")
            return {
                'overall_accuracy': 0,
                'long_accuracy': 0,
                'short_accuracy': 0,
                'high_confidence_accuracy': 0,
                'low_confidence_accuracy': 0
            }
            
    def _calculate_roi_metrics(self, predictions: List[Dict]) -> Dict:
        """Calculate ROI metrics for predictions"""
        try:
            if not predictions:
                return {
                    'total_roi': 0,
                    'avg_win': 0,
                    'avg_loss': 0,
                    'profit_factor': 0
                }
                
            wins = []
            losses = []
            
            for pred in predictions:
                if pred['success']:
                    roi = ((pred['predicted']['price_levels']['tp'] - pred['predicted']['price_levels']['entry']) / 
                           pred['predicted']['price_levels']['entry']) * 100
                    wins.append(roi)
                else:
                    roi = ((pred['predicted']['price_levels']['sl'] - pred['predicted']['price_levels']['entry']) / 
                           pred['predicted']['price_levels']['entry']) * 100
                    losses.append(roi)
                    
            total_wins = sum(wins) if wins else 0
            total_losses = abs(sum(losses)) if losses else 0
            profit_factor = total_wins / total_losses if total_losses > 0 else 0
                    
            return {
                'total_roi': total_wins + (total_losses * -1),
                'avg_win': np.mean(wins) if wins else 0,
                'avg_loss': np.mean(losses) if losses else 0,
                'profit_factor': profit_factor
            }
        except Exception as e:
            print(f"Error calculating ROI metrics: {str(e)}")
            return {
                'total_roi': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0
            }
            
    def _analyze_market_conditions(self, data: pd.DataFrame) -> Dict:
        """Analyze market conditions"""
        try:
            if len(data) < 2:
                return {
                    'volatility': 0,
                    'trend': 'unknown',
                    'volume_profile': 'normal'
                }
                
            returns = data['close'].pct_change()
            volatility = returns.std() * np.sqrt(252)  # Annualized volatility
            
            return {
                'volatility': volatility,
                'trend': self._calculate_trend(data),
                'volume_profile': 'high' if data['volume'].iloc[-1] > data['volume'].mean() else 'low'
            }
        except Exception as e:
            print(f"Error analyzing market conditions: {str(e)}")
            return {
                'volatility': 0,
                'trend': 'unknown',
                'volume_profile': 'normal'
            }
            
    def _calculate_trend(self, data: pd.DataFrame) -> str:
        """Calculate market trend"""
        try:
            if len(data) < 50:  # Need enough data for reliable trend calculation
                return 'unknown'
                
            sma20 = data['close'].rolling(window=20).mean()
            sma50 = data['close'].rolling(window=50).mean()
            
            if sma20.iloc[-1] > sma50.iloc[-1]:
                return 'uptrend'
            elif sma20.iloc[-1] < sma50.iloc[-1]:
                return 'downtrend'
            else:
                return 'sideways'
        except Exception as e:
            print(f"Error calculating trend: {str(e)}")
            return 'unknown'
            
    def _analyze_errors(self, predictions: List[Dict]) -> Dict:
        """Analyze prediction errors to identify patterns"""
        try:
            if not predictions:
                return {
                    'high_volatility_fails': 0,
                    'trend_misalignment': 0,
                    'false_breakouts': 0,
                    'stop_loss_hits': 0
                }

            failed_predictions = [p for p in predictions if not p['success']]
            total_fails = len(failed_predictions)
            
            if total_fails == 0:
                return {
                    'high_volatility_fails': 0,
                    'trend_misalignment': 0,
                    'false_breakouts': 0,
                    'stop_loss_hits': 0
                }
            
            error_patterns = {
                'high_volatility_fails': 0,
                'trend_misalignment': 0,
                'false_breakouts': 0,
                'stop_loss_hits': 0
            }
            
            for pred in failed_predictions:
                # Check volatility related failures
                if pred['predicted']['market_conditions']['volatility'] > 0.5:  # High volatility threshold
                    error_patterns['high_volatility_fails'] += 1
                    
                # Check trend misalignment
                if pred['predicted']['direction'] == 'long' and pred['actual']['trend'] == 'downtrend':
                    error_patterns['trend_misalignment'] += 1
                elif pred['predicted']['direction'] == 'short' and pred['actual']['trend'] == 'uptrend':
                    error_patterns['trend_misalignment'] += 1
                    
                # Check false breakouts
                if abs(pred['actual']['close'] - pred['predicted']['price_levels']['entry']) < \
                   abs(pred['predicted']['price_levels']['tp'] - pred['predicted']['price_levels']['entry']) * 0.1:
                    error_patterns['false_breakouts'] += 1
                    
                # Check stop loss hits
                if pred['predicted']['direction'] == 'long' and \
                   pred['actual']['low'] <= pred['predicted']['price_levels']['sl']:
                    error_patterns['stop_loss_hits'] += 1
                elif pred['predicted']['direction'] == 'short' and \
                     pred['actual']['high'] >= pred['predicted']['price_levels']['sl']:
                    error_patterns['stop_loss_hits'] += 1
                    
            # Calculate percentages
            for key in error_patterns:
                error_patterns[key] = (error_patterns[key] / total_fails) * 100
                    
            return error_patterns
        except Exception as e:
            print(f"Error analyzing errors: {str(e)}")
            return {
                'high_volatility_fails': 0,
                'trend_misalignment': 0,
                'false_breakouts': 0,
                'stop_loss_hits': 0
            }

    def _generate_detailed_analysis(self, results: Dict) -> List[Dict]:
        """Generate detailed analysis of predictions"""
        try:
            if not results.get('predictions'):
                return []

            detailed = []
            for pred in results['predictions']:
                analysis = {
                    'timestamp': pred['timestamp'],
                    'prediction': pred['predicted'],
                    'outcome': pred['actual'],
                    'success': pred['success'],
                    'confidence': pred['predicted']['confidence'],
                    'market_conditions': pred['predicted']['market_conditions']
                }
                detailed.append(analysis)
            return detailed
        except Exception as e:
            print(f"Error generating detailed analysis: {str(e)}")
            return []
