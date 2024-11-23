import json

def debug_print(title, data):
    """Helper function to print debug information"""
    print(f"\n=== {title} ===")
    print(json.dumps(data, indent=2))
    print("=" * (len(title) + 8))

def extract_chart_data(data):
    """Extract chart data and trading signals from the AI response"""
    try:
        if isinstance(data, str):
            data = json.loads(data)
        
        if not isinstance(data, dict):
            print("Error: data is not a dictionary")
            return [], {}

        debug_print("Received data structure", data)

        chart_data = []
        trading_signals = {}

        if 'chart_data' in data:
            if 'series' in data['chart_data'] and len(data['chart_data']['series']) > 0:
                series = data['chart_data']['series'][0]
                if 'data' in series:
                    chart_data = series['data']
                    debug_print("Extracted chart data", chart_data)

            if 'trading_signals' in data['chart_data']:
                trading_signals = data['chart_data']['trading_signals']
                debug_print("Extracted trading signals", trading_signals)

        return chart_data, trading_signals
    except Exception as e:
        print(f"Error in extract_chart_data: {str(e)}")
        return [], {}

def process_trading_signals(trading_signals) -> list:
    """Convert trading signals to price lines format"""
    try:
        debug_print("Processing trading signals", trading_signals)
        price_lines = []
        
        if not isinstance(trading_signals, dict):
            return []

        # Add support and resistance levels
        if trading_signals.get('support_resistance'):
            # Add support levels
            for level in trading_signals['support_resistance'].get('support_levels', []):
                price_lines.append({
                    'price': level,
                    'color': trading_signals['support_resistance']['line_style']['support']['color'],
                    'lineWidth': trading_signals['support_resistance']['line_style']['support']['lineWidth'],
                    'lineStyle': trading_signals['support_resistance']['line_style']['support']['lineStyle'],
                    'title': 'Support'
                })
            
            # Add resistance levels
            for level in trading_signals['support_resistance'].get('resistance_levels', []):
                price_lines.append({
                    'price': level,
                    'color': trading_signals['support_resistance']['line_style']['resistance']['color'],
                    'lineWidth': trading_signals['support_resistance']['line_style']['resistance']['lineWidth'],
                    'lineStyle': trading_signals['support_resistance']['line_style']['resistance']['lineStyle'],
                    'title': 'Resistance'
                })

        # Add entry zone
        if trading_signals.get('entry_zone'):
            price_lines.extend([
                {
                    'price': trading_signals['entry_zone']['from'],
                    'color': trading_signals['entry_zone']['style']['color'],
                    'lineWidth': trading_signals['entry_zone']['style']['lineWidth'],
                    'lineStyle': trading_signals['entry_zone']['style']['lineStyle'],
                    'title': 'Entry Zone Low'
                },
                {
                    'price': trading_signals['entry_zone']['to'],
                    'color': trading_signals['entry_zone']['style']['color'],
                    'lineWidth': trading_signals['entry_zone']['style']['lineWidth'],
                    'lineStyle': trading_signals['entry_zone']['style']['lineStyle'],
                    'title': 'Entry Zone High'
                }
            ])

        # Add stop loss
        if trading_signals.get('stop_loss'):
            price_lines.append({
                'price': trading_signals['stop_loss']['price'],
                'color': trading_signals['stop_loss']['style']['color'],
                'lineWidth': trading_signals['stop_loss']['style']['lineWidth'],
                'lineStyle': trading_signals['stop_loss']['style']['lineStyle'],
                'title': 'Stop Loss'
            })

        # Add take profit levels
        if trading_signals.get('take_profit_levels'):
            for i, price in enumerate(trading_signals['take_profit_levels']['prices']):
                price_lines.append({
                    'price': price,
                    'color': trading_signals['take_profit_levels']['style']['color'],
                    'lineWidth': trading_signals['take_profit_levels']['style']['lineWidth'],
                    'lineStyle': trading_signals['take_profit_levels']['style']['lineStyle'],
                    'title': f'Take Profit {i+1}'
                })

        debug_print("Generated price lines", price_lines)
        return price_lines
    except Exception as e:
        print(f"Error in process_trading_signals: {str(e)}")
        return []

