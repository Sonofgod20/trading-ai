import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from datetime import datetime
import traceback
import os
import json

class MarketAnalyzer:
    def __init__(self, binance_client):
        """
        Initialize MarketAnalyzer with Binance client
        Args:
            binance_client: Instance of BinanceFuturesClient
        """
        self.client = binance_client
        self.timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
        self.data_dir = 'data/market_data'
        self._ensure_data_directory()

    def _ensure_data_directory(self):
        """Ensure the data directory exists"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _get_cache_filename(self, symbol: str, timeframe: str) -> str:
        """Get the cache filename for a symbol and timeframe"""
        return os.path.join(self.data_dir, f"{symbol}_{timeframe}.json")

    def _save_to_cache(self, symbol: str, timeframe: str, data: pd.DataFrame):
        """Save market data to cache"""
        try:
            cache_file = self._get_cache_filename(symbol, timeframe)
            data_dict = {
                'last_updated': datetime.now().isoformat(),
                'data': data.reset_index().to_dict(orient='records')
            }
            with open(cache_file, 'w') as f:
                json.dump(data_dict, f)
        except Exception as e:
            print(f"Error saving to cache: {str(e)}")

    def _load_from_cache(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Load market data from cache if available and recent"""
        try:
            cache_file = self._get_cache_filename(symbol, timeframe)
            if not os.path.exists(cache_file):
                return None

            with open(cache_file, 'r') as f:
                cached_data = json.load(f)

            last_updated = datetime.fromisoformat(cached_data['last_updated'])
            # Check if cache is recent (less than 1 hour old)
            if (datetime.now() - last_updated).total_seconds() < 3600:
                df = pd.DataFrame(cached_data['data'])
                if not df.empty:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                    return df
            return None
        except Exception as e:
            print(f"Error loading from cache: {str(e)}")
            return None

    def get_multi_timeframe_data(self, symbol: str, 
                               timeframes: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """
        Get market data for multiple timeframes
        Args:
            symbol: Trading pair symbol
            timeframes: List of timeframes to fetch (default: all supported timeframes)
        Returns:
            Dictionary of DataFrames keyed by timeframe
        """
        if timeframes is None:
            timeframes = self.timeframes
        
        data = {}
        try:
            for tf in timeframes:
                print(f"Fetching data for {symbol} on {tf} timeframe...")
                # Try to load from cache first
                df = self._load_from_cache(symbol, tf)
                
                if df is None:
                    # If not in cache or cache is old, fetch from API
                    df = self.client.get_market_data(symbol, tf)
                    if df is not None and not df.empty:
                        # Save to cache for future use
                        self._save_to_cache(symbol, tf, df)
                        data[tf] = df
                else:
                    data[tf] = df
            
            if not data:
                print(f"Error: No data available for {symbol} on any timeframe")
            return data
        
        except Exception as e:
            print(f"Error in get_multi_timeframe_data: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return data

    def analyze_order_book_depth(self, symbol: str, levels: int = 20) -> Dict[str, Union[float, Dict]]:
        """
        Perform deep order book analysis
        Args:
            symbol: Trading pair symbol
            levels: Number of price levels to analyze
        Returns:
            Dictionary containing order book analysis
        """
        try:
            print(f"Analyzing order book for {symbol}...")
            # Get order book data
            depth = self.client._make_request('depth', params={
                'symbol': symbol,
                'limit': levels
            })
            
            if not depth or 'bids' not in depth or 'asks' not in depth:
                print(f"Warning: Invalid order book data received for {symbol}")
                return None
            
            # Convert to DataFrames
            bids_df = pd.DataFrame(depth['bids'], columns=['price', 'quantity'], dtype=float)
            asks_df = pd.DataFrame(depth['asks'], columns=['price', 'quantity'], dtype=float)
            
            if bids_df.empty or asks_df.empty:
                print(f"Warning: Empty order book data for {symbol}")
                return None
            
            # Calculate cumulative volumes
            bids_df['cumulative_volume'] = bids_df['quantity'].cumsum()
            asks_df['cumulative_volume'] = asks_df['quantity'].cumsum()
            
            # Calculate price levels metrics
            mid_price = (float(bids_df['price'].iloc[0]) + float(asks_df['price'].iloc[0])) / 2
            spread = float(asks_df['price'].iloc[0]) - float(bids_df['price'].iloc[0])
            spread_percentage = (spread / mid_price) * 100
            
            # Analyze order imbalance
            bid_volume = bids_df['quantity'].sum()
            ask_volume = asks_df['quantity'].sum()
            total_volume = bid_volume + ask_volume
            bid_ask_ratio = bid_volume / ask_volume if ask_volume > 0 else float('inf')
            
            # Find significant levels (walls)
            bid_walls = []
            ask_walls = []
            
            # Define volume threshold for walls (e.g., 2x average volume)
            avg_bid_volume = bids_df['quantity'].mean()
            avg_ask_volume = asks_df['quantity'].mean()
            
            for _, row in bids_df.iterrows():
                if row['quantity'] > avg_bid_volume * 2:
                    bid_walls.append({
                        'price': float(row['price']),
                        'quantity': float(row['quantity'])
                    })
            
            for _, row in asks_df.iterrows():
                if row['quantity'] > avg_ask_volume * 2:
                    ask_walls.append({
                        'price': float(row['price']),
                        'quantity': float(row['quantity'])
                    })
            
            # Calculate liquidity zones
            bid_liquidity_zones = self._identify_liquidity_zones(bids_df)
            ask_liquidity_zones = self._identify_liquidity_zones(asks_df)
            
            return {
                'mid_price': mid_price,
                'spread': spread,
                'spread_percentage': spread_percentage,
                'bid_ask_ratio': bid_ask_ratio,
                'bid_volume': float(bid_volume),
                'ask_volume': float(ask_volume),
                'total_volume': float(total_volume),
                'buy_pressure': (bid_volume / total_volume) * 100 if total_volume > 0 else 50,
                'sell_pressure': (ask_volume / total_volume) * 100 if total_volume > 0 else 50,
                'bid_walls': bid_walls,
                'ask_walls': ask_walls,
                'liquidity_zones': {
                    'bids': bid_liquidity_zones,
                    'asks': ask_liquidity_zones
                }
            }
        except Exception as e:
            print(f"Error analyzing order book: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return None

    def _identify_liquidity_zones(self, df: pd.DataFrame, 
                                volume_threshold: float = 0.1) -> List[Dict]:
        """
        Identify liquidity zones in order book
        Args:
            df: Order book DataFrame
            volume_threshold: Minimum volume ratio to consider as liquidity zone
        Returns:
            List of liquidity zones
        """
        try:
            if df.empty:
                return []

            total_volume = df['quantity'].sum()
            if total_volume == 0:
                return []

            threshold_volume = total_volume * volume_threshold
            zones = []
            
            current_zone = {
                'start_price': float(df['price'].iloc[0]),
                'volume': 0
            }
            
            for _, row in df.iterrows():
                current_zone['volume'] += float(row['quantity'])
                
                if current_zone['volume'] >= threshold_volume:
                    current_zone['end_price'] = float(row['price'])
                    zones.append(current_zone.copy())
                    current_zone = {
                        'start_price': float(row['price']),
                        'volume': 0
                    }
            
            return zones
        except Exception as e:
            print(f"Error identifying liquidity zones: {str(e)}")
            return []

    def analyze_volume_profile(self, symbol: str, timeframes: Optional[List[str]] = None,
                             num_bins: int = 50) -> Dict[str, Dict]:
        """
        Analyze volume profile across multiple timeframes
        Args:
            symbol: Trading pair symbol
            timeframes: List of timeframes to analyze
            num_bins: Number of price bins for volume distribution
        Returns:
            Dictionary of volume profiles by timeframe
        """
        if timeframes is None:
            timeframes = ['1h', '4h', '1d']
        
        profiles = {}
        try:
            # Get data from cache or API
            data_dict = self.get_multi_timeframe_data(symbol, timeframes)
            
            for tf, data in data_dict.items():
                print(f"Analyzing volume profile for {symbol} on {tf} timeframe...")
                if data is not None and not data.empty:
                    try:
                        # Calculate price range
                        price_min = data['low'].min()
                        price_max = data['high'].max()
                        
                        # Add small buffer to prevent identical min/max
                        if price_min == price_max:
                            price_max *= 1.001
                            price_min *= 0.999
                        
                        price_range = np.linspace(price_min, price_max, num_bins)
                        
                        # Initialize volume profile
                        volume_profile = np.zeros(num_bins)
                        
                        # Distribute volume across price levels
                        for i in range(len(data)):
                            vol = data['volume'].iloc[i]
                            price = data['close'].iloc[i]
                            
                            # Find the appropriate price bin
                            bin_idx = np.digitize(price, price_range) - 1
                            if 0 <= bin_idx < num_bins:
                                volume_profile[bin_idx] += vol
                        
                        if volume_profile.sum() == 0:
                            raise ValueError("No volume data available")
                        
                        # Find POC (Point of Control)
                        poc_idx = np.argmax(volume_profile)
                        poc_price = price_range[poc_idx]
                        
                        # Calculate Value Area (70% of volume)
                        total_volume = volume_profile.sum()
                        sorted_idx = np.argsort(volume_profile)[::-1]
                        cumsum_volume = np.cumsum(volume_profile[sorted_idx])
                        value_area_idx = sorted_idx[cumsum_volume <= total_volume * 0.7]
                        
                        if len(value_area_idx) == 0:
                            value_area_high = price_max
                            value_area_low = price_min
                        else:
                            value_area_prices = price_range[value_area_idx]
                            value_area_high = value_area_prices.max()
                            value_area_low = value_area_prices.min()
                        
                        profiles[tf] = {
                            'price_levels': price_range.tolist(),
                            'volume_profile': volume_profile.tolist(),
                            'poc': float(poc_price),
                            'value_area_high': float(value_area_high),
                            'value_area_low': float(value_area_low),
                            'total_volume': float(total_volume)
                        }
                    except Exception as e:
                        print(f"Error processing volume profile for {tf}: {str(e)}")
                        profiles[tf] = self._get_default_profile(data)
                else:
                    print(f"Warning: No data available for {symbol} on {tf} timeframe")
            
            return profiles
        
        except Exception as e:
            print(f"Error analyzing volume profile: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return {}

    def _get_default_profile(self, data: pd.DataFrame) -> Dict:
        """Get default volume profile when calculation fails"""
        try:
            if data is not None and not data.empty:
                return {
                    'price_levels': [],
                    'volume_profile': [],
                    'poc': float(data['close'].mean()),
                    'value_area_high': float(data['high'].max()),
                    'value_area_low': float(data['low'].min()),
                    'total_volume': float(data['volume'].sum())
                }
        except Exception:
            pass
        
        return {
            'price_levels': [],
            'volume_profile': [],
            'poc': 0.0,
            'value_area_high': 0.0,
            'value_area_low': 0.0,
            'total_volume': 0.0
        }

    def get_market_sentiment(self, symbol: str) -> Dict[str, Union[float, str]]:
        """
        Calculate overall market sentiment
        Args:
            symbol: Trading pair symbol
        Returns:
            Dictionary containing sentiment metrics
        """
        try:
            print(f"Calculating market sentiment for {symbol}...")
            # Get data from cache or API
            data = self.get_multi_timeframe_data(symbol, ['1h', '4h', '1d'])
            
            if not data:
                print(f"Warning: No data available for market sentiment analysis of {symbol}")
                return None
            
            # Get order book analysis
            order_book = self.analyze_order_book_depth(symbol)
            
            if not order_book:
                print(f"Warning: No order book data available for {symbol}")
                return None
            
            # Calculate sentiment metrics
            sentiment_scores = {}
            
            for tf, df in data.items():
                try:
                    # Price trend
                    price_change = (df['close'].iloc[-1] - df['open'].iloc[0]) / df['open'].iloc[0] * 100
                    
                    # Volume trend
                    volume_sma = df['volume'].rolling(window=20).mean()
                    if volume_sma.iloc[-1] > 0:
                        volume_trend = (df['volume'].iloc[-1] / volume_sma.iloc[-1]) - 1
                    else:
                        volume_trend = 0
                    
                    # Combine metrics
                    sentiment_scores[tf] = {
                        'price_change': price_change,
                        'volume_trend': volume_trend
                    }
                except Exception as e:
                    print(f"Error calculating sentiment for {tf}: {str(e)}")
                    sentiment_scores[tf] = {
                        'price_change': 0,
                        'volume_trend': 0
                    }
            
            # Calculate overall sentiment
            overall_sentiment = 0
            weights = {'1h': 0.2, '4h': 0.3, '1d': 0.5}
            
            for tf, metrics in sentiment_scores.items():
                score = (
                    np.sign(metrics['price_change']) * 
                    (1 + abs(metrics['volume_trend']))
                )
                overall_sentiment += score * weights.get(tf, 0.2)
            
            # Add order book sentiment
            book_sentiment = (order_book['buy_pressure'] - order_book['sell_pressure']) / 100
            overall_sentiment = (overall_sentiment * 0.7) + (book_sentiment * 0.3)
            
            # Classify sentiment
            sentiment_label = (
                'Very Bullish' if overall_sentiment > 0.5 else
                'Bullish' if overall_sentiment > 0.1 else
                'Neutral' if abs(overall_sentiment) <= 0.1 else
                'Bearish' if overall_sentiment > -0.5 else
                'Very Bearish'
            )
            
            return {
                'overall_score': float(overall_sentiment),
                'sentiment': sentiment_label,
                'timeframe_metrics': sentiment_scores,
                'order_book_pressure': {
                    'buy_pressure': float(order_book['buy_pressure']),
                    'sell_pressure': float(order_book['sell_pressure'])
                }
            }
        except Exception as e:
            print(f"Error calculating market sentiment: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return None
