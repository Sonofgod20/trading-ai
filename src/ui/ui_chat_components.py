import streamlit as st
import pandas as pd
from typing import Dict
from datetime import datetime, timedelta
from src.analysis.prompt.prompt_formatter import MarketAnalysisPromptFormatter
import asyncio
import uuid
from .ui_market_components import (
    format_price,
    analyze_order_book,
    format_order_book_context,
    get_market_context
)

async def get_market_data(prompt_formatter, market_data: Dict, symbol: str) -> pd.DataFrame:
    """Get formatted market data"""
    try:
        # Convert market_data to DataFrame if it's not already
        if not isinstance(market_data, pd.DataFrame):
            market_data = pd.DataFrame(market_data)
        
        return await prompt_formatter.format_market_data(market_data, symbol)
    except Exception as e:
        print(f"Error getting market data: {str(e)}")
        return pd.DataFrame(market_data)

def display_realtime_chat(market_data: Dict, analysis_service):
    """Display real-time chat interface with market data context"""
    try:
        # Initialize states
        if 'analysis_mode' not in st.session_state:
            st.session_state.analysis_mode = "real-time"
        if 'historical_data' not in st.session_state:
            st.session_state.historical_data = None
        if 'prompt_formatter' not in st.session_state:
            st.session_state.prompt_formatter = MarketAnalysisPromptFormatter()
        if 'conversation_id' not in st.session_state:
            st.session_state.conversation_id = str(uuid.uuid4())
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'include_order_book' not in st.session_state:
            st.session_state.include_order_book = False
        if 'last_update' not in st.session_state:
            st.session_state.last_update = 0
        if 'cached_market_context' not in st.session_state:
            st.session_state.cached_market_context = ""
            
        # Get trading pairs (needed for historical mode)
        trading_pairs = analysis_service.client.get_trading_pairs()

        # Display chat interface with mode indicator and order book toggle
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.subheader("💬 Trading Assistant")
        with col2:
            if st.session_state.analysis_mode == "historical":
                st.info("📈 Historical Analysis Mode (1 Year)", icon="📊")
        with col3:
            st.session_state.include_order_book = st.toggle("Include Order Book Analysis", value=st.session_state.include_order_book)
        
        # Display chat history from session state
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Ask about market conditions or trading strategies..."):
            # Check for historical analysis keywords
            historical_keywords = ['historical', 'history', 'past', 'previous', 'performance', 'backtest']
            is_historical = any(keyword in prompt.lower() for keyword in historical_keywords)
            
            # Update analysis mode and fetch historical data if needed
            if is_historical:
                st.session_state.analysis_mode = "historical"
                # Get 1 year of historical data for the first symbol (default)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                st.session_state.historical_data = analysis_service.client.get_market_data(
                    symbol=trading_pairs[0],
                    interval='1d'
                )
            else:
                st.session_state.analysis_mode = "real-time"
                st.session_state.historical_data = None
            
            # Add user message to session state
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)

            # Get market context from cache or update if needed
            market_context = get_market_context(analysis_service)
            
            # Create AI context
            ai_context = market_context
            
            # Add order book context if enabled
            if st.session_state.include_order_book:
                # Create MarketAnalyzer instance for order book analysis
                market_analyzer = MarketAnalyzer(analysis_service.client)
                order_book = analyze_order_book(market_analyzer, trading_pairs[0])
                if order_book:
                    ai_context += format_order_book_context(order_book)
            
            # Add historical context if in historical mode
            if st.session_state.analysis_mode == "historical" and st.session_state.historical_data is not None:
                # Calculate key metrics from historical data
                hist_data = st.session_state.historical_data
                year_high = float(hist_data['high'].max())
                year_low = float(hist_data['low'].min())
                year_open = float(hist_data['open'].iloc[0])
                year_close = float(hist_data['close'].iloc[-1])
                year_change = ((year_close - year_open) / year_open) * 100
                
                historical_context = f"""
Historical Data Analysis (1 Year):
    Yearly High: {format_price(year_high)}
    Yearly Low: {format_price(year_low)}
    Year Open: {format_price(year_open)}
    Year Close: {format_price(year_close)}
    Year Change: {year_change:.2f}%
"""
                ai_context = f"{historical_context}\n{ai_context}"
            
            ai_context += f"\nUser Question: {prompt}"
            
            # Get AI response with loading indicator
            try:
                with st.spinner("🤖 AI is analyzing the market..."):
                    response = analysis_service.chat(
                        messages=[{"role": "user", "content": ai_context}],
                        system_prompt="""""",
                        conversation_id=st.session_state.conversation_id,
                        symbol=trading_pairs[0]  # Use first symbol as default
                    )
                
                # Add AI response to session state
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                with st.chat_message("assistant"):
                    st.markdown(response)
                
            except Exception as e:
                st.error(f"Error getting AI response: {str(e)}")
                import traceback
                print(traceback.format_exc())

    except Exception as e:
        st.error(f"Error in real-time chat: {str(e)}")
        import traceback
        print(traceback.format_exc())
