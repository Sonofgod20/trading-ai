import streamlit as st
import streamlit.components.v1 as components
import json
from datetime import datetime

def display_tradingview_chart(symbol: str, price_levels=None, analysis_data=None):
    """Display TradingView Advanced Chart widget"""
    try:
        # Configurar el widget con las opciones necesarias
        widget_html = f"""
        <div class="tradingview-widget-container">
            <div id="tradingview_chart"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
            <script type="text/javascript">
            new TradingView.widget({{
                "width": "100%",
                "height": 500,
                "symbol": "{symbol}",
                "interval": "D",
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "1",
                "locale": "en",
                "toolbar_bg": "#f1f3f6",
                "enable_publishing": false,
                "hide_side_toolbar": false,
                "allow_symbol_change": true,
                "studies": [
                    "MASimple@tv-basicstudies",
                    "RSI@tv-basicstudies"
                ],
                "container_id": "tradingview_chart",
                "show_popup_button": true,
                "popup_width": "1000",
                "popup_height": "650"
            }});
            </script>
        </div>
        """

        # Mostrar el widget
        components.html(widget_html, height=500)

        # Si hay niveles de precio, mostrarlos en una tabla debajo del gráfico
        if price_levels:
            col1, col2, col3 = st.columns(3)
            if 'entry' in price_levels:
                col1.metric("Entry", f"${price_levels['entry']:.2f}")
            if 'tp' in price_levels:
                col2.metric("Take Profit", f"${price_levels['tp']:.2f}")
            if 'sl' in price_levels:
                col3.metric("Stop Loss", f"${price_levels['sl']:.2f}")

    except Exception as e:
        st.error(f"Error displaying TradingView chart: {str(e)}")
        return None

def format_symbol_for_tradingview(symbol: str) -> str:
    """Format symbol for TradingView (e.g., 'BTCUSDT' -> 'BINANCE:BTCUSDT')"""
    return f"BINANCE:{symbol}"
