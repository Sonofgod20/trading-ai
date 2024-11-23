# Trading AI

An advanced trading application that uses artificial intelligence to analyze cryptocurrency markets in real-time.

## Key Features

### 1. Intelligent Market Analysis
- Historical and real-time data analysis
- Japanese candlestick pattern detection
- Advanced technical indicator calculations
  - Moving averages
  - Relative Strength Index (RSI)
  - Bollinger Bands
  - MACD Oscillators

### 2. Risk Management
- Automatic risk assessment per trade
- Stop-loss and take-profit calculation
- Market volatility analysis
- Open position tracking

### 3. Trading Strategies
- Multiple predefined strategies
- Strategy conversion and customization
- Strategy backtesting
- Trading parameter optimization

### 4. Exchange Integration
- Direct connection with Binance Futures
- Automated trade execution
- Real-time position tracking

### 5. Data Visualization
- Interactive TradingView charts
- Custom UI components
- Historical data visualization
- Graphical representation of indicators

### 6. AI Assistance
- AI chat for trading queries
- Conversational market analysis
- Data-driven recommendations

## Technologies

- Python
- Streamlit
- TradingView Widgets
- Binance API
- Machine Learning
- Data Analysis

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Sonofgod20/trading-ai.git
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
Create a `.env` file with:
```
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key
```

4. Run the application:
```bash
streamlit run trading_ai.py
```

## Usage

1. Select a trading pair
2. Explore real-time technical analysis
3. Consult strategies with AI Assistant
4. Monitor and execute trades with precision

## Project Structure

- `src/analysis/`: Market analysis modules
- `src/trading/`: Trade execution logic
- `src/ui/`: User interface components
- `models/`: Knowledge and strategy models
- `data/`: Historical data storage

## License

MIT License
