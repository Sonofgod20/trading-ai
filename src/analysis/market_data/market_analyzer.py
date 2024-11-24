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
        Get raw order book data
        Args:
            symbol: Trading pair symbol
            levels: Number of price levels to get (default: 20)
        Returns:
            Dictionary containing raw order book data
        """
        try:
            print(f"Getting order book for {symbol}...")
            # Get raw order book data
            depth = self.client._make_request('depth', params={
                'symbol': symbol,
                'limit': levels
            })
            
            if not depth or 'bids' not in depth or 'asks' not in depth:
                print(f"Warning: Invalid order book data received for {symbol}")
                return None
            
            # Convert string values to float
            bids = [{'price': float(price), 'quantity': float(qty)} 
                   for price, qty in depth['bids']]
            asks = [{'price': float(price), 'quantity': float(qty)} 
                   for price, qty in depth['asks']]
            
            # Calculate basic spread info for UI display
            best_bid = float(depth['bids'][0][0])
            best_ask = float(depth['asks'][0][0])
            spread = best_ask - best_bid
            spread_percentage = (spread / best_bid) * 100
            
            # Return raw data with minimal processing
            return {
                'bids': bids,
                'asks': asks,
                'spread_percentage': spread_percentage,
                # Keep these for UI display only
                'buy_pressure': 50.0,  # Neutral default
                'sell_pressure': 50.0,  # Neutral default
                'bid_walls': [],
                'ask_walls': [],
                'liquidity_zones': {'bids': [], 'asks': []}
            }
            
        except Exception as e:
            print(f"Error analyzing order book: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return None

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
