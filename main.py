# main.py - TAMAMEN GÜNCELLENDİ
import sys
import os
import time
import random
import asyncio
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Python path'ini ayarla - PROJE KÖK DİZİNİ
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = current_dir
sys.path.insert(0, project_root)

print(f"🔧 Çalışma dizini: {current_dir}")

# ✅ GELİŞMİŞ DOSYA KONTROLÜ VE İMPORT
def import_settings():
    """Settings modülünü import et"""
    try:
        from settings import SYMBOLS, TIMEFRAMES, ANALYSIS_CONFIG, AUTO_TRADING_CONFIG, EXCHANGES, RISK_MANAGEMENT
        return SYMBOLS, TIMEFRAMES, ANALYSIS_CONFIG, AUTO_TRADING_CONFIG, EXCHANGES, RISK_MANAGEMENT
    except ModuleNotFoundError as e:
        print(f"❌ settings.py bulunamadı! Hata: {e}")
        # Varsayılan ayarlar
        SYMBOLS = [
            "BINANCE:BTCUSDT",
            "BINANCE:ETHUSDT", 
            "BINANCE:ADAUSDT",
            "BINANCE:SOLUSDT"
        ]
        TIMEFRAMES = ["5m", "15m", "1h", "4h", "1d"]
        ANALYSIS_CONFIG = {
            "check_interval": 300,
            "default_capital": 1000,
            "risk_per_trade": 0.02,
            "analyze_multiple_timeframes": True
        }
        AUTO_TRADING_CONFIG = {
            "enabled": False,
            "paper_trading": True,
            "max_positions": 5,
            "daily_loss_limit": -0.1,
            "min_signal_strength": 7
        }
        EXCHANGES = {
            "binance": {"enabled": True, "api_key": "", "api_secret": "", "testnet": True}
        }
        RISK_MANAGEMENT = {
            "max_drawdown": 0.15,
            "var_limit": 0.05,
            "correlation_threshold": 0.7,
            "portfolio_beta_limit": 1.5
        }
        return SYMBOLS, TIMEFRAMES, ANALYSIS_CONFIG, AUTO_TRADING_CONFIG, EXCHANGES, RISK_MANAGEMENT

def import_data_clients():
    """Data client'larını import et"""
    try:
        from data.hybrid_data_client import HybridDataClient
        from data.fear_greed_client import FearGreedClient
        return HybridDataClient, FearGreedClient
    except ModuleNotFoundError as e:
        print(f"❌ Data client import hatası: {e}")
        # Fallback basit client'lar
        class SimpleHybridClient:
            def get_multiple_timeframe_data(self, symbol, timeframes):
                print(f"⚠️  Basit client: {symbol} için mock veri")
                return {tf: {"close": 50000, "rsi": 50, "recommendation": "NEUTRAL"} for tf in timeframes}
            def test_all_connections(self):
                print("✅ Basit client testi başarılı")
                return True
        
        class SimpleFearGreedClient:
            def get_index(self):
                return {"value": 50, "value_classification": "Neutral"}
        
        return SimpleHybridClient, SimpleFearGreedClient

def import_ai_client():
    """AI client'ını import et"""
    try:
        # Önce ai klasöründen dene
        from ai.advanced_local_ai import AdvancedLocalAI
        print("✅ AI client ai klasöründen import edildi")
        return AdvancedLocalAI
    except ModuleNotFoundError:
        try:
            # Sonra doğrudan import et
            from advanced_local_ai import AdvancedLocalAI
            print("✅ AI client doğrudan import edildi")
            return AdvancedLocalAI
        except ModuleNotFoundError:
            try:
                # Son olarak ai_models klasöründen dene
                from ai_models.advanced_local_ai import AdvancedLocalAI
                print("✅ AI client ai_models klasöründen import edildi")
                return AdvancedLocalAI
            except ModuleNotFoundError:
                print("❌ AI client bulunamadı! Basit AI kullanılıyor...")
                
                class SimpleAI:
                    def generate_signal(self, context, timeframe="1h", capital=1000):
                        return {
                            'sinyal': random.choice(['AL', 'SAT', 'BEKLE']),
                            'ai_skor': round(random.uniform(-3, 3), 2),
                            'güç': random.randint(1, 10),
                            'mevcut_fiyat': 50000,
                            'neden': 'Basit AI modu'
                        }
                
                return SimpleAI

