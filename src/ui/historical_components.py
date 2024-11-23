import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, List
import plotly.express as px
from datetime import datetime, timedelta

def display_historical_analysis(historical_results: Dict):
    """Display historical analysis results"""
    try:
        if not historical_results or not isinstance(historical_results, dict):
            st.warning("No historical analysis results available")
            return
            
        accuracy_metrics = historical_results.get('accuracy_metrics', {})
        roi_metrics = historical_results.get('roi_metrics', {})
        error_analysis = historical_results.get('error_analysis', {})
        predictions = historical_results.get('predictions', [])
        
        st.header("📊 Historical Analysis Results")
        
        # Display accuracy metrics
        st.subheader("🎯 Accuracy Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Overall Accuracy",
                f"{accuracy_metrics.get('overall_accuracy', 0):.1f}%"
            )
        with col2:
            st.metric(
                "Long Accuracy",
                f"{accuracy_metrics.get('long_accuracy', 0):.1f}%"
            )
        with col3:
            st.metric(
                "Short Accuracy",
                f"{accuracy_metrics.get('short_accuracy', 0):.1f}%"
            )
            
        # Display confidence-based accuracy
        st.subheader("🎯 Confidence-Based Accuracy")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "High Confidence (>75%)",
                f"{accuracy_metrics.get('high_confidence_accuracy', 0):.1f}%"
            )
        with col2:
            st.metric(
                "Low Confidence (<75%)",
                f"{accuracy_metrics.get('low_confidence_accuracy', 0):.1f}%"
            )
            
        # Display ROI metrics
        st.subheader("💰 ROI Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total ROI",
                f"{roi_metrics.get('total_roi', 0):.2f}%"
            )
        with col2:
            st.metric(
                "Average Win",
                f"{roi_metrics.get('avg_win', 0):.2f}%"
            )
        with col3:
            st.metric(
                "Average Loss",
                f"{roi_metrics.get('avg_loss', 0):.2f}%"
            )
        with col4:
            st.metric(
                "Profit Factor",
                f"{roi_metrics.get('profit_factor', 0):.2f}"
            )
            
        # Plot prediction accuracy over time
        if predictions:
            st.subheader("📈 Prediction Performance")
            predictions_df = pd.DataFrame(predictions)
            
            fig = go.Figure()
            
            # Add success/failure scatter plot
            fig.add_trace(go.Scatter(
                x=predictions_df['timestamp'],
                y=[1 if s else 0 for s in predictions_df['success']],
                mode='markers',
                name='Predictions',
                marker=dict(
                    color=[('green' if s else 'red') for s in predictions_df['success']],
                    size=10
                )
            ))
            
            fig.update_layout(
                title='Prediction Success/Failure Over Time',
                yaxis=dict(
                    ticktext=['Failure', 'Success'],
                    tickvals=[0, 1],
                    range=[-0.1, 1.1]
                ),
                template='plotly_dark'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        # Display error analysis
        if error_analysis:
            st.subheader("❌ Error Analysis")
            
            # Create error analysis chart
            error_df = pd.DataFrame({
                'Error Type': list(error_analysis.keys()),
                'Percentage': list(error_analysis.values())
            })
            
            fig = px.bar(
                error_df,
                x='Error Type',
                y='Percentage',
                title='Error Pattern Distribution',
                template='plotly_dark'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display error insights
            st.subheader("🔍 Error Insights")
            
            # High volatility failures
            if error_analysis.get('high_volatility_fails', 0) > 30:
                st.warning("⚠️ High failure rate during volatile periods. Consider reducing position sizes or widening stop losses during high volatility.")
                
            # Trend misalignment
            if error_analysis.get('trend_misalignment', 0) > 30:
                st.warning("⚠️ Significant trend misalignment issues. Consider adding trend confirmation before entering trades.")
                
            # False breakouts
            if error_analysis.get('false_breakouts', 0) > 30:
                st.warning("⚠️ High rate of false breakouts. Consider waiting for confirmation before entering trades.")
                
            # Stop loss hits
            if error_analysis.get('stop_loss_hits', 0) > 30:
                st.warning("⚠️ Frequent stop loss hits. Consider reviewing stop loss placement strategy.")
            
        # Display detailed analysis
        detailed_analysis = historical_results.get('detailed_analysis', [])
        if detailed_analysis:
            st.subheader("📋 Detailed Analysis")
            for analysis in detailed_analysis:
                with st.expander(f"Analysis for {analysis['timestamp']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("Prediction Details:")
                        st.write(f"Direction: {analysis.get('prediction', {}).get('direction', 'Unknown')}")
                        st.write(f"Confidence: {analysis.get('prediction', {}).get('confidence', 0):.1f}%")
                        price_levels = analysis.get('prediction', {}).get('price_levels', {})
                        st.write(f"Entry: {price_levels.get('entry', 0):.2f}")
                        st.write(f"Take Profit: {price_levels.get('tp', 0):.2f}")
                        st.write(f"Stop Loss: {price_levels.get('sl', 0):.2f}")
                        
                    with col2:
                        st.write("Market Conditions:")
                        market_conditions = analysis.get('market_conditions', {})
                        st.write(f"Volatility: {market_conditions.get('volatility', 0):.2f}")
                        st.write(f"Trend: {market_conditions.get('trend', 'Unknown')}")
                        st.write(f"Volume Profile: {market_conditions.get('volume_profile', 'Unknown')}")
                        
                    st.write(f"Outcome: {'✅ Success' if analysis.get('success', False) else '❌ Failure'}")
    except Exception as e:
        st.error(f"Error displaying historical analysis: {str(e)}")

def plot_confidence_vs_accuracy(historical_results: Dict):
    """Plot relationship between prediction confidence and accuracy"""
    try:
        if not historical_results or not isinstance(historical_results, dict):
            return
            
        predictions = historical_results.get('predictions', [])
        if not predictions:
            return
            
        predictions_df = pd.DataFrame(predictions)
        
        fig = px.scatter(
            predictions_df,
            x=[p.get('predicted', {}).get('confidence', 0) for p in predictions],
            y=[1 if s else 0 for s in predictions_df['success']],
            title='Prediction Confidence vs Accuracy',
            labels={'x': 'Confidence (%)', 'y': 'Success'},
            color=[1 if s else 0 for s in predictions_df['success']],
            color_discrete_map={1: 'green', 0: 'red'}
        )
        
        fig.update_layout(
            yaxis=dict(
                ticktext=['Failure', 'Success'],
                tickvals=[0, 1],
                range=[-0.1, 1.1]
            ),
            template='plotly_dark'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error plotting confidence vs accuracy: {str(e)}")
