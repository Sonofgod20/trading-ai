import streamlit as st
import pandas as pd
from typing import Dict, Optional
from src.trading.analysis_parser import AnalysisParser
from datetime import datetime, timedelta
from src.analysis.market_data.market_analyzer import MarketAnalyzer

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
    """Format order book data for AI context"""
    if not order_book:
        return ""
    
    context = "\nOrder Book Analysis:\n"
    context += f"- Buy Pressure: {order_book['buy_pressure']:.1f}%\n"
    context += f"- Sell Pressure: {order_book['sell_pressure']:.1f}%\n"
    context += f"- Market Spread: {order_book['spread_percentage']:.4f}%\n"
    
    if order_book['bid_walls']:
        context += "\nBuy Walls:\n"
        for wall in order_book['bid_walls']:
            context += f"- Price: {format_price(wall['price'])} | Volume: {wall['quantity']:,.2f}\n"
    
    if order_book['ask_walls']:
        context += "\nSell Walls:\n"
        for wall in order_book['ask_walls']:
            context += f"- Price: {format_price(wall['price'])} | Volume: {wall['quantity']:,.2f}\n"
    
    context += "\nLiquidity Zones:\n"
    context += "Buy Zones:\n"
    for zone in order_book['liquidity_zones']['bids']:
        context += f"- Range: {format_price(zone['start_price'])} - {format_price(zone['end_price'])}\n"
    
    context += "Sell Zones:\n"
    for zone in order_book['liquidity_zones']['asks']:
        context += f"- Range: {format_price(zone['start_price'])} - {format_price(zone['end_price'])}\n"
    
    return context

def display_realtime_chat(market_data: Dict, analysis_service):
    """Display real-time chat interface with market data context"""
    try:
        # Initialize chat history and states in session state if not exists
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'analysis_mode' not in st.session_state:
            st.session_state.analysis_mode = "real-time"
        if 'historical_data' not in st.session_state:
            st.session_state.historical_data = None

        # Add CSS for TradingView-style chat layout
        st.markdown("""
        <style>
        /* Main container adjustments */
        .main .block-container {
            padding-bottom: 80px;
        }
        
        /* Chat input overlay styling */
        section[data-testid="stChatInput"] {
            position: sticky !important;
            bottom: 0;
            background: rgba(19, 23, 34, 0.9) !important;
            backdrop-filter: blur(10px);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            margin: 0;
            padding: 1rem 3rem;
            z-index: 999;
            box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.3);
        }
        
        section[data-testid="stChatInput"] > div {
            max-width: 1000px;
            margin: 0 auto;
        }
        
        section[data-testid="stChatInput"] input {
            border: 1px solid rgba(255, 255, 255, 0.1);
            background: rgba(30, 34, 45, 0.9);
            padding: 0.75rem 1rem;
            border-radius: 6px;
        }
        
        section[data-testid="stChatInput"] input:focus {
            border-color: rgba(55, 131, 255, 0.6);
            box-shadow: 0 0 0 1px rgba(55, 131, 255, 0.3);
        }
        
        /* Chat messages styling */
        .stChatMessage {
            background: rgba(30, 34, 45, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            backdrop-filter: blur(5px);
        }
        
        .stChatMessage:hover {
            background: rgba(30, 34, 45, 0.7);
        }
        
        /* Main content wrapper */
        .main-content {
            max-width: 1200px;
            margin: 0 auto;
            padding: 1rem 0;
        }
        
        /* Ensure proper spacing */
        .element-container {
            margin-bottom: 1rem;
        }
        
        .stMarkdown {
            margin-bottom: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)

        # Create market context string with improved formatting
        mark_price = float(market_data['mark_price'].iloc[-1])
        current_price = float(market_data['last_price'].iloc[-1])
        price_change = float(market_data['price_change_percent'].iloc[-1])
        funding_rate = float(market_data['funding_rate'].iloc[-1])
        volume = float(market_data['quote_volume'].sum())
        
        market_context = f"""
Current Market Data:
- Mark Price: {format_price(mark_price)} (Primary Reference)
- Current Price: {format_price(current_price)} ({price_change:.2f}%)
- Funding Rate: {funding_rate:.4f}%
- 24h Volume: {format_price(volume)}
"""
        # Get symbol from market data
        if 'symbol' in market_data.columns:
            symbol = market_data['symbol'].iloc[0]
        else:
            symbol = market_data.index.get_level_values('symbol')[0] if 'symbol' in market_data.index.names else "BTCUSDT"

        # Main container for the entire interface
        main_container = st.container()
        
        with main_container:
            # Display chat interface with mode indicator
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader("💬 Trading Assistant")
            with col2:
                if st.session_state.analysis_mode == "historical":
                    st.info("📈 Historical Analysis Mode (1 Year)", icon="📊")
            
            # Wrap main content in a div for styling
            st.markdown('<div class="main-content">', unsafe_allow_html=True)
            
            # Display chat history
            chat_container = st.container()
            with chat_container:
                for message in st.session_state.chat_history:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
            
            st.markdown('</div>', unsafe_allow_html=True)

            # Chat input with TradingView-style
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
                
                # Add user message to chat history
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                
                # Display user message
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Prepare AI context with market data
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
- Yearly High: {format_price(year_high)}
- Yearly Low: {format_price(year_low)}
- Year Open: {format_price(year_open)}
- Year Close: {format_price(year_close)}
- Year Change: {year_change:.2f}%
"""
                    ai_context = f"{historical_context}\n{market_context}"
                
                ai_context += f"\nUser Question: {prompt}"
                
                # Get AI response with loading indicator
                try:
                    with st.spinner("🤖 AI is analyzing the market..."):
                        response = analysis_service.chat(
                            messages=[{"role": "user", "content": ai_context}],
                            system_prompt="""You are a real-time trading assistant with access to current market data. 
                            Analyze the provided market context and answer questions about trading opportunities, 
                            market conditions, and potential strategies. Be precise and data-driven in your responses.
                            Always reference Mark Price as the primary price indicator for your analysis.
                            When order book data is available, use it to identify key support/resistance levels,
                            market depth, and potential price action based on buy/sell walls and liquidity zones."""
                        )
                    
                    # Add AI response to chat history
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    
                    # Display AI response
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
