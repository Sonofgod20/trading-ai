import pandas as pd
import numpy as np
from typing import Union, List, Dict, Optional

class TechnicalIndicators:
    @staticmethod
    def calculate_ema(data: pd.Series, periods: Union[int, List[int]] = 20) -> Dict[str, pd.Series]:
        """
        Calculate Exponential Moving Average(s)
        Args:
            data: Price series data
            periods: Integer or list of integers for EMA periods
        Returns:
            Dictionary of EMAs keyed by period
        """
        if isinstance(periods, int):
            periods = [periods]
        
        emas = {}
        for period in periods:
            emas[f'EMA_{period}'] = data.ewm(span=period, adjust=False).mean()
        return emas

    @staticmethod
    def calculate_advanced_rsi(data: pd.Series, period: int = 14, 
                             overbought: float = 70, oversold: float = 30) -> Dict[str, Union[pd.Series, pd.Series]]:
        """
        Calculate RSI with additional signals
        Args:
            data: Price series data
            period: RSI period
            overbought: Overbought threshold
            oversold: Oversold threshold
        Returns:
            Dictionary containing RSI values and signals
        """
        try:
            # Ensure data is clean and finite
            data = pd.to_numeric(data, errors='coerce')
            data = data.replace([np.inf, -np.inf], np.nan)
            data = data.fillna(method='ffill')  # Forward fill any remaining NaN values
            
            if data.isna().any():
                data = data.fillna(data.mean())  # Fill any remaining NaNs with mean
            
            # Calculate price changes
            delta = data.diff()
            
            # Separate gains and losses, ensuring no NaN or infinite values
            gain = delta.clip(lower=0).fillna(0)
            loss = (-delta.clip(upper=0)).fillna(0)
            
            # Calculate average gain and loss
            avg_gain = gain.rolling(window=period, min_periods=1).mean()
            avg_loss = loss.rolling(window=period, min_periods=1).mean()
            
            # Ensure no zero division
            avg_loss = avg_loss.replace(0, 0.00001)
            
            # Calculate RS and RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            # Clean up any remaining invalid values
            rsi = rsi.clip(0, 100)
            rsi = rsi.fillna(50)  # Fill any remaining NaNs with neutral RSI
            
            # Generate signals
            signals = pd.Series(0, index=data.index)
            signals.loc[rsi < oversold] = 1  # Oversold (potential buy)
            signals.loc[rsi > overbought] = -1  # Overbought (potential sell)
            
            # Calculate RSI divergence
            def check_higher_high(x):
                if len(x) < 2:
                    return False
                current = x.iloc[-1]
                previous = x.iloc[:-1].max()
                return current > previous

            def check_lower_low(x):
                if len(x) < 2:
                    return False
                current = x.iloc[-1]
                previous = x.iloc[:-1].min()
                return current < previous

            # Calculate price and RSI trends
            price_higher_highs = data.rolling(window=period).apply(check_higher_high).astype(int)
            rsi_lower_highs = rsi.rolling(window=period).apply(lambda x: 1 if len(x) > 1 and x.iloc[-1] < x.iloc[:-1].max() else 0)
            bearish_divergence = (price_higher_highs.astype(bool) & rsi_lower_highs.astype(bool)).astype(int)
            
            price_lower_lows = data.rolling(window=period).apply(check_lower_low).astype(int)
            rsi_higher_lows = rsi.rolling(window=period).apply(lambda x: 1 if len(x) > 1 and x.iloc[-1] > x.iloc[:-1].min() else 0)
            bullish_divergence = (price_lower_lows.astype(bool) & rsi_higher_lows.astype(bool)).astype(int)
            
            return {
                'RSI': rsi,
                'signals': signals,
                'bearish_divergence': bearish_divergence,
                'bullish_divergence': bullish_divergence
            }
        except Exception as e:
            print(f"Error calculating RSI: {str(e)}")
            # Return default values
            empty_series = pd.Series(0, index=data.index)
            return {
                'RSI': empty_series,
                'signals': empty_series,
                'bearish_divergence': empty_series,
                'bullish_divergence': empty_series
            }

    @staticmethod
    def calculate_support_resistance(data: pd.DataFrame, window: int = 20, 
                                  num_touches: int = 2) -> Dict[str, List[float]]:
        """
        Calculate support and resistance levels
        Args:
            data: OHLC DataFrame
            window: Period for calculating levels
            num_touches: Minimum number of touches to confirm level
        Returns:
            Dictionary containing support and resistance levels
        """
        try:
            def is_support(df: pd.DataFrame, i: int) -> bool:
                if i - window < 0 or i + window >= len(df):
                    return False
                
                current_low = df['low'].iloc[i]
                for j in range(i-window, i+window):
                    if df['low'].iloc[j] < current_low:
                        return False
                return True
            
            def is_resistance(df: pd.DataFrame, i: int) -> bool:
                if i - window < 0 or i + window >= len(df):
                    return False
                
                current_high = df['high'].iloc[i]
                for j in range(i-window, i+window):
                    if df['high'].iloc[j] > current_high:
                        return False
                return True
            
            levels = []
            
            # Find potential levels
            for i in range(window, len(data) - window):
                if is_support(data, i):
                    levels.append((i, data['low'].iloc[i], 'support'))
                elif is_resistance(data, i):
                    levels.append((i, data['high'].iloc[i], 'resistance'))
            
            # Count touches for each level
            support_levels = []
            resistance_levels = []
            
            for level in levels:
                touches = 0
                level_price = level[1]
                level_type = level[2]
                
                # Count price touches around this level
                for i in range(len(data)):
                    if level_type == 'support':
                        if abs(data['low'].iloc[i] - level_price) <= (level_price * 0.002):  # 0.2% tolerance
                            touches += 1
                    else:
                        if abs(data['high'].iloc[i] - level_price) <= (level_price * 0.002):
                            touches += 1
                
                if touches >= num_touches:
                    if level_type == 'support':
                        support_levels.append(level_price)
                    else:
                        resistance_levels.append(level_price)
            
            return {
                'support': sorted(list(set(support_levels))),
                'resistance': sorted(list(set(resistance_levels)))
            }
        except Exception as e:
            print(f"Error calculating support/resistance: {str(e)}")
            return {'support': [], 'resistance': []}

    @staticmethod
    def calculate_volume_profile(data: pd.DataFrame, price_levels: int = 100) -> Dict[str, Union[float, pd.Series]]:
        """
        Calculate Volume Profile
        Args:
            data: OHLC DataFrame with volume
            price_levels: Number of price levels for volume distribution
        Returns:
            Dictionary containing volume profile analysis
        """
        try:
            if len(data) == 0:
                raise ValueError("Empty data provided")

            # Calculate price range and create bins
            price_min = min(data['low'].min(), data['close'].min())
            price_max = max(data['high'].max(), data['close'].max())
            
            if price_min == price_max:
                price_max = price_min * 1.001  # Add small difference if prices are equal
            
            price_delta = (price_max - price_min) / price_levels
            if price_delta == 0:
                price_delta = 0.00001  # Prevent division by zero
            
            volume_profile = pd.Series(0.0, index=np.linspace(price_min, price_max, price_levels))
            
            # Distribute volume across price levels
            for i in range(len(data)):
                vol = data['volume'].iloc[i]
                low = data['low'].iloc[i]
                high = data['high'].iloc[i]
                
                # Handle cases where high equals low
                if high == low:
                    high = low * 1.00001  # Add small difference
                
                # Distribute volume proportionally across price range
                for price in volume_profile.index:
                    if low <= price <= high:
                        try:
                            volume_profile.loc[price] += vol / ((high - low) / price_delta)
                        except (ZeroDivisionError, RuntimeWarning):
                            volume_profile.loc[price] += vol  # Just add the volume if division fails
            
            # Find POC (Point of Control) - price level with highest volume
            poc = volume_profile.idxmax()
            
            # Calculate Value Area (70% of volume)
            total_volume = volume_profile.sum()
            value_area_volume = total_volume * 0.7
            cumulative_volume = 0
            value_area_prices = []
            
            # Sort volumes in descending order and accumulate until reaching value area volume
            for price in volume_profile.sort_values(ascending=False).index:
                cumulative_volume += volume_profile[price]
                value_area_prices.append(price)
                if cumulative_volume >= value_area_volume:
                    break
            
            if not value_area_prices:
                raise ValueError("No value area prices calculated")
            
            value_area_high = max(value_area_prices)
            value_area_low = min(value_area_prices)
            
            return {
                'volume_profile': volume_profile,
                'poc': poc,
                'value_area_high': value_area_high,
                'value_area_low': value_area_low
            }
        except Exception as e:
            print(f"Error calculating volume profile: {str(e)}")
            # Return default values
            return {
                'volume_profile': pd.Series(),
                'poc': data['close'].mean() if len(data) > 0 else 0,
                'value_area_high': data['high'].max() if len(data) > 0 else 0,
                'value_area_low': data['low'].min() if len(data) > 0 else 0
            }

    @staticmethod
    def calculate_token_correlation(price_data: Dict[str, pd.Series], 
                                 base_token: str = 'BTCUSDT',
                                 window: int = 20) -> pd.DataFrame:
        """
        Calculate rolling correlation between tokens
        Args:
            price_data: Dictionary of price series for different tokens
            base_token: Token to correlate against (default: BTCUSDT)
            window: Rolling window for correlation
        Returns:
            DataFrame of correlations
        """
        try:
            # Create DataFrame with all token prices
            df = pd.DataFrame(price_data)
            
            # Calculate returns
            returns = df.pct_change()
            
            # Calculate rolling correlations with base token
            correlations = pd.DataFrame()
            base_returns = returns[base_token]
            
            for token in returns.columns:
                if token != base_token:
                    correlations[token] = returns[token].rolling(window).corr(base_returns)
            
            return correlations
        except Exception as e:
            print(f"Error calculating correlations: {str(e)}")
            return pd.DataFrame()
