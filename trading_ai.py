import streamlit as st
# Set page config must be the first Streamlit command
st.set_page_config(page_title="Crypto Market Chat", layout="wide")

import os
from dotenv import load_dotenv
from binance_futures import BinanceFuturesClient
from src.trading.analysis_service import AnalysisService
from src.analysis.market_data.market_analyzer import MarketAnalyzer
from src.ui.ui_components import (
    display_market_metrics,
    display_order_book,
    display_realtime_chat
)
from datetime import datetime, timedelta
import pandas as pd
import base64
import io
import asyncio

# Load environment variables
load_dotenv()

# Initialize Binance client with testnet keys
binance = BinanceFuturesClient(
    api_key="2319f25b456c8ab4f5b5ef7e3",
    api_secret="f2c4d56b7c8d9e0a1b2c3d4"
)

# Initialize market analyzer
market_analyzer = MarketAnalyzer(binance)

# Initialize chatbase service
try:
    api_key = os.getenv('CHATBASE_API_KEY')
    chatbot_id = os.getenv('CHATBASE_CHATBOT_ID')
    
    if not api_key or not chatbot_id:
        st.warning("Chat service not available - credentials not found")
        analysis_service = None
    else:
        analysis_service = AnalysisService(
            binance_client=binance,
            chatbase_api_key=api_key,
            chatbase_chatbot_id=chatbot_id
        )
except Exception as e:
    st.error(f"Error initializing chat service: {str(e)}")
    analysis_service = None

def check_binance_connection():
    """Check if Binance API is accessible"""
    try:
        # Try to get server time as a simple connection test
        binance._make_request('time')
        return True
    except Exception as e:
        print(f"Binance connection error: {str(e)}")
        return False

def get_download_link(df: pd.DataFrame, symbol: str, filename: str):
    """Generate a download link for the dataframe"""
    csv = df.to_csv(index=True)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download {symbol} Historical Data (CSV)</a>'
    return href

