import requests
import json
import random
import numpy as np
from datetime import datetime

class AdvancedLocalAI:
    def __init__(self, config=None):
        self.config = config or {
            "api_url": "http://localhost:1234/v1/chat/completions",
            "max_tokens": 500,
            "temperature": 0.1
        }
    
    def generate_signal(self, context, timeframe="1h", capital=1000, analysis_data=None):
        """Gelişmiş AI sinyal üretimi - KONTROL EDİN"""
        try:
            # Context'ten verileri parse et
            parsed_data = self._parse_context(context)

            # ✅ GERÇEK FİYATI AL: Primary timeframe'den
            current_price = self._get_current_price_from_analysis(parsed_data, timeframe)

            # Çoklu zaman dilimi analizi
            multi_tf_analysis = self._analyze_multiple_timeframes(parsed_data)

            # Risk yönetimi hesaplamaları - GERÇEK FİYATLA
            risk_analysis = self._calculate_risk_management(parsed_data, capital, current_price)

            # AI karar motoru - GERÇEK FİYATLA
            signal_result = self._ai_decision_engine(multi_tf_analysis, risk_analysis, timeframe, current_price)

            # ✅ DEBUG: Sinyal detaylarını kontrol edin
            print(f"   🔍 AI Sinyal Detayları: {signal_result.keys()}")

            return signal_result

        except Exception as e:
            print(f"❌ AI analiz hatası: {e}")
            return self._get_fallback_signal()
    
    def _get_current_price_from_analysis(self, analysis_data, timeframe):
        """Analiz verilerinden gerçek fiyatı al"""
        try:
            # Önce belirtilen timeframe'den fiyatı al
            if timeframe in analysis_data.get('timeframes', {}):
                price = analysis_data['timeframes'][timeframe].get('close', 0)
                if price > 0:
                    return price
            
            # Belirtilen timeframe yoksa primary'den al
            primary_data = analysis_data.get('primary_indicators', {})
            price = primary_data.get('close', 0)
            if price > 0:
                return price
            
            # Hiçbiri yoksa ilk bulunan timeframe'den al
            for tf_data in analysis_data.get('timeframes', {}).values():
                price = tf_data.get('close', 0)
                if price > 0:
                    return price
            
            # Fallback
            return 50000
        except:
            return 50000
    
    def _parse_context(self, context):
        """Context verisini parse et"""
        try:
            parsed = {
                'timeframes': {},
                'primary_indicators': {},
                'fear_greed': context.get('fear_greed', {})
            }
            
            # Timeframe verilerini işle
            for tf, data in context.get('timeframe_data', {}).items():
                parsed['timeframes'][tf] = {
                    'close': data.get('close', 0),
                    'volume': data.get('volume', 0),
                    'rsi': data.get('rsi', 50),
                    'macd': data.get('macd', 0),
                    'macd_signal': data.get('macd_signal', 0),
                    'ema_20': data.get('ema_20', 0),
                    'ema_50': data.get('ema_50', 0),
                    'bollinger_upper': data.get('bollinger_upper', 0),
                    'bollinger_lower': data.get('bollinger_lower', 0),
                    'recommendation': data.get('recommendation', 'NEUTRAL')
                }
            
            return parsed
        except Exception as e:
            print(f"❌ Context parsing hatası: {e}")
            return {'timeframes': {}, 'primary_indicators': {}, 'fear_greed': {}}
    
    def _analyze_multiple_timeframes(self, analysis_data):
        """Çoklu zaman dilimi analizi"""
        timeframes = analysis_data.get('timeframes', {})
        
        if not timeframes:
            return {
                'trend_alignment': 0,
                'momentum_score': 0,
                'timeframe_alignment': 0,
                'consensus': 'NEUTRAL'
            }
        
        # Trend analizi
        bullish_count = 0
        total_timeframes = len(timeframes)
        
        for tf_data in timeframes.values():
            recommendation = tf_data.get('recommendation', 'NEUTRAL')
            if 'BUY' in recommendation:
                bullish_count += 1
            elif 'SELL' in recommendation:
                bullish_count -= 1
        
        trend_alignment = bullish_count / total_timeframes if total_timeframes > 0 else 0
        
        # Momentum skoru
        momentum_score = 0
        for tf_data in timeframes.values():
            rsi = tf_data.get('rsi', 50)
            if rsi < 30:
                momentum_score += 1  # Oversold - pozitif momentum
            elif rsi > 70:
                momentum_score -= 1  # Overbought - negatif momentum
            
            macd = tf_data.get('macd', 0)
            macd_signal = tf_data.get('macd_signal', 0)
            if macd > macd_signal:
                momentum_score += 0.5
            else:
                momentum_score -= 0.5
        
        # Zaman dilimi uyumu
        alignment_ratio = abs(trend_alignment)
        
        return {
            'trend_alignment': trend_alignment,
            'momentum_score': momentum_score / total_timeframes if total_timeframes > 0 else 0,
            'timeframe_alignment': alignment_ratio,
            'consensus': 'BULLISH' if trend_alignment > 0.3 else 'BEARISH' if trend_alignment < -0.3 else 'NEUTRAL'
        }
    
    def _calculate_risk_management(self, analysis_data, capital, current_price):
        """Risk yönetimi hesaplamaları - GERÇEK FİYATLA"""
        volatility = self._calculate_volatility(analysis_data)
        
        # Position sizing - GERÇEK FİYATLA
        risk_per_trade = capital * 0.02  # 2% risk
        stop_loss_pct = max(0.01, min(0.1, volatility * 2))  # %1-10 arası stop loss
        
        if current_price > 0:
            position_size = risk_per_trade / (current_price * stop_loss_pct)
        else:
            position_size = 0
        
        risk_analysis = {
            'capital': capital,
            'risk_per_trade': risk_per_trade,
            'position_size': position_size,
            'stop_loss_pct': stop_loss_pct,
            'volatility': volatility,
            'risk_reward_ratio': 2.0,
            'current_price': current_price
        }
        
        return risk_analysis
    
    def _calculate_volatility(self, analysis_data):
        """Volatilite hesapla"""
        try:
            prices = []
            for tf_data in analysis_data.get('timeframes', {}).values():
                price = tf_data.get('close', 0)
                if price > 0:
                    prices.append(price)
            
            if len(prices) < 2:
                return 0.02  # Varsayılan %2 volatilite
            
            # Basit volatilite hesaplama
            price_changes = []
            for i in range(1, len(prices)):
                change = abs(prices[i] - prices[i-1]) / prices[i-1]
                price_changes.append(change)
            
            return np.mean(price_changes) if price_changes else 0.02
        except:
            return 0.02
    
    def _ai_decision_engine(self, multi_tf_analysis, risk_analysis, timeframe, current_price):
        """AI karar motoru - GERÇEK FİYATLA"""
        trend_alignment = multi_tf_analysis['trend_alignment']
        momentum_score = multi_tf_analysis['momentum_score']
        alignment_ratio = multi_tf_analysis['timeframe_alignment']
        
        # AI skoru hesapla
        ai_score = (
            trend_alignment * 3 + 
            momentum_score * 2 +
            alignment_ratio * 2 +
            random.uniform(-0.5, 0.5)  # Küçük random faktör
        )
        
        # Sinyal gücü
        signal_strength = min(10, max(1, abs(ai_score) * 3))
        
        # ✅ GERÇEK FİYATI KULLAN
        stop_loss_distance = current_price * risk_analysis['stop_loss_pct']
        
        if ai_score > 1.5:
            # AL sinyali - GERÇEK FİYAT ÜZERİNDEN
            entry_price = current_price * 1.002  # 0.2% üstü
            stop_loss = entry_price - stop_loss_distance
            take_profit = [
                entry_price + (stop_loss_distance * 1.5),
                entry_price + (stop_loss_distance * 2.0),
                entry_price + (stop_loss_distance * 3.0)
            ]
            
            return {
                'sinyal': 'AL',
                'ai_skor': round(ai_score, 2),
                'güç': int(signal_strength),
                'zaman': self._get_time_horizon(timeframe),
                'giris_fiyati': round(entry_price, 4),
                'stop_loss': round(stop_loss, 4),
                'take_profit': [round(tp, 4) for tp in take_profit],
                'pozisyon_buyuklugu': round(risk_analysis['position_size'], 4),
                'risk_miktari': round(risk_analysis['risk_per_trade'], 2),
                'risk_reward': risk_analysis['risk_reward_ratio'],
                'kaldıraç': self._get_leverage(signal_strength),
                'neden': self._generate_reason('AL', ai_score, timeframe),
                'mevcut_fiyat': round(current_price, 4)
            }
        
        elif ai_score < -1.5:
            # SAT sinyali - GERÇEK FİYAT ÜZERİNDEN
            entry_price = current_price * 0.998  # 0.2% altı
            stop_loss = entry_price + stop_loss_distance
            take_profit = [
                entry_price - (stop_loss_distance * 1.5),
                entry_price - (stop_loss_distance * 2.0),
                entry_price - (stop_loss_distance * 3.0)
            ]
            
            return {
                'sinyal': 'SAT',
                'ai_skor': round(ai_score, 2),
                'güç': int(signal_strength),
                'zaman': self._get_time_horizon(timeframe),
                'giris_fiyati': round(entry_price, 4),
                'stop_loss': round(stop_loss, 4),
                'take_profit': [round(tp, 4) for tp in take_profit],
                'pozisyon_buyuklugu': round(risk_analysis['position_size'], 4),
                'risk_miktari': round(risk_analysis['risk_per_trade'], 2),
                'risk_reward': risk_analysis['risk_reward_ratio'],
                'kaldıraç': self._get_leverage(signal_strength),
                'neden': self._generate_reason('SAT', ai_score, timeframe),
                'mevcut_fiyat': round(current_price, 4)
            }
        
        else:
            # BEKLE sinyali
            return {
                'sinyal': 'BEKLE',
                'ai_skor': round(ai_score, 2),
                'güç': 1,
                'zaman': self._get_time_horizon(timeframe),
                'giris_fiyati': 0,
                'stop_loss': 0,
                'take_profit': [],
                'pozisyon_buyuklugu': 0,
                'risk_miktari': 0,
                'risk_reward': 0,
                'kaldıraç': '1x',
                'neden': self._generate_reason('BEKLE', ai_score, timeframe),
                'mevcut_fiyat': round(current_price, 4)
            }
    
    def _get_time_horizon(self, timeframe):
        """Zaman dilimine göre yatırım horizonu belirle"""
        horizons = {
            "5m": "ÇOK KISA VADE (Scalping)",
            "15m": "KISA VADE (Day Trading)",
            "1h": "ORTA VADE (Swing Trading)",
            "4h": "UZUN VADE (Position Trading)",
            "1d": "ÇOK UZUN VADE (Investing)"
        }
        return horizons.get(timeframe, "ORTA VADE")
    
    def _get_leverage(self, signal_strength):
        """Sinyal gücüne göre kaldıraç belirle"""
        if signal_strength >= 8:
            return "5x"
        elif signal_strength >= 6:
            return "3x"
        elif signal_strength >= 4:
            return "2x"
        else:
            return "1x"
    
    def _generate_reason(self, signal, ai_score, timeframe):
        """AI kararı için açıklama oluştur"""
        reasons = {
            'AL': [
                f"Güçlü alım sinyali - Çoklu zaman dilimlerinde uyum ({timeframe})",
                f"Teknik göstergeler yükselişi destekliyor - AI Skor: {ai_score:.2f}",
                f"Trend uyumu pozitif - {timeframe} zaman diliminde fırsat"
            ],
            'SAT': [
                f"Satış baskısı oluştu - Çoklu zaman dilimlerinde uyum ({timeframe})",
                f"Teknik göstergeler düşüşü işaret ediyor - AI Skor: {ai_score:.2f}",
                f"Trend uyumu negatif - {timeframe} zaman diliminde risk"
            ],
            'BEKLE': [
                f"Piyasa belirsiz - {timeframe} zaman diliminde net trend yok",
                f"Teknik göstergeler kararsız - AI Skor: {ai_score:.2f}",
                f"Zaman dilimleri uyumsuz - {timeframe} için daha net sinyal bekleyin"
            ]
        }
        
        return random.choice(reasons.get(signal, ["Analiz tamamlandı"]))
    
    def _get_fallback_signal(self):
        """Fallback sinyal oluştur"""
        return {
            'sinyal': 'BEKLE',
            'ai_skor': 0,
            'güç': 1,
            'zaman': "ORTA VADE",
            'giris_fiyati': 0,
            'stop_loss': 0,
            'take_profit': [],
            'pozisyon_buyuklugu': 0,
            'risk_miktari': 0,
            'risk_reward': 0,
            'kaldıraç': '1x',
            'neden': "Sistem hatası - Fallback modu aktif",
            'mevcut_fiyat': 0
        }