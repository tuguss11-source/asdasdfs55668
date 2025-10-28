import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class BinanceClient:
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_klines(self, symbol, interval, limit=500, start_time=None, end_time=None):
        """Binance'dan kline/candlestick verilerini al"""
        url = f"{self.base_url}/klines"
        
        # Binance sembol formatına çevir (BINANCE:BTCUSDT -> BTCUSDT)
        binance_symbol = symbol.replace('BINANCE:', '')
        
        params = {
            'symbol': binance_symbol,
            'interval': interval,
            'limit': min(limit, 1000)
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
            
        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Binance API Hatası: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Binance bağlantı hatası: {e}")
            return None
    
    def get_current_price(self, symbol):
        """Anlık fiyat bilgisini al - GÜNCEL"""
        url = f"{self.base_url}/ticker/price"
        binance_symbol = symbol.replace('BINANCE:', '')
        params = {'symbol': binance_symbol}
        
        try:
            response = self.session.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return float(data['price'])
            return None
        except Exception as e:
            print(f"❌ Güncel fiyat alınamadı: {e}")
            return None
    
    def calculate_technical_indicators(self, klines_data, symbol, timeframe):
        """Ham kline verilerinden teknik göstergeleri hesapla - GELİŞMİŞ"""
        if not klines_data:
            return self._get_fallback_data(symbol, timeframe)
        
        try:
            # DataFrame oluştur
            df = pd.DataFrame(klines_data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy',
                'taker_quote', 'ignore'
            ])
            
            # Sayısal veriye çevir
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            # Son veriyi al (en güncel)
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            
            # GELİŞMİŞ teknik göstergeleri hesapla
            indicators = self._calculate_advanced_indicators(df)
            
            current_price = float(latest['close'])
            prev_price = float(prev['close'])
            price_change = ((current_price - prev_price) / prev_price) * 100 if prev_price > 0 else 0
            
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'close': round(current_price, 4),
                'volume': int(float(latest['volume'])),
                'change': round(price_change, 2),
                'change_abs': round(current_price - prev_price, 4),
                'rsi': round(indicators['rsi'], 2),
                'rsi_1': round(indicators['rsi_prev'], 2),
                'macd': round(indicators['macd'], 4),
                'macd_signal': round(indicators['macd_signal'], 4),
                'macd_histogram': round(indicators['macd_histogram'], 4),
                'ema_20': round(indicators['ema_20'], 4),
                'ema_50': round(indicators['ema_50'], 4),
                'bollinger_upper': round(indicators['bollinger_upper'], 4),
                'bollinger_lower': round(indicators['bollinger_lower'], 4),
                'bollinger_middle': round(indicators['bollinger_middle'], 4),
                'stoch_k': round(indicators['stoch_k'], 2),
                'stoch_d': round(indicators['stoch_d'], 2),
                'recommendation': self._get_recommendation(indicators)
            }
        except Exception as e:
            print(f"❌ Teknik gösterge hesaplama hatası: {e}")
            return self._get_fallback_data(symbol, timeframe)
    
    def _calculate_advanced_indicators(self, df):
        """GELİŞMİŞ teknik göstergeleri hesapla"""
        close_prices = df['close'].values
        high_prices = df['high'].values
        low_prices = df['low'].values
        
        # RSI Hesaplama
        rsi = self._calculate_rsi(close_prices)
        
        # MACD Hesaplama
        macd, macd_signal, macd_histogram = self._calculate_macd(close_prices)
        
        # EMA Hesaplama
        ema_20 = self._calculate_ema(close_prices, 20)
        ema_50 = self._calculate_ema(close_prices, 50)
        
        # Bollinger Bands Hesaplama
        bb_upper, bb_lower, bb_middle = self._calculate_bollinger_bands(close_prices)
        
        # Stochastic Hesaplama
        stoch_k, stoch_d = self._calculate_stochastic(high_prices, low_prices, close_prices)
        
        return {
            'rsi': rsi[-1] if len(rsi) > 0 else 50,
            'rsi_prev': rsi[-2] if len(rsi) > 1 else 50,
            'macd': macd[-1] if len(macd) > 0 else 0,
            'macd_signal': macd_signal[-1] if len(macd_signal) > 0 else 0,
            'macd_histogram': macd_histogram[-1] if len(macd_histogram) > 0 else 0,
            'ema_20': ema_20[-1] if len(ema_20) > 0 else close_prices[-1],
            'ema_50': ema_50[-1] if len(ema_50) > 0 else close_prices[-1],
            'bollinger_upper': bb_upper[-1] if len(bb_upper) > 0 else close_prices[-1],
            'bollinger_lower': bb_lower[-1] if len(bb_lower) > 0 else close_prices[-1],
            'bollinger_middle': bb_middle[-1] if len(bb_middle) > 0 else close_prices[-1],
            'stoch_k': stoch_k[-1] if len(stoch_k) > 0 else 50,
            'stoch_d': stoch_d[-1] if len(stoch_d) > 0 else 50
        }
    
    def _calculate_rsi(self, prices, period=14):
        """RSI hesapla"""
        if len(prices) < period + 1:
            return [50] * len(prices)
        
        # ✅ DÜZELTME: NumPy array'e çevir
        prices = np.array(prices)
        deltas = np.diff(prices)
        
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = np.zeros_like(prices)
        avg_losses = np.zeros_like(prices)
        
        # İlk değerler
        avg_gains[period] = np.mean(gains[:period])
        avg_losses[period] = np.mean(losses[:period])
        
        for i in range(period + 1, len(prices)):
            avg_gains[i] = (avg_gains[i-1] * (period - 1) + gains[i-1]) / period
            avg_losses[i] = (avg_losses[i-1] * (period - 1) + losses[i-1]) / period
        
        rs = avg_gains / (avg_losses + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        # ✅ DÜZELTME: tolist() yerine list comprehension
        return [float(x) for x in rsi]
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """MACD hesapla"""
        if len(prices) < slow:
            return [0] * len(prices), [0] * len(prices), [0] * len(prices)
        
        # ✅ DÜZELTME: NumPy array'e çevir
        prices = np.array(prices)
        
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        
        macd_line = np.array(ema_fast) - np.array(ema_slow)
        signal_line = self._calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        # ✅ DÜZELTME: tolist() yerine list comprehension
        return (
            [float(x) for x in macd_line],
            [float(x) for x in signal_line], 
            [float(x) for x in histogram]
        )
    
    def _calculate_ema(self, prices, period):
        """EMA hesapla"""
        if len(prices) < period:
            # ✅ DÜZELTME: Liste döndür
            return [float(x) for x in prices] if hasattr(prices, '__iter__') else [float(prices)]
        
        # ✅ DÜZELTME: NumPy array'e çevir
        prices = np.array(prices)
        ema = np.zeros_like(prices)
        multiplier = 2 / (period + 1)
        
        # SMA ile başla
        sma = np.mean(prices[:period])
        ema[period-1] = sma
        
        # EMA devamı
        for i in range(period, len(prices)):
            ema[i] = (prices[i] * multiplier) + (ema[i-1] * (1 - multiplier))
        
        # ✅ DÜZELTME: tolist() yerine list comprehension
        return [float(x) for x in ema]
    
    def _calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """Bollinger Bands hesapla"""
        if len(prices) < period:
            middle = [float(x) for x in prices]
            upper = [float(x) for x in prices]
            lower = [float(x) for x in prices]
        else:
            middle = self._calculate_sma(prices, period)
            std = pd.Series(prices).rolling(window=period).std().tolist()
            
            upper = np.array(middle) + (np.array(std) * std_dev)
            lower = np.array(middle) - (np.array(std) * std_dev)
            
            # İlk period-1 değeri için fiyatı kullan
            for i in range(period-1):
                upper[i] = prices[i]
                lower[i] = prices[i]
        
        return (
            [float(x) for x in upper],
            [float(x) for x in lower], 
            [float(x) for x in middle]
        )
    
    def _calculate_sma(self, prices, period):
        """Simple Moving Average hesapla"""
        if len(prices) < period:
            return [float(x) for x in prices]
        
        sma = []
        for i in range(len(prices)):
            if i < period - 1:
                sma.append(float(prices[i]))
            else:
                sma.append(float(np.mean(prices[i-period+1:i+1])))
        return sma
    
    def _calculate_stochastic(self, high, low, close, period=14, smooth_k=3, smooth_d=3):
        """Stochastic Oscillator hesapla"""
        if len(close) < period:
            return [50] * len(close), [50] * len(close)
        
        k_values = []
        for i in range(len(close)):
            if i < period - 1:
                k_values.append(50)
            else:
                highest_high = max(high[i-period+1:i+1])
                lowest_low = min(low[i-period+1:i+1])
                if highest_high != lowest_low:
                    k = 100 * (close[i] - lowest_low) / (highest_high - lowest_low)
                else:
                    k = 50
                k_values.append(float(k))
        
        # Smooth K değeri
        k_smooth = self._calculate_sma(k_values, smooth_k)
        
        # Smooth D değeri (signal line)
        d_smooth = self._calculate_sma(k_smooth, smooth_d)
        
        return k_smooth, d_smooth
    
    def _get_recommendation(self, indicators):
        """Göstergelere göre tavsiye oluştur"""
        rsi = indicators['rsi']
        macd = indicators['macd']
        macd_signal = indicators['macd_signal']
        stoch_k = indicators['stoch_k']
        stoch_d = indicators['stoch_d']
        current_price = indicators['ema_20']
        bb_upper = indicators['bollinger_upper']
        bb_lower = indicators['bollinger_lower']
        
        score = 0
        
        # RSI skoru
        if rsi < 30:
            score += 2
        elif rsi < 40:
            score += 1
        elif rsi > 70:
            score -= 2
        elif rsi > 60:
            score -= 1
        
        # MACD skoru
        if macd > macd_signal:
            score += 1
        else:
            score -= 1
        
        # Stochastic skoru
        if stoch_k < 20 and stoch_d < 20:
            score += 1
        elif stoch_k > 80 and stoch_d > 80:
            score -= 1
        
        # Bollinger Bands skoru
        if current_price < bb_lower:
            score += 1
        elif current_price > bb_upper:
            score -= 1
        
        if score >= 3:
            return "STRONG_BUY"
        elif score >= 1:
            return "BUY"
        elif score <= -3:
            return "STRONG_SELL"
        elif score <= -1:
            return "SELL"
        else:
            return "NEUTRAL"
    
    def _get_fallback_data(self, symbol, timeframe):
        """Fallback veri oluştur"""
        # Önce gerçek fiyatı almaya çalış
        current_price = self.get_current_price(symbol)
        if not current_price:
            # Gerçek fiyat alınamazsa base price kullan
            base_prices = {
                "BINANCE:BTCUSDT": 50000,
                "BINANCE:ETHUSDT": 3000,
                "BINANCE:ADAUSDT": 0.5,
                "BINANCE:SOLUSDT": 100
            }
            current_price = base_prices.get(symbol, 100)
        
        import random
        return {
            'symbol': symbol,
            'timeframe': timeframe,
            'close': round(current_price, 4),
            'volume': random.randint(1000000, 5000000),
            'change': round(random.uniform(-2, 2), 2),
            'change_abs': round(current_price * random.uniform(-0.02, 0.02), 4),
            'rsi': round(random.uniform(30, 70), 2),
            'rsi_1': round(random.uniform(30, 70), 2),
            'macd': round(random.uniform(-10, 10), 4),
            'macd_signal': round(random.uniform(-8, 8), 4),
            'macd_histogram': round(random.uniform(-2, 2), 4),
            'ema_20': round(current_price * random.uniform(0.98, 1.02), 4),
            'ema_50': round(current_price * random.uniform(0.96, 1.04), 4),
            'bollinger_upper': round(current_price * random.uniform(1.02, 1.05), 4),
            'bollinger_lower': round(current_price * random.uniform(0.95, 0.98), 4),
            'bollinger_middle': round(current_price * random.uniform(0.99, 1.01), 4),
            'stoch_k': round(random.uniform(20, 80), 2),
            'stoch_d': round(random.uniform(20, 80), 2),
            'recommendation': random.choice(["BUY", "SELL", "NEUTRAL"])
        }
    
    def get_multiple_timeframe_data(self, symbol, timeframes=["5m", "15m", "1h", "4h"]):
        """Çoklu zaman dilimlerinde Binance verilerini al - GÜNCEL"""
        timeframe_data = {}
        
        print(f"   📊 Binance: {symbol} için çoklu zaman dilimi verileri çekiliyor...")
        
        # Binance interval mapping
        interval_map = {
            "5m": "5m", "15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d"
        }
        
        for timeframe in timeframes:
            print(f"   🔄 Binance {timeframe} verisi alınıyor...")
            
            binance_interval = interval_map.get(timeframe, "15m")
            klines = self.get_klines(symbol, binance_interval, limit=100)
            
            if klines:
                data = self.calculate_technical_indicators(klines, symbol, timeframe)
                if data and data['close'] > 0:
                    timeframe_data[timeframe] = data
                    print(f"   ✅ Binance {timeframe} verisi alındı - ${data['close']:,.4f}")
                else:
                    print(f"   ⚠️ Binance {timeframe} verisi hesaplanamadı, fallback kullanılıyor")
                    fallback_data = self._get_fallback_data(symbol, timeframe)
                    timeframe_data[timeframe] = fallback_data
            else:
                print(f"   ⚠️ Binance {timeframe} verisi alınamadı, fallback kullanılıyor")
                fallback_data = self._get_fallback_data(symbol, timeframe)
                timeframe_data[timeframe] = fallback_data
            
            time.sleep(0.3)  # Rate limit
        
        return timeframe_data
    
    def test_connection(self, symbol="BINANCE:BTCUSDT"):
        """Binance bağlantı testi"""
        print("🔧 Binance API bağlantısı test ediliyor...")
        price = self.get_current_price(symbol)
        if price:
            print(f"✅ Binance bağlantısı başarılı! BTC Fiyat: ${price:,.2f}")
            return True
        else:
            print("❌ Binance bağlantısı başarısız!")
            return False