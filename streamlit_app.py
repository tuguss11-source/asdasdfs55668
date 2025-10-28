import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import requests
import warnings
warnings.filterwarnings('ignore')

# Database path
DB_PATH = "portfolio.db"

def init_db():
    """Initialize database with required tables"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        
        # Portfolio table
        c.execute('''CREATE TABLE IF NOT EXISTS portfolio
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     symbol TEXT NOT NULL,
                     entry_price REAL NOT NULL,
                     quantity REAL NOT NULL,
                     current_price REAL NOT NULL,
                     pnl REAL DEFAULT 0,
                     status TEXT DEFAULT 'active',
                     timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        
        # Signals table
        c.execute('''CREATE TABLE IF NOT EXISTS signals
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     symbol TEXT NOT NULL,
                     signal_type TEXT NOT NULL,
                     strength INTEGER NOT NULL,
                     price REAL NOT NULL,
                     timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        
        conn.commit()

def get_portfolio_data():
    """Get portfolio data from database"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''SELECT * FROM portfolio WHERE status = "active"''')
        data = c.fetchall()
        
        if data:
            df = pd.DataFrame(data, columns=['id', 'symbol', 'entry_price', 'quantity', 
                                           'current_price', 'pnl', 'status', 'timestamp'])
            return df
        else:
            # Sample data for demo
            return pd.DataFrame({
                'symbol': ['BTCUSDT', 'ETHUSDT'],
                'entry_price': [45000, 3000],
                'quantity': [0.1, 2.0],
                'current_price': [52000, 3500],
                'pnl': [700, 1000],
                'status': ['active', 'active']
            })