def save_to_txt(data: pd.DataFrame, symbol: str, file_path: str):
    """Save historical data to a text file"""
    try:
        with open(file_path, 'w') as f:
            # Write header
            f.write(f"{symbol} Historical Data (3 Years)\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Write summary statistics
            f.write("Summary Statistics:\n")
            f.write("-" * 50 + "\n")
            metrics = {
                'Total Days': len(data),
                'Date Range': f"{data.index.min().strftime('%Y-%m-%d')} to {data.index.max().strftime('%Y-%m-%d')}",
                'Highest Price': f"${data['high'].max():.2f}",
                'Lowest Price': f"${data['low'].min():.2f}",
                'Average Price': f"${data['close'].mean():.2f}",
                'Total Volume': f"${data['volume'].sum():.2f}",
                'Average Daily Volume': f"${data['volume'].mean():.2f}"
            }
            
            for metric, value in metrics.items():
                f.write(f"{metric}: {value}\n")
            
            # Write historical data
            f.write("\nHistorical Data:\n")
            f.write("-" * 100 + "\n")
            f.write(f"{'Date':<12} {'Open':>12} {'High':>12} {'Low':>12} {'Close':>12} {'Volume':>15} {'Trades':>10}\n")
            f.write("-" * 100 + "\n")
            
            # Write all data rows, starting from oldest to newest
            for index, row in data.sort_index().iterrows():
                f.write(f"{index.strftime('%Y-%m-%d'):<12} "
                       f"${row['open']:>10.2f} "
                       f"${row['high']:>10.2f} "
                       f"${row['low']:>10.2f} "
                       f"${row['close']:>10.2f} "
                       f"${row['volume']:>13.2f} "
                       f"{int(row['trades']):>10}\n")
        return True
    except Exception as e:
        print(f"Error saving to txt: {str(e)}")
        return False

def download_historical_data(symbol: str):
    """Download and save 3 years of historical data for a symbol"""
    try:
        with st.spinner(f"⏳ Downloading historical data for {symbol}..."):
            # Create directory if it doesn't exist
            save_dir = os.path.join('data', 'market_data', 'historical')
            os.makedirs(save_dir, exist_ok=True)
            
            # Get 3 years of daily data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1095)  # 3 years
            
            st.info(f"📊 Fetching {symbol} data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            historical_data = binance.get_historical_klines(
                symbol=symbol,
                interval='1d',
                start_time=start_date,
                end_time=end_date
            )
            
            if historical_data is not None:
                # Save to text file
                file_path = os.path.join(save_dir, f'{symbol}_3y_history.txt')
                if save_to_txt(historical_data, symbol, file_path):
                    st.success(f"✅ Historical data saved to {file_path}")
                    
                    # Create download link for CSV
                    st.markdown(get_download_link(historical_data, symbol, f"{symbol}_historical_data.csv"), unsafe_allow_html=True)
                    return True
            return False
    except Exception as e:
        st.error(f"❌ Error downloading historical data: {str(e)}")
        return False

def download_all_historical_data():
    """Download historical data for all trading pairs"""
    success_count = 0
    failed_pairs = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_pairs = len(binance.allowed_pairs)
    
    for i, symbol in enumerate(binance.allowed_pairs):
        try:
            status_text.text(f"Processing {symbol} ({i+1}/{total_pairs})")
            if download_historical_data(symbol):
                success_count += 1
            else:
                failed_pairs.append(symbol)
        except Exception as e:
            st.error(f"Error downloading {symbol}: {str(e)}")
            failed_pairs.append(symbol)
        
        # Update progress bar
        progress_bar.progress((i + 1) / total_pairs)
    
    return success_count, failed_pairs

def main():
    """Display the main page"""
    st.title("Trading AI")
    st.markdown("---")

    # Backend Status Indicators
    with st.sidebar:
        st.header("System Status")
        
        # Binance Connection Status
        binance_status = "🟢 Connected" if check_binance_connection() else "🔴 Disconnected"
        st.markdown(f"**Binance API:** {binance_status}")
        
        # AI Service Status
        ai_status = "🟢 Connected" if analysis_service else "🔴 Disconnected"
        st.markdown(f"**AI Service:** {ai_status}")
        
        st.markdown("---")
        st.header("Market Settings")

    # Get trading pairs
    trading_pairs = binance.get_trading_pairs()
    symbol = st.sidebar.selectbox("Select Trading Pair", trading_pairs)
    
    # Select timeframe
    timeframe = st.sidebar.selectbox(
        "Chart Timeframe",
        ['1m', '5m', '15m', '1h', '4h', '1d'],
        index=3  # Default to 1h
    )
    
    # Add download buttons with status indicators
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("📥 Download Historical"):
            download_historical_data(symbol)
    
    with col2:
        if st.button("📥 Download All"):
            with st.spinner("Downloading historical data for all pairs..."):
                success_count, failed_pairs = download_all_historical_data()
                if failed_pairs:
                    st.warning(f"Downloaded {success_count} pairs. Failed: {', '.join(failed_pairs)}")
                else:
                    st.success(f"Successfully downloaded all {success_count} pairs!")

    # Get market data with status indicator
    with st.spinner(f"📊 Fetching market data be patient..."):
        market_data = binance.get_market_data(symbol, timeframe)
        if market_data is not None:
            st.success(f"✅ Market data loaded for all coins")
            
            # Add symbol to market_data
            market_data['symbol'] = symbol
            
            # Display market metrics
            display_market_metrics(market_data)
            
            # Get and store order book data
            order_book = display_order_book(market_analyzer, symbol)
            if 'order_book_data' not in st.session_state:
                st.session_state.order_book_data = {}
            st.session_state.order_book_data = order_book

            st.markdown("---")
            
            # Display chart and chat interface
            if analysis_service:
                with st.spinner(f"🤖 Be patient, each coin is being analyzed..."):
                    display_realtime_chat(market_data, analysis_service)
            else:
                st.error("Chat unavailable - service not initialized")
        else:
            st.error(f"❌ Failed to fetch market data for {symbol}")

# Run the app
if __name__ == "__main__":
    main()

# Footer
st.markdown("---")