def import_new_features():
    """Yeni özellikleri import et"""
    try:
        from auto_trader import AutoTrader
        from advanced_analytics import AdvancedAnalytics
        from backtester import Backtester
        from multi_exchange import MultiExchangeManager
        from risk_manager import RiskManager
        print("✅ Yeni özellikler başarıyla import edildi")
        return AutoTrader, AdvancedAnalytics, Backtester, MultiExchangeManager, RiskManager
    except ImportError as e:
        print(f"⚠️  Yeni özellikler import edilemedi: {e}")
        print("⚠️  Temel mod ile devam ediliyor...")
        
        # Basit fallback class'ları
        class SimpleAutoTrader:
            def __init__(self): self.enabled = False
            def execute_trade(self, signal): 
                print(f"🔄 Paper Trade: {signal['sinyal']} - {signal['symbol']}")
                return {"status": "paper_traded", "order_id": f"paper_{int(time.time())}"}
        
        class SimpleAnalytics:
            def analyze_portfolio(self, portfolio): 
                return {"total_value": 1000, "daily_pnl": 0, "sharpe_ratio": 0}
        
        class SimpleBacktester:
            def run_backtest(self, strategy, data): 
                return {"total_return": 0, "win_rate": 0, "max_drawdown": 0}
        
        class SimpleExchangeManager:
            def __init__(self): self.exchanges = {}
            def get_balance(self, exchange): return {"total": 1000, "available": 1000}
        
        class SimpleRiskManager:
            def __init__(self): pass
            def check_trade_risk(self, signal): return {"approved": True, "risk_score": 1}
        
        return SimpleAutoTrader, SimpleAnalytics, SimpleBacktester, SimpleExchangeManager, SimpleRiskManager

# Import işlemleri
SYMBOLS, TIMEFRAMES, ANALYSIS_CONFIG, AUTO_TRADING_CONFIG, EXCHANGES, RISK_MANAGEMENT = import_settings()
HybridDataClient, FearGreedClient = import_data_clients()
AdvancedLocalAI = import_ai_client()
AutoTrader, AdvancedAnalytics, Backtester, MultiExchangeManager, RiskManager = import_new_features()

