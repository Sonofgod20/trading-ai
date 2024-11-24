import streamlit as st
from typing import Dict, Optional
import re

class TradeExecutor:
    def __init__(self, binance_client, position_tracker):
        """Initialize TradeExecutor with dependencies"""
        self.client = binance_client
        self.position_tracker = position_tracker
        self.MAX_TRADE_VALUE = 500  # Maximum $500 per trade

    def execute_trade(self, symbol: str, price_levels: Dict, position_size: float) -> bool:
        """Execute trade based on chatbase recommendation"""
        try:
            # Get current market price for value calculation
            market_data = self.client.get_market_data(symbol)
            if market_data is None:
                st.error("Could not get current market price")
                return False
            
            current_price = float(market_data['last_price'].iloc[-1])
            
            # Get symbol info for lot size validation
            exchange_info = self.client._make_request('exchangeInfo')
            lot_size_info = self._get_lot_size_filter(exchange_info, symbol)
            
            if not lot_size_info:
                st.error(f"Could not get lot size information for {symbol}")
                return False
            
            # Adjust position size based on lot size constraints
            position_size = self._adjust_quantity_to_lot_size(
                position_size,
                float(lot_size_info['minQty']),
                float(lot_size_info['maxQty']),
                float(lot_size_info['stepSize'])
            )
            
            # Calculate and verify trade value
            trade_value = position_size * current_price
            if trade_value >= self.MAX_TRADE_VALUE:
                position_size = (self.MAX_TRADE_VALUE * 0.995) / current_price
                position_size = self._adjust_quantity_to_lot_size(
                    position_size,
                    float(lot_size_info['minQty']),
                    float(lot_size_info['maxQty']),
                    float(lot_size_info['stepSize'])
                )
                st.warning(f"Position size adjusted to {position_size} to maintain maximum trade value of ${self.MAX_TRADE_VALUE}")

            # Validate inputs with adjusted position size
            if not self._validate_trade_params(symbol, price_levels, position_size):
                return False

            # Format trade parameters
            side = 'BUY' if price_levels['direction'] == 'LONG' else 'SELL'
            
            # Log trade details
            st.info("Executing trade with parameters:")
            trade_details = {
                'symbol': symbol,
                'side': side,
                'quantity': position_size,
                'entry_price': price_levels['entry'],
                'stop_loss': price_levels['sl'],
                'take_profit': price_levels['tp'],
                'current_market_price': current_price,
                'estimated_value': position_size * current_price
            }
            st.json(trade_details)
            
            # Use market order if entry is close to current price
            price_diff_percent = abs(price_levels['entry'] - current_price) / current_price * 100
            use_market_order = price_diff_percent < 0.5  # Use market order if within 0.5% of current price
            
            # Execute the trade
            order = self.client.execute_trade(
                symbol=symbol,
                side=side,
                quantity=position_size,
                price=None if use_market_order else price_levels['entry'],
                stop_loss=price_levels['sl'],
                take_profit=price_levels['tp']
            )
            
            if not order:
                st.error("Trade execution failed - No order response received")
                return False
            
            if 'orderId' not in order:
                st.error(f"Trade execution failed - Invalid order response: {order}")
                return False
            
            # Add position to tracker
            self.position_tracker.add_position(
                symbol=symbol,
                entry_price=price_levels['entry'],
                stop_loss=price_levels['sl'],
                take_profit=price_levels['tp'],
                size=position_size,
                direction=price_levels['direction'],
                ai_confidence=price_levels['confidence']
            )
            
            st.success(f"""Trade executed successfully! 
            Order ID: {order['orderId']}
            Symbol: {symbol}
            Side: {side}
            Quantity: {position_size}
            Entry: {price_levels['entry']}
            Stop Loss: {price_levels['sl']}
            Take Profit: {price_levels['tp']}
            Estimated Value: ${position_size * current_price:.2f}
            """)
            
            # Clear current state
            st.session_state.current_analysis = None
            st.session_state.price_levels = None
            st.session_state.show_trade_dialog = False
            
            st.info("View your position in the Position Tracker tab")
            return True
            
        except Exception as e:
            st.error(f"Error executing trade: {str(e)}")
            return False

    def _get_lot_size_filter(self, exchange_info: Dict, symbol: str) -> Optional[Dict]:
        """Get lot size filter for a symbol"""
        try:
            if not exchange_info or 'symbols' not in exchange_info:
                return None
            
            for s in exchange_info['symbols']:
                if s['symbol'] == symbol:
                    for f in s['filters']:
                        if f['filterType'] == 'LOT_SIZE':
                            return {
                                'minQty': f['minQty'],
                                'maxQty': f['maxQty'],
                                'stepSize': f['stepSize']
                            }
            return None
        except Exception as e:
            print(f"Error getting lot size filter: {str(e)}")
            return None

    def _adjust_quantity_to_lot_size(self, quantity: float, min_qty: float, 
                                   max_qty: float, step_size: float) -> float:
        """Adjust quantity to match lot size requirements"""
        try:
            quantity = max(min_qty, min(quantity, max_qty))
            precision = 0
            step_str = f"{float(step_size):.8f}"
            if '.' in step_str:
                precision = len(step_str.split('.')[-1].rstrip('0'))
            steps = round(quantity / step_size)
            adjusted_qty = round(steps * step_size, precision)
            return adjusted_qty
        except Exception as e:
            print(f"Error adjusting quantity: {str(e)}")
            return quantity

    def _validate_trade_params(self, symbol: str, price_levels: Dict, position_size: float) -> bool:
        """Validate trade parameters before execution"""
        try:
            # Check symbol
            if not symbol or not isinstance(symbol, str):
                st.error("Invalid symbol")
                return False

            # Check price levels
            required_keys = ['entry', 'sl', 'tp', 'direction', 'confidence']
            if not all(key in price_levels for key in required_keys):
                st.error("Missing required price levels in AI response")
                return False

            # Validate direction
            if price_levels['direction'] not in ['LONG', 'SHORT']:
                st.error("Invalid trade direction from AI")
                return False

            # Validate prices
            if not all(isinstance(price_levels[k], (int, float)) 
                      for k in ['entry', 'sl', 'tp']):
                st.error("Invalid price values in AI response")
                return False

            # Check trade value
            market_data = self.client.get_market_data(symbol)
            if market_data is not None:
                current_price = float(market_data['last_price'].iloc[-1])
                trade_value = position_size * current_price
                
                if trade_value >= self.MAX_TRADE_VALUE:
                    st.error(f"Trade value ${trade_value:.2f} exceeds maximum allowed ${self.MAX_TRADE_VALUE}")
                    return False

            # Validate price relationships
            if price_levels['direction'] == 'LONG':
                if not (price_levels['sl'] < price_levels['entry'] < price_levels['tp']):
                    st.error("Invalid price levels for LONG position")
                    return False
            else:  # SHORT
                if not (price_levels['tp'] < price_levels['entry'] < price_levels['sl']):
                    st.error("Invalid price levels for SHORT position")
                    return False

            # Validate balance
            account_info = self.client.get_account_info()
            if not account_info:
                st.error("Could not verify account balance")
                return False

            required_margin = position_size * price_levels['entry'] * 0.01  # 1% initial margin
            if required_margin > account_info['balance']:
                st.error(f"Insufficient balance. Required margin: ${required_margin:.2f}")
                return False

            return True

        except Exception as e:
            st.error(f"Error validating trade parameters: {str(e)}")
            return False

    def extract_price_levels(self, ai_response: str) -> Optional[Dict]:
        """Extract price levels from chatbase AI response"""
        try:
            # Regular expressions for extracting values
            patterns = {
                'entry': r'Entry(?:\s+Price)?:\s*\$?([\d,.]+)',
                'tp': r'Take\s+Profit:\s*\$?([\d,.]+)',
                'sl': r'Stop\s+Loss:\s*\$?([\d,.]+)',
                'confidence': r'Confidence(?:\s+Level)?:\s*(\d+)%'
            }
            
            # Extract values
            extracted_values = {}
            for key, pattern in patterns.items():
                match = re.search(pattern, ai_response, re.IGNORECASE)
                if not match:
                    st.error(f"Could not extract {key} from AI response")
                    return None
                value = match.group(1).replace(',', '')
                extracted_values[key] = float(value) if key != 'confidence' else int(value)
            
            # Determine direction
            extracted_values['direction'] = 'LONG' if 'LONG' in ai_response.upper() else 'SHORT'
            
            # Validate extracted values
            if not self._validate_extracted_values(extracted_values):
                return None
                
            return extracted_values
            
        except Exception as e:
            st.error(f"Error extracting price levels from AI response: {str(e)}")
            return None

    def _validate_extracted_values(self, values: Dict) -> bool:
        """Validate extracted price levels"""
        try:
            required_keys = ['entry', 'tp', 'sl', 'direction', 'confidence']
            if not all(key in values for key in required_keys):
                st.error("Missing required price levels in AI response")
                return False

            if values['direction'] == 'LONG':
                if not (values['sl'] < values['entry'] < values['tp']):
                    st.error("Invalid price levels for LONG position")
                    return False
            else:  # SHORT
                if not (values['tp'] < values['entry'] < values['sl']):
                    st.error("Invalid price levels for SHORT position")
                    return False

            if not (0 <= values['confidence'] <= 100):
                st.error("Invalid confidence level in AI response")
                return False

            return True

        except Exception as e:
            st.error(f"Error validating AI response values: {str(e)}")
            return False
