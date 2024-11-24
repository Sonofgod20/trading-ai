from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime
import traceback
import sys

from .indicators.technical_indicators import TechnicalIndicators
from .patterns.candlestick_patterns import CandlestickPatterns
from .market_data.market_analyzer import MarketAnalyzer
from .risk_analyzer import RiskAnalyzer

class TradingAnalyzer:
    def __init__(self, binance_client):
        """
        Initialize TradingAnalyzer with all analysis components
        Args:
            binance_client: Instance of BinanceFuturesClient
        """
        try:
            self.market_analyzer = MarketAnalyzer(binance_client)
            self.indicators = TechnicalIndicators()
            self.patterns = CandlestickPatterns()
            self.risk_analyzer = RiskAnalyzer()
            self.client = binance_client
            print("TradingAnalyzer initialized successfully")
        except Exception as e:
            print(f"Error initializing TradingAnalyzer: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            raise

    def analyze_multiple_pairs(self, symbols: List[str], 
                             timeframes: Optional[List[str]] = None) -> Dict[str, Dict]:
        """
        Analyze multiple trading pairs and compare their risk profiles
        Args:
            symbols: List of trading pair symbols
            timeframes: List of timeframes to analyze
        Returns:
            Dictionary containing analysis for each pair
        """
        pairs_analysis = {}
        
        try:
            for symbol in symbols:
                print(f"\nAnalyzing {symbol}...")
                analysis = self.perform_complete_analysis(symbol, timeframes)
                if analysis:
                    pairs_analysis[symbol] = analysis
            
            # Compare pairs and rank by risk
            if pairs_analysis:
                ranked_pairs = self.risk_analyzer.compare_trading_pairs(pairs_analysis)
                return {
                    'pairs_analysis': pairs_analysis,
                    'ranked_pairs': ranked_pairs
                }
            return None
        except Exception as e:
            print(f"Error analyzing multiple pairs: {str(e)}")
            return None

    def perform_complete_analysis(self, symbol: str, 
                                timeframes: Optional[List[str]] = None) -> Dict:
        """
        Perform comprehensive market analysis across multiple timeframes
        Args:
            symbol: Trading pair symbol
            timeframes: List of timeframes to analyze
        Returns:
            Dictionary containing complete analysis
        """
        if timeframes is None:
            timeframes = ['15m', '1h', '4h', '1d']

        analysis = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'timeframes': {},
            'market_sentiment': None,
            'order_book_analysis': None,
            'volume_profile': None,
            'trade_signals': None,
            'risk_metrics': None
        }

        try:
            print(f"\nStarting analysis for {symbol}")
            print(f"Timeframes: {timeframes}")
            
            # Get market data for all timeframes
            market_data = {}
            for tf in timeframes:
                print(f"\nFetching {tf} timeframe data...")
                data = self.client.get_market_data(symbol, tf)
                if data is not None and not data.empty:
                    print(f"Received data for {tf}: {len(data)} rows")
                    market_data[tf] = data
                else:
                    print(f"Warning: No data received for {tf} timeframe")
            
            if not market_data:
                raise ValueError(f"No market data available for {symbol} on any timeframe")
            
            # Analyze each timeframe
            print("\nAnalyzing timeframes...")
            for tf, data in market_data.items():
                print(f"Processing {tf} timeframe...")
                tf_analysis = self._analyze_timeframe(data)
                if tf_analysis:
                    analysis['timeframes'][tf] = tf_analysis
                    print(f"Analysis completed for {tf}")
                else:
                    print(f"Warning: Analysis failed for {tf}")
            
            if not analysis['timeframes']:
                raise ValueError("No timeframe analysis available")
            
            # Get market sentiment
            print("\nCalculating market sentiment...")
            analysis['market_sentiment'] = self.market_analyzer.get_market_sentiment(symbol)
            if not analysis['market_sentiment']:
                print("Warning: Market sentiment analysis failed")
            
            # Get order book analysis
            print("\nAnalyzing order book...")
            analysis['order_book_analysis'] = self.market_analyzer.analyze_order_book_depth(symbol)
            if not analysis['order_book_analysis']:
                print("Warning: Order book analysis failed")
            
            # Get volume profile
            print("\nCalculating volume profile...")
            analysis['volume_profile'] = self.market_analyzer.analyze_volume_profile(symbol)
            if not analysis['volume_profile']:
                print("Warning: Volume profile analysis failed")
            
            # Calculate risk metrics
            print("\nCalculating risk metrics...")
            if '1d' in market_data:
                risk_metrics = self.risk_analyzer.calculate_risk_metrics(
                    market_data['1d'],
                    analysis['order_book_analysis'],
                    analysis['volume_profile'].get('1d', {})
                )
                if risk_metrics:
                    analysis['risk_metrics'] = risk_metrics
                    print(f"Risk analysis completed. Score: {risk_metrics['overall_risk_score']:.2f}")
                else:
                    print("Warning: Risk analysis failed")
            
            # Add trade signals
            print("\nGenerating trade signals...")
            analysis['trade_signals'] = self._generate_trade_signals(analysis)
            if not analysis['trade_signals']:
                print("Warning: Trade signal generation failed")
            
            print("\nAnalysis completed successfully")
            return analysis
        
        except Exception as e:
            print(f"\nError in perform_complete_analysis: {str(e)}")
            print(f"Python version: {sys.version}")
            print(f"Traceback: {traceback.format_exc()}")
            
            # Return partial analysis if available
            if analysis['timeframes']:
                print("Returning partial analysis")
                return analysis
            return None

    def _analyze_timeframe(self, data: pd.DataFrame) -> Dict:
        """
        Analyze single timeframe data
        Args:
            data: OHLC DataFrame
        Returns:
            Dictionary containing timeframe analysis
        """
        try:
            if data is None or data.empty:
                raise ValueError("No data provided for timeframe analysis")

            # Clean and prepare close price data
            close_prices = pd.to_numeric(data['close'], errors='coerce')
            close_prices = close_prices.replace([np.inf, -np.inf], np.nan)
            close_prices = close_prices.fillna(method='ffill')
            if close_prices.isna().any():
                close_prices = close_prices.fillna(close_prices.mean())

            print("Calculating EMAs...")
            emas = self.indicators.calculate_ema(close_prices, [9, 20, 50, 200])
            
            print("Calculating RSI...")
            rsi_analysis = self.indicators.calculate_advanced_rsi(close_prices)
            
            print("Calculating support/resistance levels...")
            support_resistance = self.indicators.calculate_support_resistance(data)
            
            print("Identifying candlestick patterns...")
            patterns = self.patterns.scan_all_patterns(data)
            
            print("Calculating volume profile...")
            volume_analysis = self.indicators.calculate_volume_profile(data)
            
            return {
                'technical_indicators': {
                    'emas': {k: float(v.iloc[-1]) for k, v in emas.items()},
                    'rsi': {
                        'value': float(rsi_analysis['RSI'].iloc[-1]),
                        'signal': float(rsi_analysis['signals'].iloc[-1]),
                        'bearish_divergence': bool(rsi_analysis['bearish_divergence'].iloc[-1]),
                        'bullish_divergence': bool(rsi_analysis['bullish_divergence'].iloc[-1])
                    }
                },
                'support_resistance': support_resistance,
                'patterns': {k: float(v.iloc[-1]) for k, v in patterns.items()},
                'volume_analysis': {
                    'poc': float(volume_analysis['poc']),
                    'value_area_high': float(volume_analysis['value_area_high']),
                    'value_area_low': float(volume_analysis['value_area_low'])
                }
            }
        except Exception as e:
            print(f"Error in _analyze_timeframe: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return None

    def _generate_trade_signals(self, analysis: Dict) -> Dict:
        """
        Generate trading signals based on complete analysis
        Args:
            analysis: Complete analysis dictionary
        Returns:
            Dictionary containing trade signals and recommendations
        """
        signals = {
            'overall_sentiment': None,
            'confidence_score': 0.0,
            'recommended_direction': None,
            'entry_zone': None,
            'stop_loss': None,
            'take_profit': None,
            'timeframe_signals': {},
            'risk_adjusted_size': None
        }

        try:
            if not analysis.get('market_sentiment'):
                print("Warning: No market sentiment data available")
                return signals

            signals['overall_sentiment'] = analysis['market_sentiment']['sentiment']
            
            # Analyze signals from each timeframe
            print("\nAnalyzing signals for each timeframe...")
            for tf, tf_analysis in analysis['timeframes'].items():
                print(f"Processing {tf} timeframe signals...")
                tf_signals = self._analyze_timeframe_signals(tf_analysis)
                if tf_signals:
                    signals['timeframe_signals'][tf] = tf_signals
                    print(f"Signals generated for {tf}")
                else:
                    print(f"Warning: Signal generation failed for {tf}")
            
            if not signals['timeframe_signals']:
                print("Warning: No timeframe signals generated")
                return signals
            
            # Calculate overall signal
            bullish_signals = 0
            bearish_signals = 0
            total_signals = 0
            
            for tf, tf_signals in signals['timeframe_signals'].items():
                weight = 1.0 if tf == '1d' else 0.5 if tf == '4h' else 0.25
                if tf_signals['signal'] == 'buy':
                    bullish_signals += weight
                elif tf_signals['signal'] == 'sell':
                    bearish_signals += weight
                total_signals += weight
            
            # Calculate confidence and direction
            if total_signals > 0:
                bull_ratio = bullish_signals / total_signals
                bear_ratio = bearish_signals / total_signals
                
                if bull_ratio > 0.6:
                    signals['recommended_direction'] = 'long'
                    signals['confidence_score'] = bull_ratio * 100
                elif bear_ratio > 0.6:
                    signals['recommended_direction'] = 'short'
                    signals['confidence_score'] = bear_ratio * 100
            
            # Adjust confidence based on risk metrics
            if analysis.get('risk_metrics'):
                risk_score = analysis['risk_metrics']['overall_risk_score']
                # Reduce confidence as risk increases
                signals['confidence_score'] *= (1 - (risk_score / 200))  # Risk adjustment factor
                
                # Calculate risk-adjusted position size
                max_position = 1.0  # 100% of available capital
                risk_factor = 1 - (risk_score / 100)  # Higher risk = lower size
                signals['risk_adjusted_size'] = max_position * risk_factor
            
            # Set entry, stop loss, and take profit zones
            if signals['recommended_direction'] and analysis.get('order_book_analysis'):
                order_book = analysis['order_book_analysis']
                current_price = float(order_book['mid_price'])
                
                if signals['recommended_direction'] == 'long':
                    # For long positions
                    support_levels = []
                    resistance_levels = []
                    
                    for tf_analysis in analysis['timeframes'].values():
                        if tf_analysis and 'support_resistance' in tf_analysis:
                            sr_levels = tf_analysis['support_resistance']
                            support_levels.extend([level for level in sr_levels['support']
                                               if level < current_price])
                            resistance_levels.extend([level for level in sr_levels['resistance']
                                                  if level > current_price])
                    
                    if support_levels and resistance_levels:
                        signals['entry_zone'] = current_price
                        signals['stop_loss'] = max(support_levels) * 0.995  # Just below support
                        signals['take_profit'] = min(resistance_levels) * 1.005  # Just above resistance
                
                else:  # Short position
                    support_levels = []
                    resistance_levels = []
                    
                    for tf_analysis in analysis['timeframes'].values():
                        if tf_analysis and 'support_resistance' in tf_analysis:
                            sr_levels = tf_analysis['support_resistance']
                            support_levels.extend([level for level in sr_levels['support']
                                               if level < current_price])
                            resistance_levels.extend([level for level in sr_levels['resistance']
                                                  if level > current_price])
                    
                    if support_levels and resistance_levels:
                        signals['entry_zone'] = current_price
                        signals['stop_loss'] = min(resistance_levels) * 1.005  # Just above resistance
                        signals['take_profit'] = max(support_levels) * 0.995  # Just below support
            
            return signals
        
        except Exception as e:
            print(f"Error in _generate_trade_signals: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return signals

    def _analyze_timeframe_signals(self, tf_analysis: Dict) -> Dict:
        """
        Analyze signals for a single timeframe
        Args:
            tf_analysis: Timeframe analysis dictionary
        Returns:
            Dictionary containing timeframe signals
        """
        signals = {
            'signal': None,  # 'buy', 'sell', or None
            'strength': 0,   # 0 to 100
            'reasons': []
        }
        
        try:
            if not tf_analysis:
                print("Warning: No timeframe analysis data provided")
                return signals

            if not tf_analysis.get('technical_indicators'):
                print("Warning: No technical indicators available for timeframe")
                return signals

            # Check EMA trends
            emas = tf_analysis['technical_indicators']['emas']
            if emas:
                ema_9 = emas.get('EMA_9', 0)
                ema_20 = emas.get('EMA_20', 0)
                ema_50 = emas.get('EMA_50', 0)
                
                # Check RSI
                rsi = tf_analysis['technical_indicators']['rsi']
                
                # Initialize signal strength
                bullish_points = 0
                bearish_points = 0
                
                # EMA Analysis
                if ema_9 and ema_20 and ema_50:
                    if ema_9 > ema_20 > ema_50:
                        bullish_points += 30
                        signals['reasons'].append("Bullish EMA alignment")
                    elif ema_9 < ema_20 < ema_50:
                        bearish_points += 30
                        signals['reasons'].append("Bearish EMA alignment")
                
                # RSI Analysis
                if rsi:
                    if rsi['value'] < 30 and rsi['bullish_divergence']:
                        bullish_points += 25
                        signals['reasons'].append("RSI oversold with bullish divergence")
                    elif rsi['value'] > 70 and rsi['bearish_divergence']:
                        bearish_points += 25
                        signals['reasons'].append("RSI overbought with bearish divergence")
                
                # Pattern Analysis
                for pattern, value in tf_analysis.get('patterns', {}).items():
                    if value == 1:  # Bullish pattern
                        bullish_points += 15
                        signals['reasons'].append(f"Bullish {pattern} pattern")
                    elif value == -1:  # Bearish pattern
                        bearish_points += 15
                        signals['reasons'].append(f"Bearish {pattern} pattern")
                
                # Determine final signal
                if bullish_points > bearish_points and bullish_points >= 30:
                    signals['signal'] = 'buy'
                    signals['strength'] = bullish_points
                elif bearish_points > bullish_points and bearish_points >= 30:
                    signals['signal'] = 'sell'
                    signals['strength'] = bearish_points
            
            return signals
        
        except Exception as e:
            print(f"Error in _analyze_timeframe_signals: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return signals
