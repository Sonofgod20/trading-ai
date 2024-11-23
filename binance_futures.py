import requests
import hmac
import hashlib
import time
from urllib.parse import urlencode
import pandas as pd
import streamlit as st
import traceback
from datetime import datetime, timedelta

class BinanceFuturesClient:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        # Changed back to testnet URL
        self.base_url = "https://testnet.binancefuture.com"
        self.api_v1_url = f"{self.base_url}/fapi/v1"
        self.api_v2_url = f"{self.base_url}/fapi/v2"
        self.symbol_info = {}
        self.current_symbol = None
        # Extended list of trading pairs
        self.allowed_pairs = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 
            'DOGEUSDT', 'MATICUSDT', 'SOLUSDT', 'DOTUSDT', 'LTCUSDT',
            'AVAXUSDT', 'LINKUSDT', 'UNIUSDT', 'ATOMUSDT', 'ETCUSDT',
            'FILUSDT', 'AAVEUSDT', 'NEARUSDT', 'ALGOUSDT', 'ICPUSDT',
            'SANDUSDT', 'MANAUSDT', 'APTUSDT', 'GMTUSDT', 'GALAUSDT',
            'FTMUSDT', 'AXSUSDT', 'RUNEUSDT', 'EOSUSDT', 'THETAUSDT'
        ]
        self._load_exchange_info()

    def get_current_symbol(self) -> str:
        """Get the currently selected trading symbol"""
        return self.current_symbol

    def _load_exchange_info(self):
        """Load and cache exchange information"""
        try:
            exchange_info = self._make_request('exchangeInfo')
            if exchange_info and 'symbols' in exchange_info:
                for symbol in exchange_info['symbols']:
                    if symbol['symbol'] in self.allowed_pairs:  # Solo cargar info de pares permitidos
                        self.symbol_info[symbol['symbol']] = {
                            'quantityPrecision': symbol['quantityPrecision'],
                            'pricePrecision': symbol['pricePrecision']
                        }
        except Exception as e:
            print(f"Error loading exchange info: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")

    def _format_number(self, number, precision):
        """Format number to specified decimal precision"""
        try:
            return f"%.{precision}f" % float(number)
        except Exception as e:
            print(f"Error formatting number: {str(e)}")
            return str(number)

    def _generate_signature(self, params):
        """Generate signature for authenticated requests"""
        try:
            return hmac.new(
                self.api_secret.encode('utf-8'),
                urlencode(params).encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
        except Exception as e:
            print(f"Error generating signature: {str(e)}")
            return None

    def _make_request(self, endpoint, method='GET', params=None, signed=False, version='v1'):
        """Make request to Binance Futures API"""
        try:
            base_url = self.api_v2_url if version == 'v2' else self.api_v1_url
            url = f"{base_url}/{endpoint}"
            headers = {'X-MBX-APIKEY': self.api_key}
            
            if params is None:
                params = {}
                
            if signed:
                # Add required parameters for signed requests
                params['timestamp'] = int(time.time() * 1000)
                params['recvWindow'] = 5000
                params['signature'] = self._generate_signature(params)
            
            response = requests.request(method, url, headers=headers, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Request error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return None

    def get_historical_klines(self, symbol, interval, start_time=None, end_time=None, limit=1500):
        """Get historical klines/candlestick data"""
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            # Convert datetime objects to milliseconds timestamp
            if isinstance(start_time, datetime):
                params['startTime'] = int(start_time.timestamp() * 1000)
            elif start_time:
                params['startTime'] = int(start_time * 1000)
                
            if isinstance(end_time, datetime):
                params['endTime'] = int(end_time.timestamp() * 1000)
            elif end_time:
                params['endTime'] = int(end_time * 1000)

            klines = self._make_request('klines', params=params)
            
            if not klines:
                return None
                
            # Create DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convert timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Convert numeric columns
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 
                             'quote_volume', 'trades', 'taker_buy_base', 
                             'taker_buy_quote']
            df[numeric_columns] = df[numeric_columns].astype(float)
            
            # Add mark price and funding rate columns
            mark_price_info = self._make_request('premiumIndex', params={'symbol': symbol})
            if mark_price_info:
                df['mark_price'] = float(mark_price_info['markPrice'])
                df['funding_rate'] = float(mark_price_info['lastFundingRate'])
            else:
                df['mark_price'] = df['close']
                df['funding_rate'] = 0.0
            
            return df
            
        except Exception as e:
            print(f"Error fetching historical klines: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return None

    def get_account_info(self):
        """Get account information using v2 endpoint"""
        try:
            account_info = self._make_request('account', signed=True, version='v2')
            if account_info and 'totalWalletBalance' in account_info:
                return {
                    'balance': float(account_info['totalWalletBalance']),
                    'unrealized_pnl': float(account_info['totalUnrealizedProfit']),
                    'margin_balance': float(account_info['totalMarginBalance']),
                    'positions': [p for p in account_info['positions'] if float(p['positionAmt']) != 0]
                }
            return None
        except Exception as e:
            print(f"Error getting account info: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return None

    def get_trading_pairs(self):
        """Get available trading pairs"""
        try:
            # Retornar solo los pares permitidos
            return self.allowed_pairs
        except Exception as e:
            print(f"Error getting trading pairs: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return ["BTCUSDT", "ETHUSDT", "BNBUSDT"]  # Default pairs if error

    def get_market_data(self, symbol='BTCUSDT', interval='1h', limit=None):
        """Get market data"""
        try:
            # Update current symbol
            self.current_symbol = symbol
            
            # Verificar que el símbolo está en la lista de permitidos
            if symbol not in self.allowed_pairs:
                print(f"Symbol {symbol} is not in allowed trading pairs")
                return None
            
            # Calculate limit based on interval if not provided
            if limit is None:
                # Calculate candles needed for 1 month based on interval
                interval_minutes = {
                    '1m': 1,
                    '5m': 5,
                    '15m': 15,
                    '1h': 60,
                    '4h': 240,
                    '1d': 1440
                }
                minutes_in_month = 43200  # 30 days * 24 hours * 60 minutes
                limit = min(1500, minutes_in_month // interval_minutes.get(interval, 60))
            
            # Get klines data
            df = self.get_historical_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            if df is None:
                print(f"No klines data received for {symbol}")
                return None
            
            # Get 24hr ticker
            ticker = self._make_request('ticker/24hr', params={'symbol': symbol})
            if ticker:
                df['price_change'] = float(ticker['priceChange'])
                df['price_change_percent'] = float(ticker['priceChangePercent'])
                df['weighted_avg_price'] = float(ticker['weightedAvgPrice'])
                df['last_price'] = float(ticker['lastPrice'])
                df['last_qty'] = float(ticker['lastQty'])
            else:
                df['price_change'] = 0.0
                df['price_change_percent'] = 0.0
                df['weighted_avg_price'] = df['close']
                df['last_price'] = df['close']
                df['last_qty'] = 0.0
            
            # Get order book
            depth = self._make_request('depth', params={'symbol': symbol, 'limit': 5})
            if depth and depth.get('bids') and depth.get('asks'):
                df['top_bid_price'] = float(depth['bids'][0][0])
                df['top_bid_qty'] = float(depth['bids'][0][1])
                df['top_ask_price'] = float(depth['asks'][0][0])
                df['top_ask_qty'] = float(depth['asks'][0][1])
            else:
                df['top_bid_price'] = df['close']
                df['top_bid_qty'] = 0.0
                df['top_ask_price'] = df['close']
                df['top_ask_qty'] = 0.0
            
            return df
        except Exception as e:
            print(f"Error fetching market data: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return None

    def execute_trade(self, symbol, side, quantity, price=None, stop_loss=None, take_profit=None):
        """Execute a trade"""
        try:
            # Verificar que el símbolo está en la lista de permitidos
            if symbol not in self.allowed_pairs:
                print(f"Symbol {symbol} is not in allowed trading pairs")
                return None
                
            # Get symbol precision info
            if symbol not in self.symbol_info:
                self._load_exchange_info()
            
            if symbol not in self.symbol_info:
                print(f"Could not get precision info for {symbol}")
                return None
            
            precision_info = self.symbol_info[symbol]
            
            # Format quantity and prices according to symbol precision
            formatted_quantity = self._format_number(quantity, precision_info['quantityPrecision'])
            
            # Prepare order parameters
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'LIMIT' if price else 'MARKET',
                'quantity': formatted_quantity,
            }
            
            if price:
                formatted_price = self._format_number(price, precision_info['pricePrecision'])
                params['price'] = formatted_price
                params['timeInForce'] = 'GTC'
            
            # Place main order
            order = self._make_request('order', method='POST', params=params, signed=True)
            
            # If order is successful and stop loss/take profit are provided
            if order and (stop_loss or take_profit):
                if stop_loss:
                    sl_side = 'SELL' if side == 'BUY' else 'BUY'
                    formatted_sl = self._format_number(stop_loss, precision_info['pricePrecision'])
                    self._make_request('order', method='POST', params={
                        'symbol': symbol,
                        'side': sl_side,
                        'type': 'STOP_MARKET',
                        'stopPrice': formatted_sl,
                        'closePosition': 'true',
                        'timeInForce': 'GTC'
                    }, signed=True)
                
                if take_profit:
                    tp_side = 'SELL' if side == 'BUY' else 'BUY'
                    formatted_tp = self._format_number(take_profit, precision_info['pricePrecision'])
                    self._make_request('order', method='POST', params={
                        'symbol': symbol,
                        'side': tp_side,
                        'type': 'TAKE_PROFIT_MARKET',
                        'stopPrice': formatted_tp,
                        'closePosition': 'true',
                        'timeInForce': 'GTC'
                    }, signed=True)
            
            return order
        except Exception as e:
            print(f"Error executing trade: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return None
