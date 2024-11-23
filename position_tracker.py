import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from src.analysis.trading_analyzer import TradingAnalyzer

class PositionTracker:
    def __init__(self, binance_client):
        self.binance_client = binance_client
        self.positions_file = 'data/positions.json'
        self.ensure_data_directory()
        self.positions = self.load_positions()
        self.migrate_positions()
        self.trading_analyzer = TradingAnalyzer(binance_client)
        self.ai_monitoring_active = False

    def ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs('data', exist_ok=True)

    def migrate_positions(self):
        """Migrate existing positions to new format"""
        for position in self.positions:
            # Add new fields if they don't exist
            if 'exit_price' not in position:
                position['exit_price'] = None
            if 'exit_time' not in position:
                position['exit_time'] = None
            if 'ai_recommendations' not in position:
                position['ai_recommendations'] = []
        self.save_positions()

    def load_positions(self):
        """Load positions from file"""
        try:
            if os.path.exists(self.positions_file):
                with open(self.positions_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            st.error(f"Error loading positions: {str(e)}")
            return []

    def save_positions(self):
        """Save positions to file"""
        try:
            with open(self.positions_file, 'w') as f:
                json.dump(self.positions, f)
        except Exception as e:
            st.error(f"Error saving positions: {str(e)}")

    def analyze_position(self, position):
        """Perform AI analysis on a position"""
        try:
            analysis = self.trading_analyzer.perform_complete_analysis(position['symbol'])
            if not analysis:
                return None

            current_price = float(analysis['order_book_analysis']['mid_price'])
            entry_price = float(position['entry_price'])
            direction = position['direction']
            
            recommendations = {
                'timestamp': datetime.now().isoformat(),
                'current_price': current_price,
                'actions': [],
                'confidence': analysis['trade_signals']['confidence_score']
            }

            # Analyze potential loss/profit scenarios
            if direction == 'LONG':
                unrealized_pnl = (current_price - entry_price) * float(position['size'])
            else:
                unrealized_pnl = (entry_price - current_price) * float(position['size'])

            # Dynamic SL/TP recommendations based on market conditions
            if analysis['trade_signals']['recommended_direction']:
                if direction == 'LONG':
                    if analysis['trade_signals']['recommended_direction'] == 'long':
                        # Market still bullish, consider adjusting TP higher
                        if analysis['trade_signals']['take_profit'] and float(analysis['trade_signals']['take_profit']) > float(position['take_profit']):
                            recommendations['actions'].append({
                                'type': 'ADJUST_TP',
                                'new_level': analysis['trade_signals']['take_profit'],
                                'reason': 'Market showing continued bullish strength'
                            })
                    else:
                        # Market turned bearish, consider tightening SL
                        if unrealized_pnl > 0:
                            new_sl = max(entry_price, current_price * 0.995)
                            recommendations['actions'].append({
                                'type': 'ADJUST_SL',
                                'new_level': new_sl,
                                'reason': 'Protect profits as market sentiment shifts bearish'
                            })
                else:  # SHORT position
                    if analysis['trade_signals']['recommended_direction'] == 'short':
                        # Market still bearish, consider adjusting TP lower
                        if analysis['trade_signals']['take_profit'] and float(analysis['trade_signals']['take_profit']) < float(position['take_profit']):
                            recommendations['actions'].append({
                                'type': 'ADJUST_TP',
                                'new_level': analysis['trade_signals']['take_profit'],
                                'reason': 'Market showing continued bearish strength'
                            })
                    else:
                        # Market turned bullish, consider tightening SL
                        if unrealized_pnl > 0:
                            new_sl = min(entry_price, current_price * 1.005)
                            recommendations['actions'].append({
                                'type': 'ADJUST_SL',
                                'new_level': new_sl,
                                'reason': 'Protect profits as market sentiment shifts bullish'
                            })

            # Risk management recommendations
            risk_percent = abs(unrealized_pnl) / (float(position['size']) * entry_price) * 100
            if risk_percent > 2:  # If potential loss exceeds 2%
                recommendations['actions'].append({
                    'type': 'RISK_WARNING',
                    'message': f'Position showing {risk_percent:.1f}% loss. Consider closing to limit risk.',
                    'severity': 'HIGH'
                })

            # Volume analysis for potential market moves
            if analysis['volume_profile']:
                poc_price = float(analysis['volume_profile']['poc'])
                if abs((current_price - poc_price) / poc_price) < 0.001:  # Price near POC
                    recommendations['actions'].append({
                        'type': 'VOLUME_ALERT',
                        'message': 'Price near high volume node, expect potential reversal or continuation',
                        'severity': 'MEDIUM'
                    })

            return recommendations

        except Exception as e:
            st.error(f"Error in AI analysis: {str(e)}")
            return None

    def update_positions(self):
        """Update all positions with current market data and AI analysis"""
        for position in self.positions:
            if position['status'] == 'OPEN':
                # Get current market data
                market_data = self.binance_client.get_market_data(position['symbol'])
                if market_data is not None:
                    current_price = float(market_data['last_price'].iloc[-1])
                    
                    # Calculate PnL
                    entry_price = float(position['entry_price'])
                    size = float(position['size'])
                    
                    if position['direction'] == 'LONG':
                        pnl = (current_price - entry_price) * size
                    else:
                        pnl = (entry_price - current_price) * size
                    
                    position['pnl'] = pnl
                    position['last_update'] = datetime.now().isoformat()
                    
                    # Check if stop loss or take profit hit
                    if position['direction'] == 'LONG':
                        if current_price <= float(position['stop_loss']):
                            position['status'] = 'CLOSED_SL'
                            position['exit_price'] = float(position['stop_loss'])
                            position['exit_time'] = datetime.now().isoformat()
                        elif current_price >= float(position['take_profit']):
                            position['status'] = 'CLOSED_TP'
                            position['exit_price'] = float(position['take_profit'])
                            position['exit_time'] = datetime.now().isoformat()
                    else:
                        if current_price >= float(position['stop_loss']):
                            position['status'] = 'CLOSED_SL'
                            position['exit_price'] = float(position['stop_loss'])
                            position['exit_time'] = datetime.now().isoformat()
                        elif current_price <= float(position['take_profit']):
                            position['status'] = 'CLOSED_TP'
                            position['exit_price'] = float(position['take_profit'])
                            position['exit_time'] = datetime.now().isoformat()

                    # Perform AI analysis if monitoring is active
                    if self.ai_monitoring_active:
                        recommendations = self.analyze_position(position)
                        if recommendations:
                            position['ai_recommendations'] = position.get('ai_recommendations', [])
                            position['ai_recommendations'].append(recommendations)
        
        self.save_positions()

    def display_ai_recommendations(self, position):
        """Display AI recommendations for a position"""
        if position.get('ai_recommendations'):
            latest_rec = position['ai_recommendations'][-1]
            
            # Display AI confidence
            st.metric("AI Confidence", f"{latest_rec['confidence']:.1f}%")
            
            # Display recommended actions
            for action in latest_rec['actions']:
                if action['type'] in ['ADJUST_SL', 'ADJUST_TP']:
                    st.warning(f"💡 Recommended {action['type']}: ${float(action['new_level']):,.2f}")
                    st.text(f"Reason: {action['reason']}")
                    
                    # Add buttons to apply recommendations
                    if st.button(f"Apply {action['type']}", key=f"{action['type']}_{position['symbol']}"):
                        if action['type'] == 'ADJUST_SL':
                            position['stop_loss'] = action['new_level']
                        else:
                            position['take_profit'] = action['new_level']
                        self.save_positions()
                        st.success(f"{action['type']} adjusted successfully!")
                
                elif action['type'] == 'RISK_WARNING':
                    st.error(f"⚠️ {action['message']}")
                
                elif action['type'] == 'VOLUME_ALERT':
                    st.info(f"📊 {action['message']}")

    def display_positions(self):
        """Display positions in Streamlit"""
        st.subheader("📊 Position Tracker")
        
        # AI Monitoring Toggle
        self.ai_monitoring_active = st.toggle("🤖 AI Position Monitoring", self.ai_monitoring_active)
        if self.ai_monitoring_active:
            st.info("AI monitoring is active. Positions will be analyzed in real-time.")
        
        # Summary metrics
        if self.positions:
            total_pnl = sum(float(p['pnl']) for p in self.positions)
            open_positions = sum(1 for p in self.positions if p['status'] == 'OPEN')
            closed_positions = sum(1 for p in self.positions if p['status'] != 'OPEN')
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total P&L", f"${total_pnl:,.2f}")
            with col2:
                st.metric("Open Positions", open_positions)
            with col3:
                st.metric("Closed Positions", closed_positions)

        # Update button
        if st.button("🔄 Update Positions"):
            self.update_positions()
            st.success("Positions updated!")
        
        # Display open positions
        st.subheader("Open Positions")
        open_pos = [p for p in self.positions if p['status'] == 'OPEN']
        if open_pos:
            for idx, pos in enumerate(open_pos):
                with st.expander(f"{pos['symbol']} {pos['direction']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Entry Price", f"${float(pos['entry_price']):,.2f}")
                        st.metric("Size", pos['size'])
                        st.metric("AI Confidence", f"{pos['ai_confidence']}%")
                    with col2:
                        st.metric("Current P&L", f"${float(pos['pnl']):,.2f}")
                        st.metric("Stop Loss", f"${float(pos['stop_loss']):,.2f}")
                        st.metric("Take Profit", f"${float(pos['take_profit']):,.2f}")
                    
                    # AI Analysis section
                    if self.ai_monitoring_active:
                        st.subheader("🤖 AI Analysis")
                        self.display_ai_recommendations(pos)
                    
                    # Manual AI Analysis button
                    if st.button("🔍 Analyze Position", key=f"analyze_{idx}"):
                        with st.spinner("Performing AI analysis..."):
                            recommendations = self.analyze_position(pos)
                            if recommendations:
                                pos['ai_recommendations'] = pos.get('ai_recommendations', [])
                                pos['ai_recommendations'].append(recommendations)
                                self.save_positions()
                                st.success("Analysis completed!")
                                self.display_ai_recommendations(pos)
                    
                    # Close position button
                    if st.button("🔴 Close Position", key=f"close_{idx}"):
                        if self.close_position(idx):
                            st.success("Position closed successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to close position")
        else:
            st.info("No open positions")
        
        # Display closed positions
        st.subheader("Closed Positions")
        closed_pos = [p for p in self.positions if p['status'] != 'OPEN']
        if closed_pos:
            for pos in closed_pos:
                with st.expander(f"{pos['symbol']} {pos['direction']} ({pos['status']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Entry Price", f"${float(pos['entry_price']):,.2f}")
                        st.metric("Exit Price", f"${float(pos.get('exit_price', 0)):,.2f}" if pos.get('exit_price') else "N/A")
                        st.metric("Size", pos['size'])
                    with col2:
                        st.metric("Final P&L", f"${float(pos['pnl']):,.2f}")
                        entry_date = pos['entry_time'].split('T')[0] if 'T' in pos['entry_time'] else pos['entry_time']
                        st.metric("Entry Time", entry_date)
                        exit_date = pos.get('exit_time', '').split('T')[0] if pos.get('exit_time') and 'T' in pos['exit_time'] else pos.get('exit_time', '')
                        st.metric("Exit Time", exit_date if exit_date else "N/A")
        else:
            st.info("No closed positions")

def create_position_tracker_page(binance_client):
    """Create the position tracker page"""
    tracker = PositionTracker(binance_client)
    tracker.display_positions()
    return tracker
