import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime

def format_trading_view_data(market_data, price_levels=None, analysis_data=None):
    """Format market data for TradingView Lightweight Charts"""
    chart_data = []
    price_lines = []
    trend_lines = []
    patterns = []
    zones = []

    try:
        # Format candlestick data
        for idx, row in market_data.iterrows():
            # Convert pandas timestamp to Unix timestamp
            if isinstance(row['timestamp'], pd.Timestamp):
                timestamp = int(row['timestamp'].timestamp())
            elif isinstance(row['timestamp'], str):
                timestamp = int(pd.Timestamp(row['timestamp']).timestamp())
            else:
                timestamp = int(row['timestamp'])

            # Ensure all price values are float
            candle = {
                'time': timestamp,
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
            }
            chart_data.append(candle)

        # Sort data by timestamp
        chart_data.sort(key=lambda x: x['time'])

        # Format price levels
        if price_levels:
            level_colors = {
                'entry': '#2196F3',  # Blue
                'tp': '#4CAF50',     # Green
                'sl': '#F44336',     # Red
            }
            
            for level_name, price in price_levels.items():
                if level_name not in ['direction', 'confidence']:
                    try:
                        price_lines.append({
                            'price': float(price),
                            'color': level_colors.get(level_name, '#FFFFFF'),
                            'title': level_name.upper(),
                        })
                    except (TypeError, ValueError) as e:
                        print(f"Error converting price level {level_name}: {str(e)}")

        # Format analysis data if available
        if analysis_data:
            # Add trend lines
            if 'trend_lines' in analysis_data:
                for trend in analysis_data['trend_lines']:
                    trend_lines.append({
                        'points': [
                            {'time': int(p['time']), 'value': float(p['price'])}
                            for p in trend['points']
                        ],
                        'color': trend.get('color', '#FFFFFF')
                    })

            # Add patterns
            if 'patterns' in analysis_data:
                for pattern in analysis_data['patterns']:
                    patterns.append({
                        'points': [
                            {'time': int(p['time']), 'value': float(p['price'])}
                            for p in pattern['points']
                        ],
                        'color': pattern.get('color', '#FFFFFF'),
                        'style': pattern.get('style', 0)
                    })

            # Add zones
            if 'zones' in analysis_data:
                for zone in analysis_data['zones']:
                    zones.append({
                        'points': [
                            {'time': int(p['time']), 'value': float(p['price'])}
                            for p in zone['points']
                        ],
                        'color': zone.get('color', 'rgba(76, 175, 80, 0.2)')  # Semi-transparent green
                    })

        return chart_data, price_lines, trend_lines, patterns, zones

    except Exception as e:
        print(f"Error formatting data: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return [], [], [], [], []
