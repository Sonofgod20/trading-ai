from datetime import datetime
from typing import Dict, Optional, Union
import pandas as pd
import streamlit as st

class MarketAnalysisPromptFormatter:
    def __init__(self):
        self.debug = True

    def _log(self, message: str):
        """Log message if debug mode is on"""
        if self.debug:
            print(f"[PromptFormatter] {message}")

    async def format_market_data(self, binance_data: Union[Dict, pd.DataFrame], symbol: str) -> pd.DataFrame:
        """Format Binance market data"""
        try:
            self._log(f"Formatting market data for {symbol}")
            
            if isinstance(binance_data, dict):
                binance_df = pd.DataFrame([binance_data])
            else:
                binance_df = binance_data.copy()
            
            return binance_df
            
        except Exception as e:
            self._log(f"Error formatting market data: {str(e)}")
            st.error("Error formatting market data. Some information may be missing.")
            return binance_data

    async def get_formatted_prompt(self, binance_data: Union[Dict, pd.DataFrame], symbol: str) -> pd.DataFrame:
        """Get the fully formatted market analysis prompt"""
        try:
            self._log("Getting formatted prompt...")
            market_data = await self.format_market_data(binance_data, symbol)
            
            # Log available data for analysis
            self._log(f"Final market data columns: {market_data.columns.tolist()}")
            
            return market_data
            
        except Exception as e:
            self._log(f"Error in get_formatted_prompt: {str(e)}")
            return binance_data
