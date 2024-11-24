import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple

class CandlestickPatterns:
    @staticmethod
    def _body_length(open_price: float, close_price: float) -> float:
        """Calculate candle body length"""
        return abs(close_price - open_price)
    
    @staticmethod
    def _upper_shadow(open_price: float, close_price: float, high_price: float) -> float:
        """Calculate upper shadow length"""
        return high_price - max(open_price, close_price)
    
    @staticmethod
    def _lower_shadow(open_price: float, close_price: float, low_price: float) -> float:
        """Calculate lower shadow length"""
        return min(open_price, close_price) - low_price
    
    @staticmethod
    def _is_bullish(open_price: float, close_price: float) -> bool:
        """Check if candle is bullish"""
        return close_price > open_price
    
    @staticmethod
    def _is_bearish(open_price: float, close_price: float) -> bool:
        """Check if candle is bearish"""
        return close_price < open_price

    @classmethod
    def identify_doji(cls, data: pd.DataFrame, tolerance: float = 0.1) -> pd.Series:
        """
        Identify Doji patterns
        Args:
            data: OHLC DataFrame
            tolerance: Maximum body to shadow ratio for Doji
        Returns:
            Series with Doji signals (1 for Doji)
        """
        try:
            signals = pd.Series(0, index=data.index)
            
            for i in range(len(data)):
                try:
                    body = cls._body_length(data['open'].iloc[i], data['close'].iloc[i])
                    upper_shadow = cls._upper_shadow(data['open'].iloc[i], data['close'].iloc[i], data['high'].iloc[i])
                    lower_shadow = cls._lower_shadow(data['open'].iloc[i], data['close'].iloc[i], data['low'].iloc[i])
                    
                    # Check if body is very small compared to shadows
                    total_shadow = upper_shadow + lower_shadow
                    if total_shadow > 0 and body <= total_shadow * tolerance:
                        signals.iloc[i] = 1
                except Exception as e:
                    print(f"Error processing Doji at index {i}: {str(e)}")
                    continue
            
            return signals
        except Exception as e:
            print(f"Error identifying Doji patterns: {str(e)}")
            return pd.Series(0, index=data.index)

    @classmethod
    def identify_hammer(cls, data: pd.DataFrame, body_ratio: float = 0.3, 
                       shadow_ratio: float = 2.0) -> pd.Series:
        """
        Identify Hammer patterns
        Args:
            data: OHLC DataFrame
            body_ratio: Maximum ratio of body to total length
            shadow_ratio: Minimum ratio of lower shadow to body
        Returns:
            Series with Hammer signals (1 for hammer)
        """
        try:
            signals = pd.Series(0, index=data.index)
            
            for i in range(len(data)):
                try:
                    body = cls._body_length(data['open'].iloc[i], data['close'].iloc[i])
                    upper_shadow = cls._upper_shadow(data['open'].iloc[i], data['close'].iloc[i], data['high'].iloc[i])
                    lower_shadow = cls._lower_shadow(data['open'].iloc[i], data['close'].iloc[i], data['low'].iloc[i])
                    total_length = upper_shadow + body + lower_shadow
                    
                    if total_length > 0:  # Prevent division by zero
                        # Check hammer criteria
                        if (body / total_length <= body_ratio and 
                            lower_shadow >= body * shadow_ratio and 
                            upper_shadow <= body * 0.1):
                            signals.iloc[i] = 1
                except Exception as e:
                    print(f"Error processing Hammer at index {i}: {str(e)}")
                    continue
            
            return signals
        except Exception as e:
            print(f"Error identifying Hammer patterns: {str(e)}")
            return pd.Series(0, index=data.index)

    @classmethod
    def identify_engulfing(cls, data: pd.DataFrame) -> pd.Series:
        """
        Identify Bullish and Bearish Engulfing patterns
        Args:
            data: OHLC DataFrame
        Returns:
            Series with Engulfing signals (1 for bullish, -1 for bearish)
        """
        try:
            signals = pd.Series(0, index=data.index)
            
            for i in range(1, len(data)):
                try:
                    prev_body = cls._body_length(data['open'].iloc[i-1], data['close'].iloc[i-1])
                    curr_body = cls._body_length(data['open'].iloc[i], data['close'].iloc[i])
                    
                    # Bullish Engulfing
                    if (cls._is_bearish(data['open'].iloc[i-1], data['close'].iloc[i-1]) and
                        cls._is_bullish(data['open'].iloc[i], data['close'].iloc[i]) and
                        data['open'].iloc[i] <= data['close'].iloc[i-1] and
                        data['close'].iloc[i] >= data['open'].iloc[i-1] and
                        curr_body > prev_body):
                        signals.iloc[i] = 1
                    
                    # Bearish Engulfing
                    elif (cls._is_bullish(data['open'].iloc[i-1], data['close'].iloc[i-1]) and
                          cls._is_bearish(data['open'].iloc[i], data['close'].iloc[i]) and
                          data['open'].iloc[i] >= data['close'].iloc[i-1] and
                          data['close'].iloc[i] <= data['open'].iloc[i-1] and
                          curr_body > prev_body):
                        signals.iloc[i] = -1
                except Exception as e:
                    print(f"Error processing Engulfing at index {i}: {str(e)}")
                    continue
            
            return signals
        except Exception as e:
            print(f"Error identifying Engulfing patterns: {str(e)}")
            return pd.Series(0, index=data.index)

    @classmethod
    def identify_morning_evening_star(cls, data: pd.DataFrame, 
                                    doji_tolerance: float = 0.1) -> pd.Series:
        """
        Identify Morning Star and Evening Star patterns
        Args:
            data: OHLC DataFrame
            doji_tolerance: Maximum body to shadow ratio for middle candle
        Returns:
            Series with Star signals (1 for morning star, -1 for evening star)
        """
        try:
            signals = pd.Series(0, index=data.index)
            
            for i in range(2, len(data)):
                try:
                    # Check middle candle for doji-like properties
                    middle_body = cls._body_length(data['open'].iloc[i-1], data['close'].iloc[i-1])
                    middle_shadows = (cls._upper_shadow(data['open'].iloc[i-1], data['close'].iloc[i-1], data['high'].iloc[i-1]) +
                                    cls._lower_shadow(data['open'].iloc[i-1], data['close'].iloc[i-1], data['low'].iloc[i-1]))
                    
                    is_small_body = middle_shadows > 0 and middle_body <= middle_shadows * doji_tolerance
                    
                    # Morning Star
                    if (cls._is_bearish(data['open'].iloc[i-2], data['close'].iloc[i-2]) and
                        is_small_body and
                        cls._is_bullish(data['open'].iloc[i], data['close'].iloc[i]) and
                        data['close'].iloc[i] > (data['open'].iloc[i-2] + data['close'].iloc[i-2]) / 2):
                        signals.iloc[i] = 1
                    
                    # Evening Star
                    elif (cls._is_bullish(data['open'].iloc[i-2], data['close'].iloc[i-2]) and
                          is_small_body and
                          cls._is_bearish(data['open'].iloc[i], data['close'].iloc[i]) and
                          data['close'].iloc[i] < (data['open'].iloc[i-2] + data['close'].iloc[i-2]) / 2):
                        signals.iloc[i] = -1
                except Exception as e:
                    print(f"Error processing Star pattern at index {i}: {str(e)}")
                    continue
            
            return signals
        except Exception as e:
            print(f"Error identifying Star patterns: {str(e)}")
            return pd.Series(0, index=data.index)

    @classmethod
    def identify_three_line_strike(cls, data: pd.DataFrame) -> pd.Series:
        """
        Identify Three Line Strike patterns
        Args:
            data: OHLC DataFrame
        Returns:
            Series with Three Line Strike signals (1 for bullish, -1 for bearish)
        """
        try:
            signals = pd.Series(0, index=data.index)
            
            for i in range(3, len(data)):
                try:
                    # Bullish Three Line Strike
                    if (cls._is_bearish(data['open'].iloc[i-3], data['close'].iloc[i-3]) and
                        cls._is_bearish(data['open'].iloc[i-2], data['close'].iloc[i-2]) and
                        cls._is_bearish(data['open'].iloc[i-1], data['close'].iloc[i-1]) and
                        data['close'].iloc[i-2] < data['close'].iloc[i-3] and
                        data['close'].iloc[i-1] < data['close'].iloc[i-2] and
                        cls._is_bullish(data['open'].iloc[i], data['close'].iloc[i]) and
                        data['close'].iloc[i] > data['open'].iloc[i-3]):
                        signals.iloc[i] = 1
                    
                    # Bearish Three Line Strike
                    elif (cls._is_bullish(data['open'].iloc[i-3], data['close'].iloc[i-3]) and
                          cls._is_bullish(data['open'].iloc[i-2], data['close'].iloc[i-2]) and
                          cls._is_bullish(data['open'].iloc[i-1], data['close'].iloc[i-1]) and
                          data['close'].iloc[i-2] > data['close'].iloc[i-3] and
                          data['close'].iloc[i-1] > data['close'].iloc[i-2] and
                          cls._is_bearish(data['open'].iloc[i], data['close'].iloc[i]) and
                          data['close'].iloc[i] < data['open'].iloc[i-3]):
                        signals.iloc[i] = -1
                except Exception as e:
                    print(f"Error processing Three Line Strike at index {i}: {str(e)}")
                    continue
            
            return signals
        except Exception as e:
            print(f"Error identifying Three Line Strike patterns: {str(e)}")
            return pd.Series(0, index=data.index)

    @classmethod
    def scan_all_patterns(cls, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Scan for all supported candlestick patterns
        Args:
            data: OHLC DataFrame
        Returns:
            Dictionary of pattern signals
        """
        try:
            if data is None or data.empty:
                raise ValueError("No data provided for pattern analysis")

            return {
                'doji': cls.identify_doji(data),
                'hammer': cls.identify_hammer(data),
                'engulfing': cls.identify_engulfing(data),
                'star': cls.identify_morning_evening_star(data),
                'three_line_strike': cls.identify_three_line_strike(data)
            }
        except Exception as e:
            print(f"Error scanning patterns: {str(e)}")
            empty_series = pd.Series(0, index=data.index if data is not None and not data.empty else [])
            return {
                'doji': empty_series,
                'hammer': empty_series,
                'engulfing': empty_series,
                'star': empty_series,
                'three_line_strike': empty_series
            }
