import streamlit as st
import pandas as pd
from typing import Dict, Optional
from src.trading.analysis_parser import AnalysisParser
from datetime import datetime, timedelta
from src.analysis.market_data.market_analyzer import MarketAnalyzer
from src.analysis.prompt.prompt_formatter import MarketAnalysisPromptFormatter
import asyncio
import uuid

def format_price(price: float) -> str:
    """Format price with appropriate decimal places"""
    return f"${price:,.8f}"  # Updated to 8 decimal places for crypto

def display_market_metrics(market_data):
    """Display current market metrics"""
    current_price = float(market_data['last_price'].iloc[-1])
    price_change = float(market_data['price_change_percent'].iloc[-1])
    funding_rate = float(market_data['funding_rate'].iloc[-1])
    mark_price = float(market_data['mark_price'].iloc[-1])
    
    # Create columns with equal width
    col1, col2, col3, col4 = st.columns(4)
    
    # Add metrics with improved styling
    with col1:
        st.metric(
            "Mark Price", 
            format_price(mark_price),
            help="The official mark price used for liquidation and settlement"
        )
    with col2:
        st.metric(
            "Current Price", 
            format_price(current_price), 
            f"{price_change:.2f}%",
            help="The last traded price and 24h change"
        )
    with col3:
        st.metric(
            "Funding Rate", 
            f"{funding_rate:.4f}%",
            help="The current funding rate for perpetual contracts"
        )
    with col4:
        st.metric(
            "24h Volume", 
            format_price(float(market_data['quote_volume'].sum())),
            help="Total trading volume in the last 24 hours"
        )

def analyze_order_book(market_analyzer, symbol: str):
    """Analyze order book and return data"""
    try:
        return market_analyzer.analyze_order_book_depth(symbol)
    except Exception as e:
        st.error(f"Error analyzing order book: {str(e)}")
        return None

def display_order_book(market_analyzer, symbol: str):
    """Display order book analysis UI and return data for AI context"""
    order_book = analyze_order_book(market_analyzer, symbol)
    if order_book:
        with st.expander("📊 Order Book Analysis - AI Decision Support", expanded=False):
            # Display buy/sell pressure
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Buy Pressure",
                    f"{order_book['buy_pressure']:.1f}%",
                    help="Current buying pressure in the market"
                )
            with col2:
                st.metric(
                    "Sell Pressure",
                    f"{order_book['sell_pressure']:.1f}%",
                    help="Current selling pressure in the market"
                )

            # Display significant walls
            if order_book['bid_walls'] or order_book['ask_walls']:
                st.markdown("### 🏗️ Significant Order Walls")
                if order_book['bid_walls']:
                    st.markdown("**Buy Walls:**")
                    for wall in order_book['bid_walls']:
                        st.markdown(f"- Price: {format_price(wall['price'])} | Volume: {wall['quantity']:,.2f}")
                if order_book['ask_walls']:
                    st.markdown("**Sell Walls:**")
                    for wall in order_book['ask_walls']:
                        st.markdown(f"- Price: {format_price(wall['price'])} | Volume: {wall['quantity']:,.2f}")

            # Display liquidity zones
            st.markdown("### 💧 Liquidity Zones")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Buy Zones:**")
                for zone in order_book['liquidity_zones']['bids']:
                    st.markdown(f"- Range: {format_price(zone['start_price'])} - {format_price(zone['end_price'])}")
            with col2:
                st.markdown("**Sell Zones:**")
                for zone in order_book['liquidity_zones']['asks']:
                    st.markdown(f"- Range: {format_price(zone['start_price'])} - {format_price(zone['end_price'])}")

            # Display market spread
            st.metric(
                "Market Spread",
                f"{order_book['spread_percentage']:.4f}%",
                help="Current spread between best bid and ask prices"
            )

            st.info("💡 This order book analysis is used by the AI to evaluate market depth and potential support/resistance levels.")

    return order_book

def format_order_book_context(order_book: Dict) -> str:
    """Format raw order book data for AI context"""
    if not order_book:
        return ""
    
    # Get raw bids and asks from the order book data
    bids = order_book.get('bids', [])
    asks = order_book.get('asks', [])
    
    context = "\nOrder Book Raw Data:\n"
    
    # Add raw bid data
    context += "\nBids (Buy Orders):\n"
    for bid in bids[:20]:  # Limit to 20 levels
        context += f"- Price: {format_price(bid['price'])} | Quantity: {bid['quantity']:.8f}\n"
    
    # Add raw ask data
    context += "\nAsks (Sell Orders):\n"
    for ask in asks[:20]:  # Limit to 20 levels
        context += f"- Price: {format_price(ask['price'])} | Quantity: {ask['quantity']:.8f}\n"
    
    # Add basic spread information
    if bids and asks:
        best_bid = bids[0]['price']
        best_ask = asks[0]['price']
        spread = best_ask - best_bid
        spread_percent = (spread / best_bid) * 100
        context += f"\nCurrent Spread: {format_price(spread)} ({spread_percent:.4f}%)\n"
    
    return context

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

        # Get symbol from market data
        if isinstance(market_data, pd.DataFrame):
            if 'symbol' in market_data.columns:
                symbol = market_data['symbol'].iloc[0]
            else:
                symbol = market_data.index.get_level_values('symbol')[0] if 'symbol' in market_data.index.names else "BTCUSDT"
        else:
            symbol = market_data.get('symbol', "BTCUSDT")

        # Create market context string with improved formatting
        mark_price = float(market_data['mark_price'].iloc[-1])
        current_price = float(market_data['last_price'].iloc[-1])
        price_change = float(market_data['price_change_percent'].iloc[-1])
        funding_rate = float(market_data['funding_rate'].iloc[-1])
        volume = float(market_data['quote_volume'].sum())
        
        market_context = f"""
Real Time Market Data (Use it when necessary):

Current Market Data for {symbol}:
    Mark Price: {format_price(mark_price)} (Primary Reference)
    Current Price: {format_price(current_price)} ({price_change:.2f}%)
    Funding Rate: {funding_rate:.4f}%
    24h Volume: {format_price(volume)}
"""
        # Display chat interface with mode indicator
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("💬 Trading Assistant")
        with col2:
            if st.session_state.analysis_mode == "historical":
                st.info("📈 Historical Analysis Mode (1 Year)", icon="📊")
        
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
                # Get 1 year of historical data
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                st.session_state.historical_data = analysis_service.client.get_market_data(
                    symbol=symbol,
                    interval='1d'
                )
            else:
                st.session_state.analysis_mode = "real-time"
                st.session_state.historical_data = None
            
            # Add user message to session state
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)

            # Get market data
            try:
                with st.spinner("Getting market data..."):
                    formatted_data = asyncio.run(get_market_data(
                        st.session_state.prompt_formatter,
                        market_data,
                        symbol
                    ))
                    
                    # Create AI context
                    ai_context = market_context
            except Exception as e:
                print(f"Error getting market data: {str(e)}")
                ai_context = market_context
            
            # Add order book context if available
            if 'order_book_data' in st.session_state and st.session_state.order_book_data:
                ai_context += format_order_book_context(st.session_state.order_book_data)
            
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
                        symbol=symbol
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
