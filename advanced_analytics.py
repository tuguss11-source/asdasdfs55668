# advanced_analytics.py - TAMAMLANDI
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
import json
warnings.filterwarnings('ignore')

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedAnalytics:
    def __init__(self, portfolio_manager=None):
        self.portfolio_manager = portfolio_manager
        self.performance_metrics = {}
        
        logger.info("📊 Gelişmiş Analitik Başlatıldı")
    
    def get_comprehensive_analytics(self) -> Dict:
        """Kapsamlı analitik raporu oluştur"""
        try:
            portfolio_data = self.portfolio_manager.get_portfolio() if self.portfolio_manager else []
            trade_history = self.portfolio_manager.get_trade_history(100) if self.portfolio_manager else []
            portfolio_summary = self.portfolio_manager.get_portfolio_summary() if self.portfolio_manager else {}
            
            analytics = {
                "portfolio_metrics": self._calculate_portfolio_metrics(portfolio_data, portfolio_summary),
                "performance_analysis": self._analyze_performance(trade_history),
                "risk_metrics": self._calculate_risk_metrics(trade_history, portfolio_summary),
                "ai_analytics": self._analyze_ai_performance(),
                "market_analytics": self._analyze_market_correlation(),
                "recommendations": self._generate_recommendations(portfolio_data, trade_history)
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Analytics hatası: {e}")
            return {"error": str(e)}
    
    def _calculate_portfolio_metrics(self, portfolio_data: List, portfolio_summary: Dict) -> Dict:
        """Portföy metriklerini hesapla"""
        try:
            if not portfolio_data:
                return {
                    "total_value": 0,
                    "total_invested": 0,
                    "unrealized_pnl": 0,
                    "pnl_percent": 0,
                    "positions_count": 0,
                    "diversification_score": 0,
                    "sector_allocation": {}
                }
            
            # Temel metrikler
            total_value = portfolio_summary.get('total_value', 0)
            total_invested = portfolio_summary.get('total_invested', 0)
            unrealized_pnl = portfolio_summary.get('total_unrealized_pnl', 0)
            pnl_percent = portfolio_summary.get('total_pnl_percent', 0)
            
            # Çeşitlilik skoru
            symbols = [pos[1] for pos in portfolio_data]  # symbol column
            unique_symbols = len(set(symbols))
            diversification_score = min(100, (unique_symbols / len(symbols)) * 100) if symbols else 0
            
            # Sektör dağılımı (basit)
            sector_allocation = {}
            for symbol in symbols:
                sector = self._classify_asset(symbol)
                sector_allocation[sector] = sector_allocation.get(sector, 0) + 1
            
            # Ağırlıklı dağılım
            total_positions = len(symbols)
            for sector in sector_allocation:
                sector_allocation[sector] = (sector_allocation[sector] / total_positions) * 100
            
            return {
                "total_value": total_value,
                "total_invested": total_invested,
                "unrealized_pnl": unrealized_pnl,
                "pnl_percent": pnl_percent,
                "positions_count": len(portfolio_data),
                "diversification_score": diversification_score,
                "sector_allocation": sector_allocation,
                "avg_position_size": total_value / len(portfolio_data) if portfolio_data else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Portfolio metrics hatası: {e}")
            return {}
    
    def _analyze_performance(self, trade_history: List) -> Dict:
        """Performans analizi yap"""
        try:
            if not trade_history:
                return {
                    "total_trades": 0,
                    "win_rate": 0,
                    "avg_profit": 0,
                    "total_profit": 0,
                    "sharpe_ratio": 0,
                    "max_drawdown": 0,
                    "profit_factor": 0
                }
            
            # Temel istatistikler
            profits = [trade[7] for trade in trade_history]  # profit_loss column
            winning_trades = [p for p in profits if p > 0]
            losing_trades = [p for p in profits if p < 0]
            
            total_trades = len(trade_history)
            win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
            avg_profit = np.mean(profits) if profits else 0
            total_profit = sum(profits)
            
            # Sharpe Ratio (basit)
            returns = [p / 1000 for p in profits]  # Normalize
            sharpe_ratio = np.mean(returns) / np.std(returns) if len(returns) > 1 and np.std(returns) > 0 else 0
            
            # Maximum Drawdown
            cumulative_returns = np.cumsum(returns)
            peak = cumulative_returns[0]
            max_drawdown = 0
            
            for ret in cumulative_returns:
                if ret > peak:
                    peak = ret
                drawdown = (peak - ret) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # Profit Factor
            gross_profit = sum(winning_trades) if winning_trades else 0
            gross_loss = abs(sum(losing_trades)) if losing_trades else 0
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            # Trade frequency
            if len(trade_history) > 1:
                timestamps = [datetime.fromisoformat(trade[5]) for trade in trade_history]  # timestamp column
                timestamps.sort()
                avg_trade_duration = np.mean([(timestamps[i+1] - timestamps[i]).total_seconds() / 3600 
                                            for i in range(len(timestamps)-1)])
            else:
                avg_trade_duration = 0
            
            return {
                "total_trades": total_trades,
                "win_rate": win_rate,
                "avg_profit": avg_profit,
                "total_profit": total_profit,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "profit_factor": profit_factor,
                "avg_trade_duration_hours": avg_trade_duration,
                "best_trade": max(profits) if profits else 0,
                "worst_trade": min(profits) if profits else 0,
                "winning_streak": self._calculate_winning_streak(profits),
                "losing_streak": self._calculate_losing_streak(profits)
            }
            
        except Exception as e:
            logger.error(f"❌ Performance analysis hatası: {e}")
            return {}
    
    def _calculate_risk_metrics(self, trade_history: List, portfolio_summary: Dict) -> Dict:
        """Risk metriklerini hesapla"""
        try:
            if not trade_history:
                return {
                    "var_95": 0,
                    "expected_shortfall": 0,
                    "volatility": 0,
                    "beta": 1.0,
                    "value_at_risk": 0,
                    "risk_adjusted_return": 0
                }
            
            profits = [trade[7] for trade in trade_history]  # profit_loss column
            
            # Value at Risk (VaR) - Historical method
            var_95 = np.percentile(profits, 5) if len(profits) > 1 else 0
            
            # Expected Shortfall (CVaR)
            es_95 = np.mean([p for p in profits if p <= var_95]) if any(p <= var_95 for p in profits) else var_95
            
            # Volatilite
            volatility = np.std(profits) if len(profits) > 1 else 0
            
            # Beta (basit)
            beta = 1.2  # Gerçek uygulamada market correlation
            
            # Risk-adjusted return
            total_return = portfolio_summary.get('total_pnl_percent', 0)
            risk_adjusted_return = total_return / max(volatility, 0.01)
            
            return {
                "var_95": var_95,
                "expected_shortfall": es_95,
                "volatility": volatility,
                "beta": beta,
                "value_at_risk": var_95,
                "risk_adjusted_return": risk_adjusted_return,
                "calmar_ratio": total_return / max(abs(portfolio_summary.get('total_pnl_percent', 0)), 0.01)
            }
            
        except Exception as e:
            logger.error(f"❌ Risk metrics hatası: {e}")
            return {}
    
    def _analyze_ai_performance(self) -> Dict:
        """AI performans analizi"""
        try:
            # AI sinyal geçmişini al
            if self.portfolio_manager:
                signal_history = self.portfolio_manager.get_ai_signal_history(limit=100)
            else:
                signal_history = []
            
            if not signal_history:
                return {
                    "total_signals": 0,
                    "signal_accuracy": 0,
                    "avg_confidence": 0,
                    "best_strategy": "N/A",
                    "strategy_performance": {}
                }
            
            # Sinyal analizi
            signals = [signal[2] for signal in signal_history]  # signal column
            strengths = [signal[3] for signal in signal_history]  # strength column
            confidences = [json.loads(signal[7]).get('composite_confidence', 0) 
                         if signal[7] else 0 for signal in signal_history]  # strategy_breakdown column
            
            total_signals = len(signal_history)
            avg_strength = np.mean(strengths) if strengths else 0
            avg_confidence = np.mean(confidences) if confidences else 0
            
            # Strateji performansı
            strategy_performance = {}
            for signal in signal_history:
                breakdown = json.loads(signal[7]) if signal[7] else {}
                strategy = breakdown.get('best_strategy', 'unknown')
                if strategy not in strategy_performance:
                    strategy_performance[strategy] = []
                strategy_performance[strategy].append(signal[3])  # strength
            
            # En iyi strateji
            best_strategy = max(strategy_performance.items(), 
                              key=lambda x: np.mean(x[1]))[0] if strategy_performance else "N/A"
            
            return {
                "total_signals": total_signals,
                "signal_accuracy": self._estimate_signal_accuracy(signal_history),
                "avg_strength": avg_strength,
                "avg_confidence": avg_confidence,
                "best_strategy": best_strategy,
                "strategy_performance": {k: np.mean(v) for k, v in strategy_performance.items()}
            }
            
        except Exception as e:
            logger.error(f"❌ AI performance analysis hatası: {e}")
            return {}
    
    def _analyze_market_correlation(self) -> Dict:
        """Piyasa korelasyon analizi"""
        # Basit implementasyon - gerçek uygulamada historical price data
        return {
            "btc_correlation": 0.85,
            "market_beta": 1.2,
            "sector_correlation": {
                "defi": 0.75,
                "layer1": 0.82,
                "ai_tokens": 0.68
            }
        }
    
    def _generate_recommendations(self, portfolio_data: List, trade_history: List) -> List[str]:
        """Öneriler oluştur"""
        recommendations = []
        
        try:
            # Portfolio çeşitliliği kontrolü
            if len(portfolio_data) > 8:
                recommendations.append("⚠️ Çok fazla pozisyon açıksınız. Konsolidasyon önerilir.")
            
            # Risk konsantrasyonu
            symbols = [pos[1] for pos in portfolio_data]
            if len(set(symbols)) < 3:
                recommendations.append("📊 Portföy çeşitliliğiniz düşük. Farklı asset'ler ekleyin.")
            
            # Performans bazlı öneriler
            if trade_history:
                recent_trades = trade_history[:10]  # Son 10 trade
                recent_profits = [trade[7] for trade in recent_trades]
                recent_win_rate = len([p for p in recent_profits if p > 0]) / len(recent_profits) * 100
                
                if recent_win_rate < 40:
                    recommendations.append("📉 Son tradelarınızda başarı oranı düşük. Stratejinizi gözden geçirin.")
            
            # Pozisyon büyüklüğü
            portfolio_summary = self.portfolio_manager.get_portfolio_summary() if self.portfolio_manager else {}
            if portfolio_summary.get('total_pnl_percent', 0) < -10:
                recommendations.append("🔴 Portföyünüzde significant kayıp var. Risk yönetimini sıkılaştırın.")
            
            # Genel öneri
            if not recommendations:
                recommendations.append("✅ Portföyünüz dengeli görünüyor. Mevcut stratejinize devam edin.")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Recommendations hatası: {e}")
            return ["Analiz tamamlandı"]
    
    def _classify_asset(self, symbol: str) -> str:
        """Asset'i kategorize et"""
        symbol_upper = symbol.upper()
        
        if 'BTC' in symbol_upper:
            return "Store of Value"
        elif 'ETH' in symbol_upper:
            return "Smart Contract"
        elif any(coin in symbol_upper for coin in ['ADA', 'SOL', 'DOT', 'AVAX']):
            return "Layer 1"
        elif any(coin in symbol_upper for coin in ['LINK', 'UNI', 'AAVE']):
            return "DeFi"
        elif any(coin in symbol_upper for coin in ['MATIC', 'ARB', 'OP']):
            return "Layer 2"
        else:
            return "Other"
    
    def _calculate_winning_streak(self, profits: List[float]) -> int:
        """Kazanma serisini hesapla"""
        if not profits:
            return 0
        
        max_streak = 0
        current_streak = 0
        
        for profit in profits:
            if profit > 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    def _calculate_losing_streak(self, profits: List[float]) -> int:
        """Kaybetme serisini hesapla"""
        if not profits:
            return 0
        
        max_streak = 0
        current_streak = 0
        
        for profit in profits:
            if profit < 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    def _estimate_signal_accuracy(self, signal_history: List) -> float:
        """Sinyal doğruluğunu tahmin et"""
        # Basit implementasyon - gerçek uygulamada trade results ile karşılaştırma
        if not signal_history:
            return 0
        
        # Strength ve confidence'a göre tahmini accuracy
        total_accuracy = 0
        for signal in signal_history:
            strength = signal[3]  # strength column
            confidence = json.loads(signal[7]).get('composite_confidence', 0) if signal[7] else 0
            
            # Basit accuracy hesaplama
            signal_accuracy = (strength / 10) * (confidence / 100)
            total_accuracy += signal_accuracy
        
        return (total_accuracy / len(signal_history)) * 100
    
    def create_performance_dashboard(self) -> go.Figure:
        """Performans dashboard'u oluştur"""
        try:
            if not self.portfolio_manager:
                return self._create_empty_dashboard()
            
            trade_history = self.portfolio_manager.get_trade_history(50)
            portfolio_summary = self.portfolio_manager.get_portfolio_summary()
            
            # 2x2 subplot
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Portföy Performansı', 'Trade Dağılımı', 
                              'Risk Metrikleri', 'AI Sinyal Gücü'),
                specs=[[{"type": "xy"}, {"type": "domain"}],
                       [{"type": "xy"}, {"type": "xy"}]]
            )
            
            # Portföy performansı
            if trade_history:
                dates = [datetime.fromisoformat(trade[5]) for trade in trade_history]  # timestamp
                profits = [trade[7] for trade in trade_history]  # profit_loss
                cumulative_profits = np.cumsum(profits)
                
                fig.add_trace(
                    go.Scatter(x=dates, y=cumulative_profits, mode='lines', name='Kümülatif Kar'),
                    row=1, col=1
                )
            
            # Trade dağılımı
            if trade_history:
                winning = len([p for p in profits if p > 0])
                losing = len([p for p in profits if p < 0])
                neutral = len([p for p in profits if p == 0])
                
                fig.add_trace(
                    go.Pie(labels=['Kazanan', 'Kaybeden', 'Nötr'], 
                          values=[winning, losing, neutral],
                          name='Trade Dağılımı'),
                    row=1, col=2
                )
            
            # Risk metrikleri
            risk_data = self._calculate_risk_metrics(trade_history, portfolio_summary)
            risk_categories = ['Volatilite', 'Max Drawdown', 'VaR', 'Beta']
            risk_values = [
                risk_data.get('volatility', 0) * 100,
                risk_data.get('max_drawdown', 0) * 100,
                abs(risk_data.get('var_95', 0)),
                risk_data.get('beta', 1.0)
            ]
            
            fig.add_trace(
                go.Bar(x=risk_categories, y=risk_values, name='Risk Metrikleri'),
                row=2, col=1
            )
            
            # AI sinyal gücü
            signal_history = self.portfolio_manager.get_ai_signal_history(limit=20)
            if signal_history:
                signal_strengths = [signal[3] for signal in signal_history]  # strength
                signal_dates = [datetime.fromisoformat(signal[5]) for signal in signal_history]  # timestamp
                
                fig.add_trace(
                    go.Scatter(x=signal_dates, y=signal_strengths, mode='lines+markers', 
                              name='AI Sinyal Gücü'),
                    row=2, col=2
                )
            
            fig.update_layout(height=600, showlegend=True, title_text="Gelişmiş Performans Dashboard")
            return fig
            
        except Exception as e:
            logger.error(f"❌ Dashboard creation hatası: {e}")
            return self._create_empty_dashboard()
    
    def _create_empty_dashboard(self) -> go.Figure:
        """Boş dashboard oluştur"""
        fig = make_subplots(rows=2, cols=2,
                          subplot_titles=('Portföy Performansı', 'Trade Dağılımı', 
                                        'Risk Metrikleri', 'AI Sinyal Gücü'))
        
        fig.add_annotation(text="Yeterli veri bulunamadı",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        
        fig.update_layout(height=600, title_text="Gelişmiş Performans Dashboard")
        return fig

# Analytics Factory
class AnalyticsFactory:
    @staticmethod
    def create_analytics(analytics_type="advanced", portfolio_manager=None):
        if analytics_type == "advanced":
            return AdvancedAnalytics(portfolio_manager)
        else:
            return AdvancedAnalytics(portfolio_manager)  # Fallback