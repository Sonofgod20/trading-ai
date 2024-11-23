from typing import Dict, Optional
import streamlit as st
import requests
from src.analysis.prompt.prompt_formatter import MarketAnalysisPromptFormatter
from src.database.chat_history_manager import ChatHistoryManager

class AnalysisService:
    def __init__(self, binance_client, chatbase_api_key, chatbase_chatbot_id):
        """Initialize AnalysisService with dependencies"""
        self.client = binance_client
        self.api_key = chatbase_api_key
        self.chatbot_id = chatbase_chatbot_id
        self.api_url = 'https://www.chatbase.co/api/v1/chat'
        self.debug_mode = False
        self.chat_manager = ChatHistoryManager()
        
        # Initialize Prompt Formatter
        self.prompt_formatter = MarketAnalysisPromptFormatter()

    def toggle_debug_mode(self):
        """Toggle debug mode to show/hide market data"""
        self.debug_mode = not self.debug_mode
        return self.debug_mode

    async def get_market_data(self, symbol: str) -> Optional[Dict]:
        """
        Get real-time market data for a specific trading pair
        Returns:
            Dictionary containing current market metrics
        """
        try:
            st.info(f"🔄 Fetching market data for {symbol}...")
            
            # Get current market data from Binance
            market_data = self.client.get_market_data(symbol)
            if market_data is None or market_data.empty:
                st.error(f"❌ Could not fetch market data for {symbol}")
                return None

            # Get exchange info for price limits
            exchange_info = self.client._make_request('exchangeInfo')
            price_limits = self._get_price_limits(exchange_info, symbol)
            
            if not price_limits:
                st.error(f"❌ Could not get price limits for {symbol}")
                return None

            # Extract current market metrics
            market_info = {
                "symbol": symbol,
                "market_data": market_data.to_dict('records'),  # Raw market data for external analysis
                "exchange_limits": price_limits
            }

            if self.debug_mode:
                st.subheader("📊 Market Data")
                st.json(market_info)

            st.success(f"✅ Market data fetched for {symbol}")
            return market_info
                
        except Exception as e:
            st.error(f"❌ Error fetching market data: {str(e)}")
            return None

    def chat(self, messages: list, system_prompt: str = None, conversation_id: str = None, symbol: str = None) -> Optional[str]:
        """Send a chat message to chatbase API"""
        try:
            if not messages or not isinstance(messages, list) or not messages[-1].get('content'):
                return None

            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            # Get conversation history if conversation_id is provided
            if conversation_id and symbol:
                history = self.chat_manager.get_chat_history(symbol=symbol, conversation_id=conversation_id)
                # Convert history to chatbase format
                chat_messages = []
                for msg in history:
                    chat_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                # Add the new message
                chat_messages.append(messages[-1])
            else:
                chat_messages = messages
            
            data = {
                'messages': chat_messages,
                'chatId': self.chatbot_id,
                'stream': True,
                'temperature': 0
            }

            # Add conversation ID if provided
            if conversation_id:
                data['conversationId'] = conversation_id

            if system_prompt:
                data['systemPrompt'] = system_prompt

            response = requests.post(self.api_url, json=data, headers=headers)
            
            if response.status_code != 200:
                st.error(f"Error from chatbase API: {response.text}")
                return None

            if not response.text:
                return None

            return response.text

        except Exception as e:
            st.error(f"Error in chat: {str(e)}")
            return None

    def _get_price_limits(self, exchange_info: Dict, symbol: str) -> Optional[Dict]:
        """Get price limits for a symbol from exchange info"""
        try:
            if not exchange_info or 'symbols' not in exchange_info:
                return None
            
            for s in exchange_info['symbols']:
                if s['symbol'] == symbol:
                    for f in s['filters']:
                        if f['filterType'] == 'PRICE_FILTER':
                            return {
                                'min_price': float(f['minPrice']),
                                'max_price': float(f['maxPrice'])
                            }
            return None
        except Exception as e:
            print(f"Error getting price limits: {str(e)}")
            return None