def get_chart_html(container_id: str, data: dict, price_lines: list, timeframe: str) -> str:
    """Generate the HTML/JavaScript code for the chart"""
    try:
        # Extract chart data and trading signals
        chart_data = data
        
        # Use raw string for JavaScript template literals
        dollar = '$'
        chart_html = f"""
        <div style="width: 100%; height: 600px; padding: 20px; background: linear-gradient(to bottom, #1a1a1a, #000000);">
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500&display=swap" rel="stylesheet">
            <div id="{container_id}" style="width: 100%; height: 100%; border-radius: 10px; overflow: hidden;"></div>
        </div>
        
        <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
        <script>
            const container = document.getElementById('{container_id}');
            const chart = LightweightCharts.createChart(container, {{
                layout: {{
                    background: {{ 
                        type: 'gradient',
                        gradient: {{
                            type: 'linear',
                            coordinates: {{
                                0: 0,
                                1: 1,
                            }},
                            colors: [
                                {{offset: 0, color: '#1a1a1a'}},
                                {{offset: 1, color: '#000000'}}
                            ],
                        }},
                    }},
                    textColor: '#e0e0e0',
                    fontSize: 12,
                    fontFamily: "'Roboto', sans-serif",
                }},
                grid: {{
                    vertLines: {{ 
                        color: 'rgba(42, 46, 57, 0.3)',
                        style: 1,
                    }},
                    horzLines: {{ 
                        color: 'rgba(42, 46, 57, 0.3)',
                        style: 1,
                    }},
                }},
                crosshair: {{
                    mode: LightweightCharts.CrosshairMode.Normal,
                    vertLine: {{
                        color: 'rgba(224, 227, 235, 0.4)',
                        style: 1,
                        width: 1,
                        labelBackgroundColor: '#2962FF',
                    }},
                    horzLine: {{
                        color: 'rgba(224, 227, 235, 0.4)',
                        style: 1,
                        width: 1,
                        labelBackgroundColor: '#2962FF',
                    }},
                }},
                rightPriceScale: {{
                    borderColor: 'rgba(197, 203, 206, 0.4)',
                    borderVisible: true,
                    scaleMargins: {{
                        top: 0.2,
                        bottom: 0.2,
                    }},
                    textColor: '#e0e0e0',
                }},
                timeScale: {{
                    borderColor: 'rgba(197, 203, 206, 0.4)',
                    borderVisible: true,
                    timeVisible: true,
                    secondsVisible: false,
                    tickMarkFormatter: (time, tickMarkType, locale) => {{
                        const date = new Date(time * 1000);
                        const format = {{ 
                            '1m': {{month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'}},
                            '5m': {{month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'}},
                            '15m': {{month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'}},
                            '30m': {{month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'}},
                            '1h': {{month: 'short', day: 'numeric', hour: '2-digit'}},
                            '4h': {{month: 'short', day: 'numeric', hour: '2-digit'}},
                            '1d': {{year: 'numeric', month: 'short', day: 'numeric'}},
                            '1w': {{year: 'numeric', month: 'short', day: 'numeric'}}
                        }}['{timeframe}'];
                        return date.toLocaleDateString(locale, format);
                    }},
                }},
            }});

            // Create candlestick series
            const candlestickSeries = chart.addCandlestickSeries({{
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderVisible: false,
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350',
                priceFormat: {{
                    type: 'price',
                    precision: 2,
                    minMove: 0.01,
                }},
            }});

            // Add volume series
            const volumeSeries = chart.addHistogramSeries({{
                color: '#26a69a',
                priceFormat: {{
                    type: 'volume',
                }},
                priceScaleId: '',
                scaleMargins: {{
                    top: 0.8,
                    bottom: 0,
                }},
            }});

            // Set the data
            const chartData = {json.dumps(chart_data)};
            console.log('Chart Data:', chartData);  // Debug log
            candlestickSeries.setData(chartData);

            // Set volume data
            const volumeData = chartData.map(d => ({{
                time: d.time,
                value: d.volume || 0,
                color: d.close >= d.open ? '#26a69a50' : '#ef535050',
            }}));
            volumeSeries.setData(volumeData);

            // Add price lines
            const priceLines = {json.dumps(price_lines)};
            console.log('Price Lines:', priceLines);  // Debug log
            priceLines.forEach(line => {{
                candlestickSeries.createPriceLine({{
                    price: line.price,
                    color: line.color,
                    lineWidth: line.lineWidth || 2,
                    lineStyle: line.lineStyle || LightweightCharts.LineStyle.Dashed,
                    axisLabelVisible: true,
                    title: line.title,
                }});
            }});

            // Handle window resize
            const handleResize = () => {{
                chart.applyOptions({{
                    width: container.clientWidth,
                    height: container.clientHeight,
                }});
            }};

            window.addEventListener('resize', handleResize);

            // Add tooltip
            const toolTipWidth = 80;
            const toolTipHeight = 80;
            const toolTipMargin = 15;

            // Create and style the tooltip element
            const toolTip = document.createElement('div');
            toolTip.style = `
                width: 96px;
                height: 80px;
                position: absolute;
                display: none;
                padding: 8px;
                box-sizing: border-box;
                font-size: 12px;
                color: #fff;
                background-color: rgba(0, 0, 0, 0.8);
                border-radius: 4px;
                font-family: 'Roboto', sans-serif;
                z-index: 1000;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            `;
            container.appendChild(toolTip);

            // update tooltip
            chart.subscribeCrosshairMove(param => {{
                if (
                    param.point === undefined ||
                    !param.time ||
                    param.point.x < 0 ||
                    param.point.x > container.clientWidth ||
                    param.point.y < 0 ||
                    param.point.y > container.clientHeight
                ) {{
                    toolTip.style.display = 'none';
                    return;
                }}

                const data = param.seriesData.get(candlestickSeries);
                const volume = param.seriesData.get(volumeSeries);

                if (!data) {{
                    toolTip.style.display = 'none';
                    return;
                }}

                toolTip.style.display = 'block';
                const price = data;
                
                toolTip.innerHTML = `
                    <div style="margin-bottom: 4px;">
                        <span style="color: #9B7DFF">O:</span> <span style="color: #e0e0e0">${dollar}${{price.open.toFixed(2)}}</span>
                    </div>
                    <div style="margin-bottom: 4px">
                        <span style="color: #9B7DFF">H:</span> <span style="color: #e0e0e0">${dollar}${{price.high.toFixed(2)}}</span>
                    </div>
                    <div style="margin-bottom: 4px">
                        <span style="color: #9B7DFF">L:</span> <span style="color: #e0e0e0">${dollar}${{price.low.toFixed(2)}}</span>
                    </div>
                    <div style="margin-bottom: 4px">
                        <span style="color: #9B7DFF">C:</span> <span style="color: #e0e0e0">${dollar}${{price.close.toFixed(2)}}</span>
                    </div>
                    <div>
                        <span style="color: #9B7DFF">Vol:</span> <span style="color: #e0e0e0">${dollar}${{volume?.value?.toLocaleString() || 0}}</span>
                    </div>
                `;

                const coordinate = param.point;
                let left = coordinate.x + toolTipMargin;
                if (left > container.clientWidth - toolTipWidth) {{
                    left = coordinate.x - toolTipMargin - toolTipWidth;
                }}

                let top = coordinate.y + toolTipMargin;
                if (top > container.clientHeight - toolTipHeight) {{
                    top = coordinate.y - toolTipHeight - toolTipMargin;
                }}

                toolTip.style.left = left + 'px';
                toolTip.style.top = top + 'px';
            }});

            // Fit content and handle initial resize
            chart.timeScale().fitContent();
            handleResize();
        </script>
        """
        return chart_html
    except Exception as e:
        print(f"Error in get_chart_html: {str(e)}")
        return f"<div>Error displaying chart: {str(e)}</div>"

def get_price_metrics_style() -> str:
    """Get the CSS styles for price metrics"""
    return """
    <style>
    .price-metric {
        background: rgba(26, 26, 26, 0.8);
        padding: 15px;
        border-radius: 8px;
        margin: 5px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .price-metric-label {
        color: #9B7DFF;
        font-size: 14px;
        margin-bottom: 5px;
        font-family: 'Roboto', sans-serif;
    }
    .price-metric-value {
        color: #ffffff;
        font-size: 18px;
        font-weight: 500;
        font-family: 'Roboto', sans-serif;
    }
    </style>
    """
