import streamlit as st
import pandas as pd
from typing import Dict
from src.analysis.market_data.market_analyzer import MarketAnalyzer
import time

def format_price(price: float) -> str:
    """Format price with appropriate decimal places"""
    return f"${price:,.8f}"

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

def analyze_order_book(market_analyzer: MarketAnalyzer, symbol: str):
    """Analyze order book and return data"""
    try:
        return market_analyzer.analyze_order_book_depth(symbol)
    except Exception as e:
        print(f"Error analyzing order book: {str(e)}")
        return None

def display_order_book(market_analyzer: MarketAnalyzer, symbol: str):
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

def update_market_data(analysis_service):
    """Update market data and return context"""
    trading_pairs = analysis_service.client.get_trading_pairs()
    market_context = "\nReal Time Market Data:\n\n"
    
    # Procesar todos los pares con datos completos
    for symbol in trading_pairs:
        try:
            symbol_data = analysis_service.client.get_market_data(symbol=symbol)
            
            if symbol_data is not None and not symbol_data.empty:
                mark_price = float(symbol_data['mark_price'].iloc[-1])
                current_price = float(symbol_data['last_price'].iloc[-1])
                price_change = float(symbol_data['price_change_percent'].iloc[-1])
                funding_rate = float(symbol_data['funding_rate'].iloc[-1])
                volume = float(symbol_data['quote_volume'].sum())
                
                market_context += f"""Market Data for {symbol}:
Mark Price: {format_price(mark_price)} (Primary Reference)
Current Price: {format_price(current_price)} ({price_change:.2f}%)
Funding Rate: {funding_rate:.4f}%
24h Volume: {format_price(volume)}

"""
        except Exception as e:
            print(f"Error getting data for {symbol}: {str(e)}")
            continue
    
    return market_context

def get_market_context(analysis_service, force_update=False):
    """Get market context from cache or update if needed"""
    current_time = time.time()
    
    # Initialize market data at startup
    if 'market_context' not in st.session_state:
        st.session_state.market_context = update_market_data(analysis_service)
        st.session_state.last_update = current_time
        st.session_state.market_history = [
            {
                'timestamp': current_time,
                'context': st.session_state.market_context
            }
        ]
    
    # Add update button in the UI
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button('🔄 Update Market Data'):
            force_update = True
    with col1:
        st.text(f"Last Update: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.session_state.last_update))}")
    
    # Update data if forced or 5 minutes have passed
    if (force_update or 
        current_time - st.session_state.last_update >= 300):  # 300 seconds = 5 minutes
        
        st.session_state.market_context = update_market_data(analysis_service)
        st.session_state.last_update = current_time
        
        # Store historical data
        st.session_state.market_history.append({
            'timestamp': current_time,
            'context': st.session_state.market_context
        })
        
        # Keep only last 24 hours of history
        cutoff_time = current_time - (24 * 60 * 60)
        st.session_state.market_history = [
            h for h in st.session_state.market_history 
            if h['timestamp'] > cutoff_time
        ]
    
    return st.session_state.market_context
