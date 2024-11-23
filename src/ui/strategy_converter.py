import streamlit as st

def convert_indicator_to_strategy(anthropic_client, indicator_code):
    """Use Anthropic to convert indicator code to strategy"""
    if not anthropic_client:
        st.error("Chatbase integration not configured. Please check your API key.")
        return None
        
    try:
        # Use exact prompt format
        prompt = f"""You are a professional PineScript version=5 developer.
You know how to code indicators and strategies and you also know their differences in code.
I need your help to turn a TradingView indicator into a strategy please.

Please correct the Pine Script as follows:

    Ensure Entries Only Within Date Range: Ensure trades are executed only between the specified start and end dates.
    Position Management: Only enter a trade if no position is open.
    Close Positions When Conditions Change: Close the position when conditions are no longer met.
    Simplify Logic: Clean the logic to ensure the conditions for entry and exit are clearly defined without redundancy.

Respect these instructions:
- Convert all Indicator specific code to Strategy specific code
- Preserve the timeframe logic if there is one
- If the indicator is plotting something, the strategy code shall plot the same thing
- Set commission to 0.1% and slippage to 3 in the strategy() function
- Add Start Date (2018) and End Date (2069) inputs
- Add "Trading-Ai - " prefix to strategy name

Critical Rules:
ALWAYS include both entry and exit conditions
ALWAYS use proper color syntax (color.xxx)
ALWAYS check position size before entries
ALWAYS include date range filter in trading logic

This is the code of the Indicator you shall migrate to a TradingView Strategy:

{indicator_code}"""

        # Use Claude 3 Sonnet for conversion
        response = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            temperature=0,
            system="You are an expert PineScript developer.",
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Return the complete AI response
        if hasattr(response, 'content'):
            content = response.content
            if isinstance(content, list):
                content = content[0].text if content else ""
            return content
            
        return None
        
    except Exception as e:
        st.error(f"Error during conversion: {str(e)}")
        return None

def display_strategy_converter():
    """Display the TradingView indicator to strategy converter interface"""
    st.header("🔄 Convert TradingView Indicators to Strategies")
    
    st.markdown("""
    Convert your TradingView indicators into strategies using AI. The converter:
    - Converts indicator code to strategy code
    - Preserves timeframe logic and visuals
    - Sets commission (0.1%) and slippage (3)
    - Adds date range inputs (2018-2069)
    """)
    
    # Input area for indicator code
    indicator_code = st.text_area(
        "Paste your TradingView indicator code here:",
        height=300,
        help="Paste your PineScript indicator code and the AI will convert it to a strategy"
    )
    
    # Get Anthropic client from session state
    anthropic_client = st.session_state.get('anthropic_client')
    
    if st.button("Convert to Strategy", type="primary"):
        if not indicator_code.strip():
            st.error("Please paste your indicator code first")
            return
            
        st.markdown("### 🤖 AI Response")
        
        with st.spinner("AI is analyzing and converting your indicator..."):
            ai_response = convert_indicator_to_strategy(anthropic_client, indicator_code)
            
            if ai_response:
                st.markdown(ai_response)
                
                # Add to conversion history
                if 'conversion_history' not in st.session_state:
                    st.session_state.conversion_history = []
                    
                st.session_state.conversion_history.append({
                    'timestamp': st.session_state.get('current_time', ''),
                    'original': indicator_code,
                    'ai_response': ai_response
                })

def display_conversion_history():
    """Display history of previous conversions"""
    if 'conversion_history' in st.session_state and st.session_state.conversion_history:
        st.markdown("### 📚 Conversion History")
        for i, conversion in enumerate(reversed(st.session_state.conversion_history)):
            st.markdown(f"**Conversion {i+1} - {conversion['timestamp']}**")
            
            tab1, tab2 = st.tabs(["Original Code", "AI Response"])
            
            with tab1:
                st.code(conversion['original'], language="pine")
            
            with tab2:
                st.markdown(conversion['ai_response'])
            
            st.markdown("---")