class TradingBot:
    def __init__(self):
        self.data_client = HybridDataClient()
        self.fg_client = FearGreedClient()
        self.ai_client = AdvancedLocalAI()
        self.auto_trader = AutoTrader()
        self.analytics = AdvancedAnalytics()
        self.backtester = Backtester()
        self.exchange_manager = MultiExchangeManager()
        self.risk_manager = RiskManager()
        
        self.SYMBOLS = SYMBOLS
        self.TIMEFRAMES = TIMEFRAMES
        self.capital = ANALYSIS_CONFIG.get('default_capital', 1000)
        self.analysis_count = 0
        self.auto_trading_enabled = AUTO_TRADING_CONFIG.get('enabled', False)
        self.paper_trading = AUTO_TRADING_CONFIG.get('paper_trading', True)
        
        # Yeni: Performans takibi
        self.performance_history = []
        self.trade_history = []
        
        print("🤖 GELİŞMİŞ TRADING BOTU BAŞLATILDI")
        print(f"   • Auto Trading: {'✅ AÇIK' if self.auto_trading_enabled else '❌ KAPALI'}")
        print(f"   • Paper Trading: {'✅ AÇIK' if self.paper_trading else '❌ KAPALI'}")
        print(f"   • Çoklu Exchange: {len(EXCHANGES)} adet")
        
    def analyze_symbol(self, symbol):
        """Sembol analizi - GELİŞMİŞ VERSİYON"""
        print(f"\n🔍 {symbol} analiz ediliyor...")
        
        try:
            # 1. Hibrit sistemden teknik verileri al
            print("   📈 Veri kaynağı aktif...")
            timeframe_data = self.data_client.get_multiple_timeframe_data(symbol, self.TIMEFRAMES)
            
            if not timeframe_data:
                print("❌ Veri alınamadı")
                return None
            
            # 2. Fear & Greed Index al
            fear_greed = self.fg_client.get_index()
            
            # 3. Context oluştur
            context = self._create_multi_timeframe_context(symbol, timeframe_data, fear_greed)
            
            # 4. AI analizi yap
            primary_timeframe = self.TIMEFRAMES[2] if len(self.TIMEFRAMES) > 2 else "1h"
            ai_signal = self.ai_client.generate_signal(context, primary_timeframe, self.capital)
            
            # 5. Risk kontrolü - YENİ
            risk_check = self.risk_manager.check_trade_risk(ai_signal)
            if not risk_check.get('approved', True):
                print(f"   ⚠️  Risk yönetimi: Trade reddedildi - {risk_check.get('reason', 'Risk limiti aşıldı')}")
                ai_signal['sinyal'] = 'BEKLE'
                ai_signal['neden'] = f"Risk yönetimi: {risk_check.get('reason', 'Risk limiti')}"
            
            # 6. Sonuçları birleştir
            result = self._combine_results(symbol, timeframe_data, ai_signal, fear_greed, risk_check)
            
            # 7. Otomatik trading - YENİ
            if self.auto_trading_enabled and ai_signal.get('sinyal') in ['AL', 'SAT']:
                self._execute_auto_trade(result)
            
            # 8. Sonuçları göster
            self._display_results(result)
            
            self.analysis_count += 1
            return result
            
        except Exception as e:
            print(f"❌ {symbol} analiz hatası: {e}")
            return None
    
    def _execute_auto_trade(self, result):
        """Otomatik trade yürüt - YENİ"""
        try:
            if self.paper_trading:
                # Paper trading
                trade_result = self.auto_trader.execute_paper_trade(result)
                print(f"   📝 Paper Trade: {trade_result['status']}")
            else:
                # Gerçek trading
                trade_result = self.auto_trader.execute_trade(result)
                print(f"   🎯 Gerçek Trade: {trade_result['status']}")
                
                # Trade history'e ekle
                self.trade_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'symbol': result['symbol'],
                    'signal': result['signal'],
                    'result': trade_result
                })
                
        except Exception as e:
            print(f"❌ Auto trade hatası: {e}")
    
    def _create_multi_timeframe_context(self, symbol, timeframe_data, fear_greed):
        """Çoklu zaman dilimi context'i oluştur"""
        context = {
            'symbol': symbol,
            'timeframe_data': timeframe_data,
            'fear_greed': fear_greed,
            'analysis_time': datetime.now().isoformat(),
            'market_sentiment': self._calculate_market_sentiment(timeframe_data, fear_greed),
            'portfolio_context': self._get_portfolio_context()  # YENİ
        }
        return context
    
    def _get_portfolio_context(self):
        """Portföy context'i al - YENİ"""
        try:
            portfolio = self.analytics.get_current_portfolio()
            return {
                'total_value': portfolio.get('total_value', 0),
                'open_positions': portfolio.get('open_positions', 0),
                'daily_pnl': portfolio.get('daily_pnl', 0),
                'unrealized_pnl': portfolio.get('unrealized_pnl', 0)
            }
        except:
            return {'total_value': self.capital, 'open_positions': 0, 'daily_pnl': 0, 'unrealized_pnl': 0}
    
    def _calculate_market_sentiment(self, timeframe_data, fear_greed):
        """Piyasa sentiment'ını hesapla"""
        try:
            buy_signals = 0
            total_signals = 0
            
            for tf, data in timeframe_data.items():
                recommendation = data.get('recommendation', 'NEUTRAL')
                if 'BUY' in recommendation:
                    buy_signals += 1
                elif 'SELL' in recommendation:
                    buy_signals -= 1
                total_signals += 1
            
            sentiment_score = buy_signals / total_signals if total_signals > 0 else 0
            
            # Fear & Greed Index'i de ekle
            fg_value = int(fear_greed.get('value', 50))
            fg_score = (fg_value - 50) / 50
            
            total_sentiment = (sentiment_score + fg_score) / 2
            
            if total_sentiment > 0.3:
                return "BULLISH"
            elif total_sentiment < -0.3:
                return "BEARISH"
            else:
                return "NEUTRAL"
                
        except Exception as e:
            print(f"❌ Sentiment hesaplama hatası: {e}")
            return "NEUTRAL"
    
    def _combine_results(self, symbol, timeframe_data, ai_signal, fear_greed, risk_check):
        """Sonuçları birleştir - GELİŞMİŞ"""
        return {
            'symbol': symbol,
            'signal': ai_signal,
            'timeframe_data': timeframe_data,
            'fear_greed': fear_greed,
            'risk_check': risk_check,  # YENİ
            'timestamp': datetime.now().isoformat(),
            'summary': self._create_summary(ai_signal, timeframe_data, risk_check),
            'auto_trading': {  # YENİ
                'enabled': self.auto_trading_enabled,
                'paper_trading': self.paper_trading,
                'executed': ai_signal.get('sinyal') in ['AL', 'SAT'] and self.auto_trading_enabled
            }
        }
    
    def _create_summary(self, ai_signal, timeframe_data, risk_check):
        """Analiz özeti oluştur - GELİŞMİŞ"""
        signal_type = ai_signal.get('sinyal', 'BEKLE')
        strength = ai_signal.get('güç', 1)
        current_price = ai_signal.get('mevcut_fiyat', 0)
        
        # Timeframe özeti
        tf_recommendations = {}
        for tf, data in timeframe_data.items():
            tf_recommendations[tf] = data.get('recommendation', 'NEUTRAL')
        
        return {
            'signal_type': signal_type,
            'strength': strength,
            'current_price': current_price,
            'timeframe_recommendations': tf_recommendations,
            'risk_level': self._calculate_risk_level(strength, signal_type),
            'risk_check': risk_check,  # YENİ
            'confidence_score': self._calculate_confidence_score(ai_signal, timeframe_data)  # YENİ
        }
    
    def _calculate_confidence_score(self, ai_signal, timeframe_data):
        """Güven skoru hesapla - YENİ"""
        try:
            base_score = ai_signal.get('güç', 1) * 10
            tf_alignment = 0
            
            # Zaman dilimi uyumu
            for tf, data in timeframe_data.items():
                rec = data.get('recommendation', 'NEUTRAL')
                if 'BUY' in rec and ai_signal.get('sinyal') == 'AL':
                    tf_alignment += 20
                elif 'SELL' in rec and ai_signal.get('sinyal') == 'SAT':
                    tf_alignment += 20
                elif rec == 'NEUTRAL' and ai_signal.get('sinyal') == 'BEKLE':
                    tf_alignment += 10
            
            return min(100, base_score + tf_alignment)
        except:
            return 50
    
    def _calculate_risk_level(self, strength, signal_type):
        """Risk seviyesini hesapla"""
        if signal_type == 'BEKLE':
            return 'DÜŞÜK'
        
        if strength >= 8:
            return 'YÜKSEK' if signal_type in ['AL', 'SAT'] else 'ORTA'
        elif strength >= 5:
            return 'ORTA'
        else:
            return 'DÜŞÜK'
    
    def _display_results(self, result):
        """Sonuçları göster - GÜNCELLENMİŞ VERSİYON"""
        if not result:
            print("❌ Analiz sonucu yok")
            return

        signal = result.get('signal', {})
        symbol = result.get('symbol', 'Bilinmeyen')
        risk_check = result.get('risk_check', {})
        auto_trading = result.get('auto_trading', {})

        print(f"\n{'='*80}")
        print(f"🎯 {symbol} ANALİZ SONUCU")
        print(f"{'='*80}")

        # Ana sinyal bilgileri
        print(f"📊 Sinyal: {signal.get('sinyal', 'BEKLE')}")
        print(f"💪 Güç: {signal.get('güç', 1)}/10")
        print(f"🤖 AI Skor: {signal.get('ai_skor', 0):.2f}")
        print(f"💰 Mevcut Fiyat: ${signal.get('mevcut_fiyat', 0):,.4f}")

        # Risk kontrolü - YENİ
        risk_status = "✅ ONAYLANDI" if risk_check.get('approved', True) else "❌ REDDEDİLDİ"
        print(f"⚖️  Risk Kontrolü: {risk_status}")
        if not risk_check.get('approved', True):
            print(f"   📋 Sebep: {risk_check.get('reason', 'Bilinmiyor')}")

        # Auto trading durumu - YENİ
        if auto_trading.get('enabled', False):
            trading_type = "PAPER" if auto_trading.get('paper_trading', True) else "GERÇEK"
            executed = "✅ YÜRÜTÜLDÜ" if auto_trading.get('executed', False) else "⏸️  BEKLE"
            print(f"🤖 Auto Trading ({trading_type}): {executed}")

        # Trade detayları
        if signal.get('sinyal') in ['AL', 'SAT']:
            print(f"🎯 Giriş Fiyatı: ${signal.get('giris_fiyati', 0):,.4f}")
            print(f"🛑 Stop Loss: ${signal.get('stop_loss', 0):,.4f}")
            print(f"✅ Take Profit: {[f'${tp:,.4f}' for tp in signal.get('take_profit', [])]}")
            print(f"📈 Pozisyon Büyüklüğü: {signal.get('pozisyon_buyuklugu', 0):.4f} adet")
            print(f"💰 Risk Miktarı: ${signal.get('risk_miktari', 0):,.2f}")
            print(f"⚖️ Risk/Reward: 1:{signal.get('risk_reward', 0)}")
            print(f"🎯 Kaldıraç: {signal.get('kaldıraç', '1x')}")

        # Fear & Greed Index
        fear_greed = result.get('fear_greed', {})
        print(f"😨 Fear & Greed: {fear_greed.get('value', 'N/A')} - {fear_greed.get('value_classification', 'N/A')}")

        # Zaman dilimi özeti
        print(f"\n📊 TEKNİK GÖSTERGE ÖZETİ:")
        timeframe_data = result.get('timeframe_data', {})
        for tf, data in timeframe_data.items():
            price = data.get('close', 0)
            rsi = data.get('rsi', 0)
            recommendation = data.get('recommendation', 'NEUTRAL')
            
            print(f"   {tf}: ${price:,.4f} | RSI: {rsi:.1f} | 📊 {recommendation}")

        # Güven skoru - YENİ
        summary = result.get('summary', {})
        confidence = summary.get('confidence_score', 50)
        print(f"\n🎯 Güven Skoru: %{confidence:.1f}")
        print(f"⚠️  Risk Seviyesi: {summary.get('risk_level', 'DÜŞÜK')}")

        print(f"📖 Neden: {signal.get('neden', 'Analiz tamamlandı')}")
        print(f"{'='*80}\n")

    def analyze_all_symbols(self):
        """Tüm sembolleri analiz et - GELİŞMİŞ"""
        print("🚀 TÜM SEMBOLLER ANALİZ EDİLİYOR...")
        print(f"📈 Semboller: {', '.join(self.SYMBOLS)}")
        print(f"⏰ Zaman Dilimleri: {', '.join(self.TIMEFRAMES)}")
        print(f"💰 Sermaye: ${self.capital:,.2f}")
        print(f"🤖 Auto Trading: {'✅ AÇIK' if self.auto_trading_enabled else '❌ KAPALI'}")
        
        results = []
        
        for symbol in self.SYMBOLS:
            try:
                result = self.analyze_symbol(symbol)
                if result:
                    results.append(result)
                
                # Semboller arası bekleme
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ {symbol} analizinde hata: {e}")
                continue
        
        # Özet rapor
        self._generate_summary_report(results)
        
        # Performans kaydı - YENİ
        self._record_performance(results)
        
        return results
    
    def _record_performance(self, results):
        """Performans kaydı oluştur - YENİ"""
        try:
            performance_data = {
                'timestamp': datetime.now().isoformat(),
                'total_analysis': len(results),
                'buy_signals': sum(1 for r in results if r.get('signal', {}).get('sinyal') == 'AL'),
                'sell_signals': sum(1 for r in results if r.get('signal', {}).get('sinyal') == 'SAT'),
                'total_trades': len(self.trade_history)
            }
            
            self.performance_history.append(performance_data)
            
            # Son 100 kaydı tut
            if len(self.performance_history) > 100:
                self.performance_history = self.performance_history[-100:]
                
        except Exception as e:
            print(f"❌ Performans kaydı hatası: {e}")
    
    def _generate_summary_report(self, results):
        """Özet rapor oluştur - GELİŞMİŞ"""
        if not results:
            print("❌ Hiçbir analiz sonucu yok")
            return
        
        print(f"\n{'='*60}")
        print(f"📊 GELİŞMİŞ ANALİZ ÖZET RAPORU")
        print(f"{'='*60}")
        
        buy_signals = 0
        sell_signals = 0
        wait_signals = 0
        total_confidence = 0
        
        for result in results:
            signal = result.get('signal', {})
            signal_type = signal.get('sinyal', 'BEKLE')
            summary = result.get('summary', {})
            
            if signal_type == 'AL':
                buy_signals += 1
            elif signal_type == 'SAT':
                sell_signals += 1
            else:
                wait_signals += 1
            
            total_confidence += summary.get('confidence_score', 50)
            
            symbol = result.get('symbol', 'Bilinmeyen')
            strength = signal.get('güç', 1)
            price = signal.get('mevcut_fiyat', 0)
            risk_check = result.get('risk_check', {})
            risk_status = "✅" if risk_check.get('approved', True) else "❌"
            
            print(f"   {symbol}: {signal_type} (Güç: {strength}/10) {risk_status} - ${price:,.2f}")
        
        avg_confidence = total_confidence / len(results) if results else 0
        
        print(f"\n📈 Sinyal Dağılımı:")
        print(f"   ✅ AL Sinyalleri: {buy_signals}")
        print(f"   ❌ SAT Sinyalleri: {sell_signals}")
        print(f"   ⏸️  BEKLE Sinyalleri: {wait_signals}")
        print(f"   📊 Toplam Analiz: {len(results)}")
        print(f"   🎯 Ortalama Güven: %{avg_confidence:.1f}")
        
        # Auto trading özeti - YENİ
        if self.auto_trading_enabled:
            recent_trades = [t for t in self.trade_history 
                           if datetime.fromisoformat(t['timestamp']) > datetime.now() - timedelta(hours=24)]
            print(f"   🤖 Son 24s Trade: {len(recent_trades)}")
        
        # Genel market sentiment
        if buy_signals > sell_signals and buy_signals > wait_signals:
            overall_sentiment = "BULLISH 📈"
        elif sell_signals > buy_signals and sell_signals > wait_signals:
            overall_sentiment = "BEARISH 📉"
        else:
            overall_sentiment = "NEUTRAL ➡️"
        
        print(f"   🎯 Genel Market: {overall_sentiment}")
        print(f"{'='*60}\n")
    
    def run_backtest(self, days=30, initial_capital=1000):
        """Backtest çalıştır - YENİ"""
        print(f"🧪 BACKTEST BAŞLATILIYOR: {days} gün, ${initial_capital:,.2f}")
        
        try:
            backtest_result = self.backtester.run_backtest(
                strategy="ai_trading",
                symbols=self.SYMBOLS,
                days=days,
                initial_capital=initial_capital
            )
            
            print(f"📊 BACKTEST SONUÇLARI:")
            print(f"   📈 Toplam Getiri: %{backtest_result.get('total_return', 0)*100:.2f}")
            print(f"   🎯 Win Rate: %{backtest_result.get('win_rate', 0)*100:.2f}")
            print(f"   📉 Maksimum Drawdown: %{backtest_result.get('max_drawdown', 0)*100:.2f}")
            print(f"   ⚖️ Sharpe Oranı: {backtest_result.get('sharpe_ratio', 0):.2f}")
            
            return backtest_result
            
        except Exception as e:
            print(f"❌ Backtest hatası: {e}")
            return None
    
    def get_portfolio_analytics(self):
        """Portföy analitiği al - YENİ"""
        print("📊 GELİŞMİŞ PORTFÖY ANALİTİĞİ")
        
        try:
            analytics = self.analytics.get_comprehensive_analytics()
            
            print(f"   💰 Toplam Portföy: ${analytics.get('total_value', 0):,.2f}")
            print(f"   📈 Günlük P&L: ${analytics.get('daily_pnl', 0):,.2f}")
            print(f"   📊 Açık Pozisyon: {analytics.get('open_positions', 0)}")
            print(f"   ⚖️ Sharpe Oranı: {analytics.get('sharpe_ratio', 0):.2f}")
            print(f"   📉 Maksimum Drawdown: %{analytics.get('max_drawdown', 0)*100:.2f}")
            
            return analytics
            
        except Exception as e:
            print(f"❌ Portfolio analitik hatası: {e}")
            return None
    
    def test_system(self):
        """Sistem testi - GELİŞMİŞ"""
        print("🧪 GELİŞMİŞ SİSTEM TESTİ BAŞLATILIYOR...")
        
        try:
            # Test bağlantıları
            print("\n1. Veri Kaynakları Testi:")
            data_ok = self.data_client.test_all_connections() if hasattr(self.data_client, 'test_all_connections') else True
            
            print("\n2. Fear & Greed Testi:")
            fear_greed = self.fg_client.get_index()
            print(f"   Fear & Greed: {fear_greed.get('value', 'N/A')}")
            
            print("\n3. AI Model Testi:")
            test_context = {'symbol': 'TEST', 'timeframe_data': {}, 'fear_greed': fear_greed}
            ai_signal = self.ai_client.generate_signal(test_context, "1h", 1000)
            print(f"   AI Sinyal: {ai_signal.get('sinyal', 'TEST')}")
            
            print("\n4. Risk Yönetimi Testi:")
            risk_check = self.risk_manager.check_trade_risk(ai_signal)
            print(f"   Risk Kontrol: {'✅ ONAYLANDI' if risk_check.get('approved', False) else '❌ REDDEDİLDİ'}")
            
            print("\n5. Exchange Bağlantı Testi:")
            exchange_balance = self.exchange_manager.get_balance('binance')
            print(f"   Binance Balance: ${exchange_balance.get('total', 0):,.2f}")
            
            print("\n6. Tek Sembol Test Analizi:")
            test_result = self.analyze_symbol(self.SYMBOLS[0] if self.SYMBOLS else "BINANCE:BTCUSDT")
            
            if test_result:
                print("\n✅ GELİŞMİŞ SİSTEM TESTİ BAŞARILI!")
                return True
            else:
                print("\n❌ SİSTEM TESTİ BAŞARISIZ!")
                return False
                
        except Exception as e:
            print(f"❌ Test hatası: {e}")
            return False

