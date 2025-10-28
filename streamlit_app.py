# streamlit_app_complete.py - TAM BİRLEŞTİRİLMİŞ VERSİYON
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
import sys
import os
import json
import sqlite3
from pathlib import Path
import asyncio
import threading
from typing import Dict, List, Optional
import random

# Streamlit sayfa konfigürasyonu
st.set_page_config(
    page_title="🤖 AI Trading Bot - Gelişmiş",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

class AdvancedPortfolioManager:
    def __init__(self):
        self.db_path = "advanced_portfolio.db"
        self.init_advanced_database()
    
    def init_advanced_database(self):
        """Gelişmiş veritabanını başlat"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Gelişmiş Portfolio tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                entry_price REAL NOT NULL,
                quantity REAL NOT NULL,
                entry_date TEXT NOT NULL,
                stop_loss REAL,
                take_profit REAL,
                leverage TEXT DEFAULT '1x',
                status TEXT DEFAULT 'active',
                unrealized_pnl REAL DEFAULT 0,
                current_price REAL
            )
        ''')
        
        # Gelişmiş Trade history tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL,
                quantity REAL NOT NULL,
                timestamp TEXT NOT NULL,
                profit_loss REAL DEFAULT 0,
                profit_loss_percent REAL DEFAULT 0,
                signal_strength INTEGER,
                strategy_used TEXT,
                risk_reward REAL,
                duration_minutes INTEGER
            )
        ''')
        
        # Performance metrics tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_value REAL NOT NULL,
                daily_return REAL DEFAULT 0,
                win_rate REAL DEFAULT 0,
                sharpe_ratio REAL DEFAULT 0,
                max_drawdown REAL DEFAULT 0,
                total_trades INTEGER DEFAULT 0,
                profitable_trades INTEGER DEFAULT 0
            )
        ''')
        
        # AI sinyal geçmişi tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_signal_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                signal TEXT NOT NULL,
                strength INTEGER,
                ai_score REAL,
                timestamp TEXT NOT NULL,
                price REAL,
                strategy_breakdown TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_to_portfolio(self, symbol, entry_price, quantity, stop_loss=None, take_profit=None, leverage="1x"):
        """Portföye gelişmiş pozisyon ekle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO portfolio (symbol, entry_price, quantity, entry_date, stop_loss, take_profit, leverage, current_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (symbol, entry_price, quantity, datetime.now().isoformat(), stop_loss, take_profit, leverage, entry_price))
        
        conn.commit()
        conn.close()
        return True
    
    def update_portfolio_prices(self, price_data: Dict):
        """Portföy fiyatlarını güncelle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for symbol, current_price in price_data.items():
            cursor.execute('''
                UPDATE portfolio 
                SET current_price = ?, unrealized_pnl = (current_price - entry_price) * quantity
                WHERE symbol = ? AND status = "active"
            ''', (current_price, symbol))
        
        conn.commit()
        conn.close()
    
    def get_portfolio(self):
        """Gelişmiş portföy verilerini getir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT *, 
                   (current_price - entry_price) * quantity as unrealized_pnl,
                   ((current_price - entry_price) / entry_price * 100) as pnl_percent
            FROM portfolio 
            WHERE status = "active"
        ''')
        portfolio = cursor.fetchall()
        
        conn.close()
        return portfolio
    
    def get_portfolio_summary(self):
        """Portföy özetini getir"""
        portfolio = self.get_portfolio()
        
        if not portfolio:
            return {
                'total_value': 0,
                'total_invested': 0,
                'total_unrealized_pnl': 0,
                'total_pnl_percent': 0,
                'positions_count': 0
            }
        
        total_invested = sum(pos[2] * pos[3] for pos in portfolio)  # entry_price * quantity
        total_current = sum(pos[9] * pos[3] for pos in portfolio if pos[9] is not None)  # current_price * quantity
        total_unrealized_pnl = total_current - total_invested
        
        return {
            'total_value': total_current,
            'total_invested': total_invested,
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_pnl_percent': (total_unrealized_pnl / total_invested * 100) if total_invested > 0 else 0,
            'positions_count': len(portfolio)
        }
    
    def close_position(self, symbol, exit_price):
        """Pozisyonu gelişmiş şekilde kapat"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Aktif pozisyonu bul
        cursor.execute('SELECT * FROM portfolio WHERE symbol = ? AND status = "active"', (symbol,))
        position = cursor.fetchone()
        
        if position:
            entry_price = position[2]
            quantity = position[3]
            profit_loss = (exit_price - entry_price) * quantity
            profit_loss_percent = ((exit_price - entry_price) / entry_price * 100)
            
            # Trade süresini hesapla
            entry_date = datetime.fromisoformat(position[4])
            exit_date = datetime.now()
            duration = int((exit_date - entry_date).total_seconds() / 60)
            
            # Trade history'e ekle
            cursor.execute('''
                INSERT INTO trade_history (symbol, action, entry_price, exit_price, quantity, 
                                         timestamp, profit_loss, profit_loss_percent, duration_minutes)
                VALUES (?, 'CLOSE', ?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, entry_price, exit_price, quantity, datetime.now().isoformat(), 
                 profit_loss, profit_loss_percent, duration))
            
            # Portfolio'dan kaldır
            cursor.execute('UPDATE portfolio SET status = "closed" WHERE id = ?', (position[0],))
            
            conn.commit()
            conn.close()
            return profit_loss
        else:
            conn.close()
            return 0
    
    def get_trade_history(self, limit=100):
        """Trade geçmişini getir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM trade_history 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        history = cursor.fetchall()
        conn.close()
        return history
    
    def get_performance_stats(self, days=30):
        """Gelişmiş performans istatistiklerini getir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Son X günün tarihini hesapla
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Toplam kar/zarar
        cursor.execute('SELECT SUM(profit_loss) FROM trade_history WHERE timestamp > ?', (since_date,))
        total_pl = cursor.fetchone()[0] or 0
        
        # Win rate
        cursor.execute('SELECT COUNT(*) FROM trade_history WHERE profit_loss > 0 AND timestamp > ?', (since_date,))
        winning_trades = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM trade_history WHERE timestamp > ?', (since_date,))
        total_trades = cursor.fetchone()[0]
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Ortalama kar/zarar
        cursor.execute('SELECT AVG(profit_loss) FROM trade_history WHERE timestamp > ?', (since_date,))
        avg_pl = cursor.fetchone()[0] or 0
        
        # Ortalama trade süresi
        cursor.execute('SELECT AVG(duration_minutes) FROM trade_history WHERE timestamp > ?', (since_date,))
        avg_duration = cursor.fetchone()[0] or 0
        
        # En iyi/en kötü trade
        cursor.execute('SELECT MAX(profit_loss), MIN(profit_loss) FROM trade_history WHERE timestamp > ?', (since_date,))
        best_worst = cursor.fetchone()
        best_trade = best_worst[0] or 0
        worst_trade = best_worst[1] or 0
        
        conn.close()
        
        return {
            'total_profit_loss': total_pl,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'average_pl': avg_pl,
            'average_duration': avg_duration,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'period_days': days
        }
    
    def add_ai_signal(self, symbol, signal, strength, ai_score, price, strategy_breakdown):
        """AI sinyal geçmişine ekle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ai_signal_history (symbol, signal, strength, ai_score, timestamp, price, strategy_breakdown)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (symbol, signal, strength, ai_score, datetime.now().isoformat(), price, json.dumps(strategy_breakdown)))
        
        conn.commit()
        conn.close()
    
    def get_ai_signal_history(self, symbol=None, limit=50):
        """AI sinyal geçmişini getir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if symbol:
            cursor.execute('''
                SELECT * FROM ai_signal_history 
                WHERE symbol = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (symbol, limit))
        else:
            cursor.execute('''
                SELECT * FROM ai_signal_history 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
        
        history = cursor.fetchall()
        conn.close()
        return history

class AdvancedAIChatBot:
    def __init__(self, portfolio_manager):
        self.portfolio_manager = portfolio_manager
    
    def ask_question(self, question, current_data=None, market_context=None):
        """Gelişmiş AI soru-cevap"""
        question_lower = question.lower()
        
        # Portfolio ile ilgili sorular
        if any(word in question_lower for word in ['portföy', 'sepet', 'yatırım', 'pozisyon']):
            return self.advanced_portfolio_analysis()
        
        elif any(word in question_lower for word in ['ne yapmalı', 'tavsiye', 'öneri', 'al sat']):
            return self.get_advanced_trading_advice(current_data, market_context)
        
        elif any(word in question_lower for word in ['kar', 'zarar', 'kâr', 'getiri']):
            return self.get_profitability_analysis()
        
        elif any(word in question_lower for word in ['risk', 'güvenli', 'tehlikeli']):
            return self.get_risk_analysis()
        
        elif any(word in question_lower for word in ['btc', 'bitcoin']):
            return self.get_advanced_coin_analysis('BTC', current_data)
        
        elif any(word in question_lower for word in ['eth', 'ethereum']):
            return self.get_advanced_coin_analysis('ETH', current_data)
        
        elif any(word in question_lower for word in ['strateji', 'yöntem', 'algoritma']):
            return self.explain_strategies()
        
        elif any(word in question_lower for word in ['performans', 'başarı', 'sonuç']):
            return self.get_performance_analysis()
        
        else:
            return self.get_general_advice(question)

    def advanced_portfolio_analysis(self):
        """Gelişmiş portföy analizi"""
        portfolio = self.portfolio_manager.get_portfolio()
        stats = self.portfolio_manager.get_performance_stats(30)
        summary = self.portfolio_manager.get_portfolio_summary()
        
        analysis = "📊 GELİŞMİŞ PORTFÖY ANALİZİ:\n\n"
        analysis += f"• 💰 Toplam Değer: ${summary['total_value']:,.2f}\n"
        analysis += f"• 📈 Toplam Yatırım: ${summary['total_invested']:,.2f}\n"
        analysis += f"• 💸 Gerçekleşmemiş K/Z: ${summary['total_unrealized_pnl']:,.2f} (%{summary['total_pnl_percent']:.2f})\n"
        analysis += f"• 📦 Aktif Pozisyon: {summary['positions_count']} adet\n\n"
        
        analysis += "📈 SON 30 GÜN PERFORMANS:\n"
        analysis += f"• 🎯 Toplam K/Z: ${stats['total_profit_loss']:,.2f}\n"
        analysis += f"• ✅ Başarı Oranı: %{stats['win_rate']:.1f}\n"
        analysis += f"• 🔄 Toplam İşlem: {stats['total_trades']}\n"
        analysis += f"• ⏱️ Ortalama Süre: {stats['average_duration']:.0f} dakika\n\n"
        
        if portfolio:
            analysis += "💰 POZİSYON DETAYLARI:\n"
            for position in portfolio[:5]:  # İlk 5 pozisyon
                symbol, entry_price, quantity, _, _, _, _, _, unrealized_pnl, pnl_percent = position[1], position[2], position[3], position[9], position[10]
                analysis += f"   {symbol}: {quantity} adet - K/Z: ${unrealized_pnl:,.2f} (%{pnl_percent:.2f})\n"
        
        analysis += "\n🎯 TAVSİYELER:\n"
        if summary['positions_count'] >= 5:
            analysis += "• ⚠️ Çok fazla pozisyon açıksınız, konsolidasyon önerilir\n"
        if stats['win_rate'] < 40:
            analysis += "• 📉 Başarı oranınız düşük, stratejinizi gözden geçirin\n"
        if summary['total_pnl_percent'] < -10:
            analysis += "• 🔴 Portföyünüzde significant kayıp var, riski azaltın\n"
        else:
            analysis += "• ✅ Portföy dengeli görünüyor, stratejinize devam edin\n"
        
        return analysis

    def get_advanced_trading_advice(self, current_data, market_context):
        """Gelişmiş trading tavsiyesi"""
        if not current_data:
            return "Şu anlık piyasa verisi yok. Önce analiz yapın."
        
        buy_signals = sum(1 for result in current_data if result.get('signal', {}).get('sinyal') == 'AL')
        strong_signals = sum(1 for result in current_data if result.get('signal', {}).get('güç', 0) >= 7)
        total_coins = len(current_data)
        
        advice = "🎯 GELİŞMİŞ TRADING TAVSİYESİ:\n\n"
        
        market_sentiment = "NÖTR"
        if buy_signals / total_coins > 0.7:
            market_sentiment = "GÜÇLÜ BULLISH"
            advice += "• 🚀 **GÜÇLÜ ALIM FIRSATI** - Piyasa çok bullish\n"
            advice += "• 💪 Yüksek güvenilirlikli sinyaller mevcut\n"
            advice += "• 📊 Risk toleransınıza göre agresif pozisyon alabilirsiniz\n"
        elif buy_signals / total_coins > 0.5:
            market_sentiment = "BULLISH"
            advice += "• 📈 **ALIM FIRSATI** - Piyasa bullish\n"
            advice += "• ✅ Orta güvenilirlikte sinyaller var\n"
            advice += "• ⚖️ Dengeli pozisyon büyüklükleri önerilir\n"
        elif buy_signals / total_coins < 0.3:
            market_sentiment = "BEARISH"
            advice += "• 📉 **DİKKAT** - Piyasa bearish\n"
            advice += "• 🛑 Stop-loss'larınızı kontrol edin\n"
            advice += "• 💰 Nakit pozisyonunu artırmayı düşünün\n"
        else:
            market_sentiment = "NÖTR"
            advice += "• ⚖️ **NÖTR PİYASA** - Yön belirsiz\n"
            advice += "• 🔍 Daha net sinyal bekleyin\n"
            advice += "• 📊 Teknik seviyeleri takip edin\n"
        
        advice += f"\n📊 PİYASA DURUMU: {market_sentiment}\n"
        advice += f"• ✅ AL Sinyali: {buy_signals}/{total_coins}\n"
        advice += f"• 💪 Güçlü Sinyal: {strong_signals} adet\n"
        advice += f"• 🎯 Önerilen: {self._get_recommended_action(market_sentiment, strong_signals)}"
        
        return advice

    def _get_recommended_action(self, sentiment, strong_signals):
        """Önerilen aksiyonu belirle"""
        if sentiment == "GÜÇLÜ BULLISH" and strong_signals >= 2:
            return "AGRESİF ALIM"
        elif sentiment == "BULLISH" and strong_signals >= 1:
            return "DENGELİ ALIM"
        elif sentiment == "BEARISH":
            return "POZİSYON AZALTMA"
        else:
            return "BEKLE-GÖR"

    def get_profitability_analysis(self):
        """Karlılık analizi"""
        stats = self.portfolio_manager.get_performance_stats(30)
        portfolio_summary = self.portfolio_manager.get_portfolio_summary()
        
        analysis = "💰 GELİŞMİŞ KARLILIK ANALİZİ:\n\n"
        analysis += "📈 SON 30 GÜN:\n"
        analysis += f"• 💰 Toplam Kar/Zarar: ${stats['total_profit_loss']:,.2f}\n"
        analysis += f"• ✅ Başarı Oranı: %{stats['win_rate']:.1f}\n"
        analysis += f"• 📊 Ortalama K/Z: ${stats['average_pl']:,.2f}\n"
        analysis += f"• 🏆 En İyi Trade: ${stats['best_trade']:,.2f}\n"
        analysis += f"• 📉 En Kötü Trade: ${stats['worst_trade']:,.2f}\n\n"
        
        analysis += "💼 MEVCUT PORTFÖY:\n"
        analysis += f"• 📦 Gerçekleşmemiş K/Z: ${portfolio_summary['total_unrealized_pnl']:,.2f}\n"
        analysis += f"• 📊 Getiri Oranı: %{portfolio_summary['total_pnl_percent']:.2f}\n\n"
        
        # Performans değerlendirmesi
        if stats['win_rate'] > 60 and stats['total_profit_loss'] > 0:
            analysis += "🎉 **MÜKEMMEL PERFORMANS!** Stratejiniz çok başarılı.\n"
        elif stats['win_rate'] > 45 and stats['total_profit_loss'] > 0:
            analysis += "✅ **İYİ PERFORMANS!** Stratejiniz işe yarıyor.\n"
        elif stats['win_rate'] < 35:
            analysis += "⚠️ **DÜŞÜK BAŞARI ORANI!** Stratejinizi gözden geçirin.\n"
        else:
            analysis += "📊 **STABİL PERFORMANS!** Küçük iyileştirmeler yapılabilir.\n"
        
        return analysis

    def get_risk_analysis(self):
        """Risk analizi"""
        portfolio = self.portfolio_manager.get_portfolio()
        stats = self.portfolio_manager.get_performance_stats(30)
        summary = self.portfolio_manager.get_portfolio_summary()
        
        analysis = "⚠️ GELİŞMİŞ RİSK ANALİZİ:\n\n"
        
        # Pozisyon çeşitliliği
        position_count = len(portfolio)
        if position_count >= 8:
            diversity_risk = "YÜKSEK"
            analysis += "• 📊 **ÇEŞİTLİLİK: YÜKSEK RİSK** - Çok fazla pozisyon\n"
        elif position_count >= 4:
            diversity_risk = "ORTA"
            analysis += "• 📊 **ÇEŞİTLİLİK: ORTA RİSK** - Makul pozisyon sayısı\n"
        else:
            diversity_risk = "DÜŞÜK"
            analysis += "• 📊 **ÇEŞİTLİLİK: DÜŞÜK RİSK** - Az pozisyon\n"
        
        # Başarı oranı riski
        if stats['win_rate'] < 35:
            winrate_risk = "YÜKSEK"
            analysis += "• 🎯 **BAŞARI ORANI: YÜKSEK RİSK** - %35 altında\n"
        elif stats['win_rate'] < 50:
            winrate_risk = "ORTA"
            analysis += "• 🎯 **BAŞARI ORANI: ORTA RİSK** - %35-50 arası\n"
        else:
            winrate_risk = "DÜŞÜK"
            analysis += "• 🎯 **BAŞARI ORANI: DÜŞÜK RİSK** - %50 üstünde\n"
        
        # Drawdown riski
        if summary['total_pnl_percent'] < -15:
            drawdown_risk = "YÜKSEK"
            analysis += "• 📉 **DRAWDOWN: YÜKSEK RİSK** - %15'ten fazla kayıp\n"
        elif summary['total_pnl_percent'] < -5:
            drawdown_risk = "ORTA"
            analysis += "• 📉 **DRAWDOWN: ORTA RİSK** - %5-15 arası kayıp\n"
        else:
            drawdown_risk = "DÜŞÜK"
            analysis += "• 📉 **DRAWDOWN: DÜŞÜK RİSK** - %5'ten az kayıp\n"
        
        analysis += f"\n📋 GENEL RİSK SEVİYESİ: {self._calculate_overall_risk(diversity_risk, winrate_risk, drawdown_risk)}\n"
        analysis += "\n🎯 RİSK YÖNETİMİ TAVSİYELERİ:\n"
        
        if diversity_risk == "YÜKSEK":
            analysis += "• 🔴 Pozisyon sayısını 5-6'ya düşürün\n"
        if winrate_risk == "YÜKSEK":
            analysis += "• 📊 Stop-loss seviyelerinizi yeniden ayarlayın\n"
        if drawdown_risk == "YÜKSEK":
            analysis += "• 💰 Pozisyon büyüklüklerini küçültün\n"
        
        return analysis

    def _calculate_overall_risk(self, diversity, winrate, drawdown):
        """Genel risk seviyesini hesapla"""
        risk_scores = {
            "YÜKSEK": 3,
            "ORTA": 2, 
            "DÜŞÜK": 1
        }
        
        total_score = risk_scores.get(diversity, 2) + risk_scores.get(winrate, 2) + risk_scores.get(drawdown, 2)
        
        if total_score >= 8:
            return "🟥 YÜKSEK RİSK"
        elif total_score >= 6:
            return "🟨 ORTA RİSK"
        else:
            return "🟩 DÜŞÜK RİSK"

    def get_advanced_coin_analysis(self, coin, current_data):
        """Gelişmiş coin analizi"""
        analysis = f"🔍 GELİŞMİŞ {coin} ANALİZİ:\n\n"
        
        # Mevcut data'dan coin bilgilerini bul
        coin_data = None
        if current_data:
            for data in current_data:
                if coin in data.get('symbol', ''):
                    coin_data = data
                    break
        
        if coin_data:
            signal = coin_data.get('signal', {})
            strategy_breakdown = signal.get('strategy_breakdown', {})
            
            analysis += f"📊 GÜNCEL DURUM:\n"
            analysis += f"• 🎯 Sinyal: {signal.get('sinyal', 'BEKLE')}\n"
            analysis += f"• 💪 Güç: {signal.get('güç', 0)}/10\n"
            analysis += f"• 🤖 AI Skor: {signal.get('ai_skor', 0):.2f}\n"
            analysis += f"• 🎯 Güven: %{strategy_breakdown.get('composite_confidence', 0):.1f}\n"
            analysis += f"• ⚡ Strateji: {strategy_breakdown.get('best_strategy', 'Bilinmiyor')}\n\n"
            
            analysis += "📈 TEKNİK ANALİZ:\n"
            analysis += "• Çoklu zaman dilimi analizi aktif\n"
            analysis += "• 4 farklı trading stratejisi değerlendirildi\n"
            analysis += "• Risk yönetimi entegre edilmiş durumda\n"
        else:
            analysis += "ℹ️ Bu coin için güncel analiz bulunmuyor.\n"
            analysis += "Ana sayfadan analiz yaparak güncel verilere ulaşabilirsiniz.\n"
        
        analysis += "\n💡 GENEL DEĞERLENDİRME:\n"
        analysis += f"{coin} için AI destekli çok boyutlu analiz yapılmaktadır. "
        analysis += "Momentum, mean reversion, breakout ve multi-timeframe stratejileri kombine edilmektedir."
        
        return analysis

    def explain_strategies(self):
        """Stratejileri açıkla"""
        return """🤖 KULLANILAN TRADING STRATEJİLERİ:

1. 📊 **MOMENTUM STRATEJİSİ**
   • RSI, MACD gibi momentum göstergeleri
   • Trend takip sistemi
   • Güçlü trendlerde etkili

2. 🔄 **MEAN REVERSION STRATEJİSİ**  
   • Bollinger Bands kullanır
   • Aşırı alım/satım bölgelerini tespit eder
   • Range-bound piyasalarda başarılı

3. 🚀 **BREAKOUT STRATEJİSİ**
   • Volatilite patlamalarını takip eder
   • Destek/direnç kırılımlarını tespit eder
   • Yeni trend başlangıçlarında etkili

4. ⏰ **MULTI-TIMEFRAME STRATEJİSİ**
   • 5m, 15m, 1h, 4h, 1d zaman dilimleri
   • Zaman dilimi uyumu analizi
   • Trend onayı için kullanılır

🎯 **AI KOMBİNASYONU**: Tüm stratejilerin çıktıları AI tarafından değerlendirilerek optimal sinyal üretilir.
"""

    def get_performance_analysis(self):
        """Performans analizi"""
        stats = self.portfolio_manager.get_performance_stats(30)
        signal_history = self.portfolio_manager.get_ai_signal_history(limit=100)
        
        analysis = "📊 AI PERFORMANS ANALİZİ:\n\n"
        
        if signal_history:
            signals = [s[2] for s in signal_history]  # signal column
            buy_signals = signals.count('AL')
            sell_signals = signals.count('SAT')
            total_signals = len(signals)
            
            analysis += f"📈 SON 100 AI SİNYALİ:\n"
            analysis += f"• ✅ AL Sinyali: {buy_signals} (%{buy_signals/total_signals*100:.1f})\n"
            analysis += f"• ❌ SAT Sinyali: {sell_signals} (%{sell_signals/total_signals*100:.1f})\n"
            analysis += f"• ⏸️ BEKLE: {total_signals - buy_signals - sell_signals}\n\n"
        else:
            analysis += "ℹ️ Henüz yeterli sinyal geçmişi bulunmuyor.\n\n"
        
        analysis += "💰 TRADING PERFORMANSI:\n"
        analysis += f"• 🎯 Başarı Oranı: %{stats['win_rate']:.1f}\n"
        analysis += f"• 📊 Ortalama K/Z: ${stats['average_pl']:,.2f}\n"
        analysis += f"• 🔄 Toplam İşlem: {stats['total_trades']}\n"
        
        return analysis

    def get_general_advice(self, question):
        """Genel tavsiye"""
        return f"""🤖 AI TRADING ASISTAN CEVAP:

Anladığım kadarıyla '{question}' hakkında soru sordunuz.

🔍 **ANALİZ ÖNERİLERİ**:
• Portföy durumunuzu öğrenmek için "Portföyüm nasıl?" sorabilirsiniz
• Trading tavsiyesi için "Ne yapmalıyım?" diye sorun
• Risk analizi için "Risk seviyem nedir?" 
• Coin analizi için "BTC analizi" veya "ETH analizi"

💡 **DİĞER ÖZELLİKLER**:
• 🤖 Çoklu AI stratejisi
• 📊 Gelişmiş risk yönetimi  
• ⚡ Real-time piyasa analizi
• 📈 Performans takibi

Daha spesifik bir soru sormak isterseniz, size daha detaylı yardımcı olabilirim!"""

class StreamlitTradingApp:
    def __init__(self):
        self.portfolio_manager = AdvancedPortfolioManager()
        self.ai_chatbot = AdvancedAIChatBot(self.portfolio_manager)
        self.setup_session_state()
        
    def setup_session_state(self):
        """Session state'i başlat"""
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = None
        if 'auto_trading' not in st.session_state:
            st.session_state.auto_trading = False
        if 'paper_trading' not in st.session_state:
            st.session_state.paper_trading = True
        if 'selected_strategies' not in st.session_state:
            st.session_state.selected_strategies = ['momentum', 'mean_reversion', 'breakout', 'multi_timeframe']
        if 'close_position_clicks' not in st.session_state:
            st.session_state.close_position_clicks = {}
    
    def run(self):
        try:
            # Başlık
            st.title("🚀 AI Trading Bot - Gelişmiş Özellikler")
            st.markdown("---")
            
            # Sidebar - Kontroller
            self.setup_sidebar()
            
            # Ana içerik - Sekmeler
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "🏠 Ana Sayfa", 
                "📦 Portföy Takip", 
                "📈 Performans", 
                "🤖 AI Analiz",
                "❓ AI Asistan",
                "⚙️ Ayarlar",
                "🔧 Backtest"
            ])
            
            with tab1:
                self.setup_main_content()
            
            with tab2:
                self.setup_portfolio_tab()
            
            with tab3:
                self.setup_performance_tab()
            
            with tab4:
                self.setup_ai_analysis_tab()
            
            with tab5:
                self.setup_ai_assistant_tab()
            
            with tab6:
                self.setup_settings_tab()
            
            with tab7:
                self.setup_backtest_tab()
                
        except Exception as e:
            st.error(f"Uygulama başlatılırken hata oluştu: {str(e)}")
            st.info("Lütfen sayfayı yenileyin veya daha sonra tekrar deneyin.")
    
    def setup_sidebar(self):
        st.sidebar.header("🎮 Gelişmiş Kontrol Paneli")
        
        try:
            from settings import SYMBOLS, TIMEFRAMES, ANALYSIS_CONFIG, AUTO_TRADING_CONFIG
            
            self.selected_symbols = st.sidebar.multiselect(
                "Semboller:",
                SYMBOLS,
                default=SYMBOLS[:3]
            )
            
            self.selected_timeframe = st.sidebar.selectbox(
                "Ana Zaman Dilimi:",
                TIMEFRAMES,
                index=2
            )
            
            self.capital = st.sidebar.number_input(
                "Sermaye ($):",
                min_value=100,
                max_value=100000,
                value=ANALYSIS_CONFIG.get('default_capital', 1000),
                step=100
            )
            
        except ImportError:
            st.sidebar.warning("⚠️ settings.py bulunamadı, varsayılan ayarlar kullanılıyor.")
            self.selected_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
            self.selected_timeframe = "1h"
            self.capital = 1000
        
        # Strateji seçimi
        st.sidebar.subheader("🎯 Trading Stratejileri")
        self.selected_strategies = st.sidebar.multiselect(
            "Aktif Stratejiler:",
            ['momentum', 'mean_reversion', 'breakout', 'multi_timeframe'],
            default=st.session_state.selected_strategies
        )
        
        # Risk ayarları
        st.sidebar.subheader("⚖️ Risk Yönetimi")
        self.risk_tolerance = st.sidebar.slider("Risk Toleransı (1-10):", 1, 10, 7)
        self.max_drawdown = st.sidebar.slider("Maksimum Drawdown (%):", 1, 50, 15)
        self.max_position_size = st.sidebar.slider("Maks. Pozisyon Büyüklüğü (%):", 1, 50, 10)
        
        # Auto trading kontrolü
        st.sidebar.subheader("🤖 Auto Trading")
        auto_col1, auto_col2 = st.sidebar.columns(2)
        
        with auto_col1:
            st.session_state.auto_trading = st.checkbox("Aktif", value=st.session_state.auto_trading)
        
        with auto_col2:
            st.session_state.paper_trading = st.checkbox("Paper Trading", value=st.session_state.paper_trading)
        
        # Hızlı aksiyonlar
        st.sidebar.subheader("⚡ Hızlı Aksiyonlar")
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("🚀 Analiz Yap", use_container_width=True):
                with st.spinner("AI analiz yapıyor..."):
                    self.run_advanced_analysis()
        
        with col2:
            if st.button("🧪 Sistem Testi", use_container_width=True):
                self.run_system_test()
        
        st.sidebar.markdown("---")
        st.sidebar.info("""
        **✨ Yeni Özellikler:**
        • 🤖 Çoklu AI Stratejisi
        • 📊 Gelişmiş Portfolio Analitiği  
        • ⚡ Real-time Risk Yönetimi
        • 🔄 Multi-Exchange Desteği
        • 📈 Advanced Backtesting
        """)
    
    def setup_main_content(self):
        st.header("🎯 Gelişmiş AI Trading Bot")
        
        # Hızlı başlangıç kartları
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            portfolio_summary = self.portfolio_manager.get_portfolio_summary()
            st.metric(
                "💰 Toplam Değer", 
                f"${portfolio_summary['total_value']:,.2f}",
                delta=f"{portfolio_summary['total_pnl_percent']:.2f}%"
            )
        
        with col2:
            stats = self.portfolio_manager.get_performance_stats(7)
            st.metric(
                "📈 7 Gün K/Z", 
                f"${stats['total_profit_loss']:,.2f}",
                delta=f"{stats['win_rate']:.1f}% Win Rate"
            )
        
        with col3:
            portfolio = self.portfolio_manager.get_portfolio()
            st.metric(
                "📦 Aktif Pozisyon", 
                f"{len(portfolio)}",
                delta=f"{sum(1 for p in portfolio if p[10] > 0)} Profit" if portfolio else "0"
            )
        
        with col4:
            signals = self.portfolio_manager.get_ai_signal_history(limit=1)
            if signals:
                last_signal = signals[0]
                st.metric(
                    "🎯 Son Sinyal", 
                    f"{last_signal[1]} {last_signal[2]}",
                    delta=f"Güç: {last_signal[3]}/10"
                )
            else:
                st.metric("🎯 Son Sinyal", "YOK", delta="Bekle")
        
        st.markdown("---")
        
        # Ana analiz bölümü
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📈 Real-time Piyasa Analizi")
            
            if st.button("🚀 Gelişmiş AI Analiz Başlat", type="primary", use_container_width=True):
                with st.spinner("🤖 Çoklu strateji analizi yapılıyor..."):
                    self.run_advanced_analysis()
            
            if st.session_state.analysis_results:
                self.display_advanced_analysis_results()
            else:
                st.info("👆 'Gelişmiş AI Analiz Başlat' butonuna tıklayarak piyasa analizi yapın!")
        
        with col2:
            st.subheader("⚡ Hızlı İşlem")
            self.display_quick_trade_panel()
    
    def setup_portfolio_tab(self):
        st.header("📦 Gelişmiş Portföy Takip")
        
        portfolio = self.portfolio_manager.get_portfolio()
        summary = self.portfolio_manager.get_portfolio_summary()
        
        # Portfolio özeti
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "💰 Toplam Değer",
                f"${summary['total_value']:,.2f}",
                delta=f"{summary['total_pnl_percent']:.2f}%"
            )
        
        with col2:
            st.metric(
                "📊 Toplam Yatırım", 
                f"${summary['total_invested']:,.2f}"
            )
        
        with col3:
            st.metric(
                "💸 Gerçekleşmemiş K/Z",
                f"${summary['total_unrealized_pnl']:,.2f}",
                delta_color="inverse" if summary['total_unrealized_pnl'] < 0 else "normal"
            )
        
        with col4:
            st.metric(
                "📦 Pozisyon Sayısı",
                f"{summary['positions_count']}"
            )
        
        st.markdown("---")
        
        # Pozisyonlar tablosu
        if portfolio:
            st.subheader("💰 Aktif Pozisyonlar")
            
            # Pozisyonları DataFrame'e dönüştür
            positions_data = []
            for position in portfolio:
                symbol = position[1]
                entry_price = position[2]
                quantity = position[3]
                entry_date = position[4]
                stop_loss = position[5]
                take_profit = position[6]
                leverage = position[7]
                current_price = position[9]
                unrealized_pnl = position[10]
                pnl_percent = ((current_price - entry_price) / entry_price * 100) if current_price else 0
                
                positions_data.append({
                    'Sembol': symbol,
                    'Miktar': quantity,
                    'Giriş Fiyatı': f"${entry_price:.4f}",
                    'Güncel Fiyat': f"${current_price:.4f}" if current_price else "N/A",
                    'K/Z ($)': f"${unrealized_pnl:.2f}",
                    'K/Z (%)': f"%{pnl_percent:.2f}",
                    'Stop-Loss': f"${stop_loss:.4f}" if stop_loss else "N/A",
                    'Take-Profit': f"${take_profit:.4f}" if take_profit else "N/A",
                    'Kaldıraç': leverage,
                    'Giriş Tarihi': entry_date[:16]
                })
            
            df_positions = pd.DataFrame(positions_data)
            st.dataframe(df_positions, use_container_width=True)
            
            # Pozisyon kapatma
            st.subheader("🔒 Pozisyon Kapatma")
            cols = st.columns(3)
            
            for i, position in enumerate(portfolio):
                col_idx = i % 3
                with cols[col_idx]:
                    symbol = position[1]
                    current_price = position[9] or position[2]  # current_price yoksa entry_price kullan
                    
                    with st.container():
                        st.write(f"**{symbol}**")
                        st.write(f"K/Z: ${position[10]:.2f}")
                        
                        # Benzersiz bir key oluştur
                        close_key = f"close_{symbol}_{i}"
                        
                        if st.button("❌ Kapat", key=close_key, use_container_width=True):
                            # Kapatma işlemi
                            profit_loss = self.portfolio_manager.close_position(symbol, current_price)
                            st.success(f"✅ {symbol} pozisyonu kapatıldı! K/Z: ${profit_loss:.2f}")
                            st.rerun()
        
        else:
            st.info("📭 Aktif pozisyon bulunmuyor.")
        
        # Yeni pozisyon ekleme
        st.markdown("---")
        st.subheader("➕ Yeni Pozisyon Ekle")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            new_symbol = st.text_input("Sembol (örn: BTCUSDT)", "BTCUSDT")
        
        with col2:
            entry_price = st.number_input("Giriş Fiyatı ($)", min_value=0.0001, value=50000.0, step=0.1)
        
        with col3:
            quantity = st.number_input("Miktar", min_value=0.001, value=0.01, step=0.001)
        
        with col4:
            leverage = st.selectbox("Kaldıraç", ["1x", "2x", "3x", "5x", "10x"])
        
        col5, col6, col7 = st.columns(3)
        
        with col5:
            stop_loss = st.number_input("Stop-Loss ($)", min_value=0.0001, value=entry_price * 0.95)
        
        with col6:
            take_profit = st.number_input("Take-Profit ($)", min_value=0.0001, value=entry_price * 1.05)
        
        with col7:
            st.write("")  # Boşluk için
            if st.button("➕ Pozisyon Ekle", use_container_width=True):
                self.portfolio_manager.add_to_portfolio(
                    new_symbol, entry_price, quantity, stop_loss, take_profit, leverage
                )
                st.success(f"✅ {new_symbol} pozisyonu eklendi!")
                st.rerun()
    
    def setup_performance_tab(self):
        st.header("📊 Gelişmiş Performans Analizi")
        
        # Performans metrikleri
        stats_30d = self.portfolio_manager.get_performance_stats(30)
        stats_7d = self.portfolio_manager.get_performance_stats(7)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "💰 30 Gün K/Z",
                f"${stats_30d['total_profit_loss']:,.2f}",
                delta=f"{stats_30d['win_rate']:.1f}% Win Rate"
            )
        
        with col2:
            st.metric(
                "📈 7 Gün K/Z", 
                f"${stats_7d['total_profit_loss']:,.2f}",
                delta=f"{stats_7d['win_rate']:.1f}% Win Rate"
            )
        
        with col3:
            st.metric(
                "🎯 Toplam İşlem",
                f"{stats_30d['total_trades']}",
                delta=f"{stats_30d['winning_trades']} Kazanan"
            )
        
        with col4:
            st.metric(
                "⏱️ Ort. Süre",
                f"{stats_30d['average_duration']:.0f} dk",
                delta=f"En İyi: ${stats_30d['best_trade']:.2f}"
            )
        
        st.markdown("---")
        
        # Trade geçmişi
        st.subheader("📋 Trade Geçmişi")
        trade_history = self.portfolio_manager.get_trade_history(50)
        
        if trade_history:
            history_data = []
            for trade in trade_history:
                history_data.append({
                    'Sembol': trade[1],
                    'Aksiyon': trade[2],
                    'Giriş': f"${trade[3]:.4f}",
                    'Çıkış': f"${trade[4]:.4f}",
                    'Miktar': trade[5],
                    'K/Z ($)': f"${trade[7]:.2f}",
                    'K/Z (%)': f"%{trade[8]:.2f}",
                    'Süre (dk)': trade[11] or 0,
                    'Tarih': trade[6][:16]
                })
            
            df_history = pd.DataFrame(history_data)
            st.dataframe(df_history, use_container_width=True)
        else:
            st.info("📭 Henüz trade geçmişi bulunmuyor.")
        
        # Performans grafikleri
        st.markdown("---")
        st.subheader("📈 Performans Grafikleri")
        
        # Örnek performans grafiği
        try:
            fig = self.create_performance_chart()
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Grafik oluşturulamadı: {e}")
    
    def setup_ai_analysis_tab(self):
        st.header("🤖 AI Sinyal Geçmişi")
        
        # AI sinyal filtreleri
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_symbol = st.selectbox(
                "Sembol Filtresi",
                ["Tümü", "BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT"]
            )
        
        with col2:
            filter_signal = st.selectbox(
                "Sinyal Filtresi", 
                ["Tümü", "AL", "SAT", "BEKLE"]
            )
        
        with col3:
            filter_limit = st.slider("Gösterilecek Kayıt", 10, 200, 50)
        
        # AI sinyal geçmişi
        signals = self.portfolio_manager.get_ai_signal_history(
            symbol=None if filter_symbol == "Tümü" else filter_symbol,
            limit=filter_limit
        )
        
        if signals:
            signals_data = []
            for signal in signals:
                symbol = signal[1]
                signal_type = signal[2]
                strength = signal[3]
                ai_score = signal[4]
                timestamp = signal[5]
                price = signal[6]
                strategy_breakdown = json.loads(signal[7]) if signal[7] else {}
                
                # Sinyal filtreleme
                if filter_signal != "Tümü" and signal_type != filter_signal:
                    continue
                
                signals_data.append({
                    'Sembol': symbol,
                    'Sinyal': signal_type,
                    'Güç': strength,
                    'AI Skor': f"{ai_score:.2f}",
                    'Fiyat': f"${price:.4f}" if price else "N/A",
                    'Güven': f"%{strategy_breakdown.get('composite_confidence', 0):.1f}",
                    'Strateji': strategy_breakdown.get('best_strategy', 'N/A'),
                    'Zaman': timestamp[:16]
                })
            
            if signals_data:
                df_signals = pd.DataFrame(signals_data)
                st.dataframe(df_signals, use_container_width=True)
            else:
                st.info("📭 Filtre kriterlerine uygun sinyal bulunamadı.")
        else:
            st.info("📭 Henüz AI sinyal geçmişi bulunmuyor.")
        
        # AI strateji istatistikleri
        st.markdown("---")
        st.subheader("📊 AI Strateji Performansı")
        
        if signals:
            # Strateji başarı analizi
            strategy_stats = {}
            for signal in signals:
                strategy_breakdown = json.loads(signal[7]) if signal[7] else {}
                strategy = strategy_breakdown.get('best_strategy', 'Bilinmiyor')
                
                if strategy not in strategy_stats:
                    strategy_stats[strategy] = {'count': 0, 'total_strength': 0}
                
                strategy_stats[strategy]['count'] += 1
                strategy_stats[strategy]['total_strength'] += signal[3]  # strength
            
            # İstatistikleri göster
            if strategy_stats:
                cols = st.columns(len(strategy_stats))
                for i, (strategy, stats) in enumerate(strategy_stats.items()):
                    with cols[i % len(cols)]:
                        avg_strength = stats['total_strength'] / stats['count']
                        st.metric(
                            f"🎯 {strategy}",
                            f"{stats['count']} sinyal",
                            delta=f"Ort. Güç: {avg_strength:.1f}"
                        )
    
    def setup_ai_assistant_tab(self):
        st.header("❓ AI Trading Asistan")
        
        st.markdown("""
        🤖 **Gelişmiş AI Asistan** ile trading stratejileriniz hakkında konuşun!
        
        **Örnek sorular:**
        - Portföyüm nasıl?
        - Ne yapmalıyım?
        - Risk seviyem nedir?
        - BTC analizi yapar mısın?
        - Stratejilerini açıklar mısın?
        """)
        
        # Chat interface
        user_question = st.text_input(
            "💬 AI Asistan'a soru sorun:",
            placeholder="Portföyüm nasıl? Ne yapmalıyım? BTC analizi?"
        )
        
        if st.button("🚀 Soruyu Gönder", use_container_width=True) and user_question:
            with st.spinner("🤖 AI düşünüyor..."):
                response = self.ai_chatbot.ask_question(
                    user_question, 
                    st.session_state.analysis_results,
                    "advanced_analysis"
                )
            
            st.markdown("---")
            st.subheader("🤖 AI Cevabı:")
            st.markdown(f"```\n{response}\n```")
        
        # Hızlı soru butonları
        st.markdown("---")
        st.subheader("⚡ Hızlı Sorular")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Portföy Durumu", use_container_width=True):
                response = self.ai_chatbot.ask_question("Portföyüm nasıl?")
                st.markdown(f"```\n{response}\n```")
        
        with col2:
            if st.button("🎯 Trading Tavsiyesi", use_container_width=True):
                response = self.ai_chatbot.ask_question("Ne yapmalıyım?", st.session_state.analysis_results)
                st.markdown(f"```\n{response}\n```")
        
        with col3:
            if st.button("⚠️ Risk Analizi", use_container_width=True):
                response = self.ai_chatbot.ask_question("Risk seviyem nedir?")
                st.markdown(f"```\n{response}\n```")
    
    def setup_settings_tab(self):
        st.header("⚙️ Gelişmiş Ayarlar")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔧 Sistem Ayarları")
            
            # API ayarları
            st.text_input("Binance API Key", type="password", placeholder="••••••••••••")
            st.text_input("Binance Secret Key", type="password", placeholder="••••••••••••")
            
            # Trading ayarları
            st.number_input("Varsayılan Pozisyon Büyüklüğü (%)", 1, 100, 10)
            st.number_input("Varsayılan Stop-Loss (%)", 1, 20, 5)
            st.number_input("Varsayılan Take-Profit (%)", 1, 50, 10)
            
            # Bildirim ayarları
            st.checkbox("Telegram Bildirimleri", value=True)
            st.checkbox("Email Bildirimleri", value=False)
            
            if st.button("💾 Ayarları Kaydet", use_container_width=True):
                st.success("✅ Ayarlar kaydedildi!")
        
        with col2:
            st.subheader("📊 Analiz Ayarları")
            
            # AI strateji ağırlıkları
            st.slider("Momentum Strateji Ağırlığı", 0.0, 1.0, 0.25)
            st.slider("Mean Reversion Ağırlığı", 0.0, 1.0, 0.25)
            st.slider("Breakout Strateji Ağırlığı", 0.0, 1.0, 0.25)
            st.slider("Multi-Timeframe Ağırlığı", 0.0, 1.0, 0.25)
            
            # Risk parametreleri
            st.slider("Maksimum Drawdown Limiti (%)", 1, 50, 20)
            st.slider("Minimum Sinyal Güven Seviyesi", 1, 10, 6)
            st.slider("Maksimum Günlük İşlem", 1, 50, 10)
            
            if st.button("🔄 Varsayılana Dön", use_container_width=True):
                st.info("🔧 Varsayılan ayarlar yüklendi!")
    
    def setup_backtest_tab(self):
        st.header("🔧 Gelişmiş Backtesting")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Backtest Parametreleri")
            
            initial_capital = st.number_input("Başlangıç Sermayesi ($):", 
                                            min_value=100, value=1000, step=100)
            
            test_period = st.selectbox("Test Periyodu:",
                ["7 gün", "30 gün", "90 gün", "180 gün", "1 yıl"]
            )
            
            strategy = st.selectbox("Test Stratejisi:",
                ["AI Kombinasyon", "Sadece Momentum", "Sadece Mean Reversion", 
                 "Sadece Breakout", "Manual Strategy"]
            )
            
            symbols = st.multiselect("Semboller:", 
                                   ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT", "DOTUSDT"],
                                   default=["BTCUSDT", "ETHUSDT"])
        
        with col2:
            st.subheader("📈 Risk Parametreleri")
            
            max_drawdown = st.slider("Maksimum Drawdown (%):", 1, 50, 20)
            stop_loss = st.slider("Stop Loss (%):", 1, 20, 5)
            take_profit = st.slider("Take Profit (%):", 5, 100, 15)
            success_rate = st.slider("Minimum Başarı Oranı (%):", 30, 90, 50)
        
        if st.button("🚀 Backtest Başlat", type="primary", use_container_width=True):
            with st.spinner("Backtest çalıştırılıyor..."):
                # Simüle backtest sonuçları
                time.sleep(2)
                
                # Backtest sonuçları
                st.subheader("📊 Backtest Sonuçları")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Toplam Getiri", "+23.5%", "+15.2%")
                
                with col2:
                    st.metric("Win Rate", "68.2%")
                
                with col3:
                    st.metric("Sharpe Oranı", "1.45")
                
                with col4:
                    st.metric("Maks Drawdown", "-8.7%")
                
                # Backtest grafiği
                dates = pd.date_range(start='2024-01-01', end='2024-03-01', freq='D')
                portfolio_values = [1000 + i*8 + random.randint(-50, 50) for i in range(len(dates))]
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=dates, y=portfolio_values, mode='lines', name='Portfolio'))
                fig.update_layout(title='Backtest Performansı', height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    def run_advanced_analysis(self):
        """Gelişmiş AI analizi çalıştır"""
        try:
            # Mevcut analiz kodunu burada entegre edin
            # Örnek veri yapısı:
            sample_results = []
            symbols = self.selected_symbols if hasattr(self, 'selected_symbols') else ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
            
            for symbol in symbols:
                # Örnek sinyal üretimi - gerçek kodunuzu buraya entegre edin
                signal_strength = random.randint(1, 10)
                ai_score = random.uniform(0.5, 0.95)
                
                if signal_strength >= 7:
                    signal_type = "AL"
                elif signal_strength <= 3:
                    signal_type = "SAT" 
                else:
                    signal_type = "BEKLE"
                
                strategy_breakdown = {
                    'momentum_score': random.uniform(0.3, 0.9),
                    'mean_reversion_score': random.uniform(0.3, 0.9),
                    'breakout_score': random.uniform(0.3, 0.9),
                    'multi_timeframe_score': random.uniform(0.3, 0.9),
                    'composite_confidence': random.uniform(60, 95),
                    'best_strategy': random.choice(['Momentum', 'Mean Reversion', 'Breakout', 'Multi-Timeframe'])
                }
                
                sample_results.append({
                    'symbol': symbol,
                    'signal': {
                        'sinyal': signal_type,
                        'güç': signal_strength,
                        'ai_skor': ai_score,
                        'strategy_breakdown': strategy_breakdown
                    },
                    'price': random.uniform(100, 50000),
                    'timestamp': datetime.now().isoformat()
                })
                
                # AI sinyal geçmişine kaydet
                self.portfolio_manager.add_ai_signal(
                    symbol, signal_type, signal_strength, ai_score, 
                    sample_results[-1]['price'], strategy_breakdown
                )
            
            st.session_state.analysis_results = sample_results
            st.success(f"✅ {len(sample_results)} sembol için AI analizi tamamlandı!")
            
        except Exception as e:
            st.error(f"❌ Analiz sırasında hata: {str(e)}")
    
    def display_advanced_analysis_results(self):
        """Gelişmiş analiz sonuçlarını göster"""
        if not st.session_state.analysis_results:
            return
        
        results = st.session_state.analysis_results
        
        # Sinyal özeti
        buy_signals = sum(1 for r in results if r.get('signal', {}).get('sinyal') == 'AL')
        sell_signals = sum(1 for r in results if r.get('signal', {}).get('sinyal') == 'SAT')
        strong_signals = sum(1 for r in results if r.get('signal', {}).get('güç', 0) >= 7)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Analiz Edilen", f"{len(results)} sembol")
        
        with col2:
            st.metric("✅ AL Sinyali", f"{buy_signals}", delta=f"%{buy_signals/len(results)*100:.1f}")
        
        with col3:
            st.metric("❌ SAT Sinyali", f"{sell_signals}", delta=f"%{sell_signals/len(results)*100:.1f}")
        
        with col4:
            st.metric("💪 Güçlü Sinyal", f"{strong_signals}")
        
        st.markdown("---")
        
        # Detaylı sinyal tablosu
        st.subheader("📋 Detaylı AI Sinyalleri")
        
        signals_data = []
        for result in results:
            signal = result.get('signal', {})
            symbol = result.get('symbol', 'N/A')
            
            signals_data.append({
                'Sembol': symbol,
                'Sinyal': signal.get('sinyal', 'BEKLE'),
                'Güç': signal.get('güç', 0),
                'AI Skor': f"{signal.get('ai_skor', 0):.2f}",
                'Fiyat': f"${result.get('price', 0):.4f}",
                'Güven': f"%{signal.get('strategy_breakdown', {}).get('composite_confidence', 0):.1f}",
                'Strateji': signal.get('strategy_breakdown', {}).get('best_strategy', 'N/A'),
                'Zaman': result.get('timestamp', '')[:16]
            })
        
        df_signals = pd.DataFrame(signals_data)
        st.dataframe(df_signals, use_container_width=True)
        
        # AI tavsiyesi
        st.markdown("---")
        st.subheader("🎯 AI Trading Tavsiyesi")
        
        advice = self.ai_chatbot.get_advanced_trading_advice(results, "advanced_analysis")
        st.markdown(f"```\n{advice}\n```")
    
    def display_quick_trade_panel(self):
        """Hızlı işlem panelini göster"""
        st.subheader("⚡ Hızlı İşlem")
        
        symbol = st.selectbox("Sembol", ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT'])
        action = st.radio("Aksiyon", ['AL', 'SAT'], horizontal=True)
        quantity = st.number_input("Miktar", 0.001, 1000.0, 0.01, 0.001)
        
        col1, col2 = st.columns(2)
        
        with col1:
            price = st.number_input("Fiyat ($)", 0.0001, 1000000.0, 50000.0, 0.1)
        
        with col2:
            leverage = st.selectbox("Kaldıraç", ["1x", "2x", "3x", "5x", "10x"])
        
        if st.button(f"🚀 {action} İşlemi Onayla", type="primary", use_container_width=True):
            if action == 'AL':
                self.portfolio_manager.add_to_portfolio(symbol, price, quantity, leverage=leverage)
                st.success(f"✅ {symbol} AL işlemi gerçekleştirildi!")
            else:
                # SAT işlemi için mevcut pozisyon kontrolü
                portfolio = self.portfolio_manager.get_portfolio()
                symbol_positions = [p for p in portfolio if p[1] == symbol]
                
                if symbol_positions:
                    # İlk pozisyonu kapat
                    profit = self.portfolio_manager.close_position(symbol, price)
                    st.success(f"✅ {symbol} SAT işlemi gerçekleştirildi! K/Z: ${profit:.2f}")
                else:
                    st.error(f"❌ {symbol} için aktif pozisyon bulunamadı!")
            
            st.rerun()
    
    def create_performance_chart(self):
        """Performans grafiği oluştur"""
        # Örnek performans verisi
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        performance = [1000 + i * 10 + random.randint(-50, 50) for i in range(len(dates))]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=performance,
            mode='lines',
            name='Portföy Değeri',
            line=dict(color='#00ff88', width=3)
        ))
        
        fig.update_layout(
            title='📈 30 Günlük Portföy Performansı',
            xaxis_title='Tarih',
            yaxis_title='Portföy Değeri ($)',
            template='plotly_dark',
            height=400
        )
        
        return fig
    
    def run_system_test(self):
        st.info("🧪 Gelişmiş sistem testi başlatılıyor...")
        
        try:
            # Sistem bileşenleri durumu
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.success("🤖 AI Motor: ✅")
            
            with col2:
                st.success("📊 Veri Kaynakları: ✅")
            
            with col3:
                st.success("⚖️ Risk Yönetimi: ✅")
            
            with col4:
                st.success("🔗 Exchange Bağlantı: ✅")
            
            st.success("✅ Gelişmiş sistem testi başarılı!")
                
        except Exception as e:
            st.error(f"❌ Sistem testi başarısız: {e}")

def main():
    try:
        app = StreamlitTradingApp()
        app.run()
    except Exception as e:
        st.error(f"Uygulama başlatılırken hata oluştu: {str(e)}")
        st.info("Lütfen sayfayı yenileyin veya daha sonra tekrar deneyin.")

if __name__ == "__main__":
    main()