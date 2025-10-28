import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.binance_client import BinanceClient
from data.tradingview_client import TradingViewClient

class HybridDataClient:
    def __init__(self):
        self.binance_client = BinanceClient()
        self.tradingview_client = TradingViewClient()
        self.data_source_priority = ["binance", "tradingview"]
    
    def get_multiple_timeframe_data(self, symbol, timeframes=["5m", "15m", "1h", "4h"]):
        """Melez veri kaynağı - önce Binance, sonra TradingView"""
        print(f"   🔄 Hibrit veri kaynağı: {symbol} için veri alınıyor...")
        
        # Önce Binance'dan dene
        binance_data = self.binance_client.get_multiple_timeframe_data(symbol, timeframes)
        
        # Binance verilerini kontrol et
        valid_data = {}
        for tf, data in binance_data.items():
            if data and data['close'] > 0:
                valid_data[tf] = data
                print(f"   ✅ Binance {tf} verisi kullanılıyor")
            else:
                # Binance'tan alınamazsa TradingView'dan al
                print(f"   🔄 {tf} için TradingView deneniyor...")
                tv_data = self.tradingview_client.get_technical_data(symbol, tf)
                if tv_data and tv_data['close'] > 0:
                    valid_data[tf] = tv_data
                    print(f"   ✅ TradingView {tf} verisi kullanılıyor")
                else:
                    # Hiçbiri olmazsa Binance fallback
                    valid_data[tf] = data
                    print(f"   ⚠️ {tf} için fallback veri kullanılıyor")
        
        return valid_data
    
    def get_technical_data(self, symbol, timeframe):
        """Tek zaman dilimi için hibrit veri al"""
        # Önce Binance
        klines = self.binance_client.get_klines(symbol, timeframe, limit=100)
        if klines:
            data = self.binance_client.calculate_technical_indicators(klines, symbol, timeframe)
            if data and data['close'] > 0:
                return data
        
        # Binance olmazsa TradingView
        return self.tradingview_client.get_technical_data(symbol, timeframe)
    
    def test_all_connections(self):
        """Tüm bağlantıları test et"""
        print("🧪 TÜM VERİ KAYNAKLARI TEST EDİLİYOR...")
        
        print("\n1. Binance Testi:")
        binance_ok = self.binance_client.test_connection()
        
        print("\n2. TradingView Testi:")
        tradingview_ok = self.tradingview_client.test_connection()
        
        print("\n3. Hibrit Sistem Testi:")
        test_data = self.get_multiple_timeframe_data("BINANCE:BTCUSDT", ["15m", "1h"])
        
        if test_data and len(test_data) > 0:
            print("✅ Hibrit sistem çalışıyor!")
            for tf, data in test_data.items():
                print(f"   {tf}: ${data['close']:,.2f} | RSI: {data['rsi']:.1f}")
            return True
        else:
            print("❌ Hibrit sistem testi başarısız!")
            return False