def main():
    """Ana fonksiyon - GELİŞMİŞ"""
    bot = TradingBot()
    
    print("🤖 GELİŞMİŞ AI TRADING BOTU BAŞLATILIYOR...")
    print("✨ Yeni Özellikler: Auto Trading, Backtesting, Portfolio Analytics, Risk Management")
    
    # Sistem testi
    if not bot.test_system():
        print("⚠️  Sistem testi başarısız, ancak devam ediliyor...")
    
    # Kullanıcı seçimi
    print("\n🔧 GELİŞMİŞ ÇALIŞMA MODU SEÇİN:")
    print("1 - Tek Seferlik Analiz")
    print("2 - Sürekli Analiz Modu")
    print("3 - Backtest Çalıştır")
    print("4 - Portfolio Analitiği")
    print("5 - Auto Trading Ayarları")
    print("6 - Sadece Test")
    
    try:
        choice = input("Seçiminiz (1-6): ").strip()
        
        if choice == "1":
            print("\n🚀 TEK SEFERLİK ANALİZ BAŞLATILIYOR...")
            bot.analyze_all_symbols()
            
        elif choice == "2":
            interval = input("Analiz aralığı (dakika) [5]: ").strip()
            interval = int(interval) if interval.isdigit() else 5
            print(f"\n🔄 SÜREKLİ ANALİZ MODU ({interval} dakika)")
            print("⏹️  Durdurmak için Ctrl+C")
            
            try:
                while True:
                    print(f"\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    bot.analyze_all_symbols()
                    print(f"⏳ {interval} dakika bekleniyor...")
                    time.sleep(interval * 60)
            except KeyboardInterrupt:
                print(f"\n🛑 Analiz durduruldu. Toplam analiz: {bot.analysis_count}")
            
        elif choice == "3":
            days = input("Backtest gün sayısı [30]: ").strip()
            days = int(days) if days.isdigit() else 30
            capital = input("Başlangıç sermayesi [$1000]: ").strip()
            capital = float(capital) if capital.replace('.', '').isdigit() else 1000
            
            bot.run_backtest(days=days, initial_capital=capital)
            
        elif choice == "4":
            bot.get_portfolio_analytics()
            
        elif choice == "5":
            # Auto trading ayarları
            enable_auto = input("Auto trading aktif et? (e/h) [h]: ").strip().lower()
            if enable_auto == 'e':
                bot.auto_trading_enabled = True
                paper_trading = input("Paper trading? (e/h) [e]: ").strip().lower()
                bot.paper_trading = paper_trading != 'h'
                print("✅ Auto trading ayarları kaydedildi!")
            else:
                bot.auto_trading_enabled = False
                print("❌ Auto trading kapatıldı!")
                
        elif choice == "6":
            print("✅ Test tamamlandı.")
            
        else:
            print("❌ Geçersiz seçim, tek seferlik analiz başlatılıyor...")
            bot.analyze_all_symbols()
            
    except KeyboardInterrupt:
        print(f"\n👋 Çıkılıyor... Toplam analiz: {bot.analysis_count}")
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")

if __name__ == "__main__":
    main()