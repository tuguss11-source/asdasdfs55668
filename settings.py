# 📁 settings.py - GÜNCEL
import sys
import os

# PROJE KÖK DİZİNİNİ BUL
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# SEMBOL İSİMLERİ
SYMBOLS = [
    "BINANCE:BTCUSDT",
    "BINANCE:ETHUSDT", 
    "BINANCE:ADAUSDT",
    "BINANCE:SOLUSDT"
]

# Çoklu zaman dilimleri
TIMEFRAMES = ["5m", "15m", "1h", "4h", "1d"]

# API için model config
MODEL_CONFIG = {
    "api_url": "http://localhost:1234/v1/chat/completions",
    "max_tokens": 500,
    "temperature": 0.1
}

ANALYSIS_CONFIG = {
    "check_interval": 300,
    "default_capital": 1000,
    "risk_per_trade": 0.02,
    "analyze_multiple_timeframes": True
}

TRADING_CONFIG = {
    "stop_loss_percentage": 0.05,
    "take_profit_ratios": [1.5, 2.0, 3.0],
    "position_sizing": True,
    "max_leverage": "5x"
}

# YENİ: OTOMATİK TRADING AYARLARI
AUTO_TRADING_CONFIG = {
    "enabled": False,
    "paper_trading": True,
    "max_positions": 5,
    "daily_loss_limit": -0.1,  # -%10
    "min_signal_strength": 7
}

# YENİ: EXCHANGE AYARLARI
EXCHANGES = {
    "binance": {
        "enabled": True,
        "api_key": "",
        "api_secret": "",
        "testnet": True
    },
    "kucoin": {
        "enabled": False,
        "api_key": "",
        "api_secret": "",
        "passphrase": ""
    }
}

# YENİ: RİSK YÖNETİMİ
RISK_MANAGEMENT = {
    "max_drawdown": 0.15,  # Maksimum %15 drawdown
    "var_limit": 0.05,     # Value at Risk limit
    "correlation_threshold": 0.7,
    "portfolio_beta_limit": 1.5
}