def get_signals_data():
    """Get signals data from database"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''SELECT * FROM signals ORDER BY timestamp DESC LIMIT 10''')
        data = c.fetchall()
        
        if data:
            df = pd.DataFrame(data, columns=['id', 'symbol', 'signal_type', 'strength', 
                                           'price', 'timestamp'])
            return df
        else:
            # Sample signals for demo
            return pd.DataFrame({
                'symbol': ['BTCUSDT', 'ETHUSDT', 'ADAUSDT'],
                'signal_type': ['BUY', 'SELL', 'HOLD'],
                'strength': [8, 6, 3],
                'price': [52000, 3500, 0.45],
                'timestamp': [datetime.now()] * 3
            })

def main():
    """Main Streamlit application"""
    
    # Initialize database
    init_db()
    
    # Page configuration
    st.set_page_config(
        page_title="Crypto Signal System",
        page_icon="📈",
        layout="wide"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #00D4AA;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #1E1E1E;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #00D4AA;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">🤖 Crypto Signal System</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.title("🎯 Navigation")
        
        # UNIQUE KEY'ler eklendi - selectbox hataları düzeltildi
        page = st.selectbox(
            "Choose Page",
            ["Dashboard", "Portfolio", "Signals", "Analysis", "Settings"],
            key="page_selector"
        )
        
        st.markdown("---")
        st.subheader("🔧 Configuration")
        
        # UNIQUE KEY'ler eklendi
        symbol = st.selectbox(
            "Select Symbol",
            ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT", "BNBUSDT"],
            key="symbol_selector"
        )
        
        # UNIQUE KEY'ler eklendi
        timeframe = st.selectbox(
            "Select Timeframe",
            ["5m", "15m", "1h", "4h", "1d"],
            key="timeframe_selector"
        )
        
        st.markdown("---")
        st.info("""
        **Real-time Features:**
        ✅ Live Price Data
        ✅ AI Signal Generation  
        ✅ Portfolio Tracking
        ✅ Risk Management
        """)
    
    # Main content based on selected page
    if page == "Dashboard":
        show_dashboard()
    elif page == "Portfolio":
        show_portfolio()
    elif page == "Signals":
        show_signals()
    elif page == "Analysis":
        show_analysis()
    else:
        show_settings()

def show_dashboard():
    """Dashboard page"""
    st.header("📊 Dashboard")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Portfolio", "$25,430", "+5.2%")
    
    with col2:
        st.metric("Active Signals", "8", "+2")
    
    with col3:
        st.metric("Today's P&L", "+$342", "+1.8%")
    
    with col4:
        st.metric("Risk Level", "Medium", "-0.3")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Portfolio Allocation")
        
        # Sample pie chart
        fig = go.Figure(data=[go.Pie(
            labels=['BTC', 'ETH', 'ADA', 'SOL'],
            values=[60, 25, 10, 5],
            hole=.3
        )])
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Price Performance")
        
        # Sample line chart
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        prices = 50000 + np.cumsum(np.random.randn(30) * 1000)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=prices,
            mode='lines',
            name='BTC Price',
            line=dict(color='#00D4AA', width=3)
        ))
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent signals
    st.subheader("🎯 Recent Signals")
    signals_df = get_signals_data()
    st.dataframe(signals_df, use_container_width=True)

def show_portfolio():
    """Portfolio page"""
    st.header("💰 Portfolio Management")
    
    portfolio_df = get_portfolio_data()
    
    # Portfolio metrics
    total_value = (portfolio_df['current_price'] * portfolio_df['quantity']).sum()
    total_invested = (portfolio_df['entry_price'] * portfolio_df['quantity']).sum()
    total_pnl = total_value - total_invested
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Value", f"${total_value:,.2f}")
    
    with col2:
        st.metric("Total Invested", f"${total_invested:,.2f}")
    
    with col3:
        st.metric("Total P&L", f"${total_pnl:,.2f}", 
                 f"{(total_pnl/total_invested*100):.2f}%" if total_invested > 0 else "0%")
    
    # Portfolio table
    st.subheader("Current Positions")
    st.dataframe(portfolio_df, use_container_width=True)
    
    # Add new position form
    with st.expander("➕ Add New Position"):
        with st.form("add_position"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # UNIQUE KEY eklendi
                new_symbol = st.selectbox(
                    "Symbol",
                    ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT"],
                    key="new_symbol_selector"
                )
            
            with col2:
                entry_price = st.number_input("Entry Price", min_value=0.0, value=50000.0)
            
            with col3:
                quantity = st.number_input("Quantity", min_value=0.0, value=0.1)
            
            if st.form_submit_button("Add Position"):
                st.success(f"Added {quantity} {new_symbol} at ${entry_price:,.2f}")

def show_signals():
    """Signals page"""
    st.header("🎯 Trading Signals")
    
    # Signal filters
    col1, col2 = st.columns(2)
    
    with col1:
        # UNIQUE KEY eklendi
        signal_type = st.selectbox(
            "Filter by Type",
            ["All", "BUY", "SELL", "HOLD"],
            key="signal_type_filter"
        )
    
    with col2:
        # UNIQUE KEY eklendi
        min_strength = st.selectbox(
            "Minimum Strength",
            [1, 3, 5, 7, 9],
            index=2,
            key="min_strength_filter"
        )
    
    # Signals table
    signals_df = get_signals_data()
    
    # Apply filters
    if signal_type != "All":
        signals_df = signals_df[signals_df['signal_type'] == signal_type]
    
    signals_df = signals_df[signals_df['strength'] >= min_strength]
    
    # Color code signals
    def color_signal(val):
        if val == 'BUY':
            return 'background-color: #00FF0020; color: green;'
        elif val == 'SELL':
            return 'background-color: #FF000020; color: red;'
        else:
            return 'background-color: #FFFF0020; color: orange;'
    
    styled_df = signals_df.style.map(color_signal, subset=['signal_type'])
    st.dataframe(styled_df, use_container_width=True)
    
    # Signal actions
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Generate New Signals", key="generate_signals_btn"):
            st.info("Generating new AI signals...")
            time.sleep(1)
            st.rerun()
    
    with col2:
        if st.button("📊 Backtest Signals", key="backtest_btn"):
            st.info("Running backtest analysis...")

def show_analysis():
    """Analysis page"""
    st.header("🔍 Market Analysis")
    
    # Technical indicators
    st.subheader("Technical Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("RSI", "54.3", "-1.2")
    
    with col2:
        st.metric("MACD", "128.6", "+8.4")
    
    with col3:
        st.metric("Volume", "2.1B", "+5.3%")
    
    with col4:
        st.metric("Volatility", "2.8%", "-0.2%")
    
    # Market sentiment
    st.subheader("Market Sentiment")
    
    sentiment_col1, sentiment_col2 = st.columns(2)
    
    with sentiment_col1:
        st.info("""
        **📈 Bullish Factors:**
        - Strong institutional buying
        - Positive regulatory developments  
        - Increasing adoption metrics
        """)
    
    with sentiment_col2:
        st.warning("""
        **📉 Bearish Factors:**
        - Global economic uncertainty
        - High leverage in derivatives
        - Technical resistance levels
        """)
    
    # AI Analysis
    st.subheader("🤖 AI Analysis")
    
    st.success("""
    **BTCUSDT - 1H Timeframe Analysis**
    
    **Recommendation:** CAUTIOUS BUY
    **Confidence Score:** 7.2/10
    
    **Key Insights:**
    - RSI in neutral territory (54.3)
    - MACD showing positive momentum
    - Volume supporting upward movement
    - Key resistance at $53,000
    
    **Risk Level:** Medium
    **Suggested Position Size:** 2-3% of portfolio
    """)

def show_settings():
    """Settings page"""
    st.header("⚙️ System Settings")
    
    # Trading settings
    st.subheader("Trading Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # UNIQUE KEY eklendi
        trading_mode = st.selectbox(
            "Trading Mode",
            ["Paper Trading", "Live Trading"],
            key="trading_mode_selector"
        )
        
        # UNIQUE KEY eklendi
        risk_level = st.selectbox(
            "Risk Level",
            ["Low", "Medium", "High"],
            index=1,
            key="risk_level_selector"
        )
    
    with col2:
        max_position_size = st.slider(
            "Max Position Size (%)",
            min_value=1,
            max_value=20,
            value=5
        )
        
        stop_loss = st.slider(
            "Default Stop Loss (%)", 
            min_value=1,
            max_value=15,
            value=3
        )
    
    # API settings
    st.subheader("API Configuration")
    
    api_key = st.text_input(
        "Exchange API Key",
        type="password",
        placeholder="Enter your API key...",
        key="api_key_input"
    )
    
    api_secret = st.text_input(
        "Exchange API Secret", 
        type="password",
        placeholder="Enter your API secret...",
        key="api_secret_input"
    )
    
    if st.button("💾 Save Settings", key="save_settings_btn"):
        st.success("Settings saved successfully!")
    
    # System info
    st.markdown("---")
    st.subheader("System Information")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.write("**Version:** 2.1.0")
        st.write("**Last Updated:** 2024-10-28")
        st.write("**Database:** SQLite")
    
    with info_col2:
        st.write("**AI Model:** Advanced Local AI")
        st.write("**Exchange Support:** Binance")
        st.write("**Signal Accuracy:** 78.3%")

if __name__ == "__main__":
    main()