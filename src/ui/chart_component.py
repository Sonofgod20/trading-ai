import streamlit as st
import streamlit.components.v1 as components
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Union
from .chart_renderer import get_chart_html, get_price_metrics_style

def display_tradingview_widget(symbol: str):
    """Display TradingView widget for live chart"""
    tv_symbol = f"BINANCE:{symbol}PERP"
    
    widget_html = f"""
    <div style="width: 100%; height: 600px;">
        <div class="tradingview-widget-container">
            <div id="tradingview_chart"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
            <script type="text/javascript">
            new TradingView.widget({{
                "width": "100%",
                "height": "600",
                "symbol": "{tv_symbol}",
                "interval": "60",
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "1",
                "locale": "en",
                "toolbar_bg": "#f1f3f6",
                "enable_publishing": false,
                "hide_side_toolbar": false,
                "allow_symbol_change": true,
                "container_id": "tradingview_chart",
                "studies": [
                    "RSI@tv-basicstudies",
                    "MACD@tv-basicstudies",
                    "Volume@tv-basicstudies"
                ]
            }});
            </script>
        </div>
    </div>
    """
    components.html(widget_html, height=600)

def format_chart_data(market_data) -> List[Dict]:
    """Format market data for chart display"""
    chart_data = []
    for idx, row in market_data.iterrows():
        chart_data.append({
            'time': int(row.name.timestamp()) if hasattr(row.name, 'timestamp') else int(row.name),
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'close': float(row['close']),
            'volume': float(row['volume']) if 'volume' in row else 0,
        })
    return chart_data

def format_price_lines(price_levels: Optional[Dict]) -> List[Dict]:
    """Format price levels for chart display"""
    price_lines = []
    if price_levels:
        if isinstance(price_levels.get('entry'), (list, tuple)):
            for i, entry in enumerate(price_levels['entry']):
                if entry is not None:
                    price_lines.append({
                        'price': float(entry),
                        'color': '#2196F3',
                        'title': f'Entry {i+1}'
                    })
        elif price_levels.get('entry') is not None:
            price_lines.append({
                'price': float(price_levels['entry']),
                'color': '#2196F3',
                'title': 'Entry'
            })
        
        if isinstance(price_levels.get('tp'), (list, tuple)):
            for i, tp in enumerate(price_levels['tp']):
                if tp is not None:
                    price_lines.append({
                        'price': float(tp),
                        'color': '#4CAF50',
                        'title': f'TP {i+1}'
                    })
        elif price_levels.get('tp') is not None:
            price_lines.append({
                'price': float(price_levels['tp']),
                'color': '#4CAF50',
                'title': 'TP'
            })
        
        if price_levels.get('sl') is not None:
            price_lines.append({
                'price': float(price_levels['sl']),
                'color': '#FF5252',
                'title': 'SL'
            })
    return price_lines

def display_price_metrics(price_levels: Dict):
    """Display price metrics below the chart"""
    st.markdown(get_price_metrics_style(), unsafe_allow_html=True)
    
    cols = st.columns(3)
    
    # Show multiple entries if they exist
    if isinstance(price_levels.get('entry'), (list, tuple)):
        for i, entry in enumerate(price_levels['entry']):
            if entry is not None:
                cols[0].markdown(f"""
                <div class="price-metric">
                    <div class="price-metric-label">Entry {i+1}</div>
                    <div class="price-metric-value">${entry:.8f}</div>
                </div>
                """, unsafe_allow_html=True)
    elif price_levels.get('entry') is not None:
        cols[0].markdown(f"""
        <div class="price-metric">
            <div class="price-metric-label">Entry</div>
            <div class="price-metric-value">${price_levels['entry']:.8f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Show multiple take profits if they exist
    if isinstance(price_levels.get('tp'), (list, tuple)):
        for i, tp in enumerate(price_levels['tp']):
            if tp is not None:
                cols[1].markdown(f"""
                <div class="price-metric">
                    <div class="price-metric-label">Take Profit {i+1}</div>
                    <div class="price-metric-value">${tp:.8f}</div>
                </div>
                """, unsafe_allow_html=True)
    elif price_levels.get('tp') is not None:
        cols[1].markdown(f"""
        <div class="price-metric">
            <div class="price-metric-label">Take Profit</div>
            <div class="price-metric-value">${price_levels['tp']:.8f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Show Stop Loss
    if price_levels.get('sl') is not None:
        cols[2].markdown(f"""
        <div class="price-metric">
            <div class="price-metric-label">Stop Loss</div>
            <div class="price-metric-value">${price_levels['sl']:.8f}</div>
        </div>
        """, unsafe_allow_html=True)

def display_trading_view_chart(market_data, price_levels=None, analysis_data=None):
    """Display market data using Lightweight Charts"""
    try:
        # Get the symbol from market data
        if 'symbol' in market_data.columns:
            symbol = market_data['symbol'].iloc[0]
        else:
            symbol = market_data.index.get_level_values('symbol')[0] if 'symbol' in market_data.index.names else "BTCUSDT"
        
        # Add timeframe selector
        timeframe = st.selectbox(
            "Timeframe",
            ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"],
            index=4  # Default to 1h
        )
        
        # Create unique container ID
        container_id = f"chart_{uuid.uuid4().hex[:8]}"
        
        # Format data for chart
        chart_data = format_chart_data(market_data)
        price_lines = format_price_lines(price_levels)
        
        # Get and display chart HTML
        chart_html = get_chart_html(container_id, chart_data, price_lines, timeframe)
        components.html(chart_html, height=650)
        
        # Display price metrics if available
        if price_levels:
            display_price_metrics(price_levels)

    except Exception as e:
        st.error(f"Error displaying chart: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None
