# risk_manager.py - YENİ DOSYA
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, config=None):
        self.config = config or {
            "max_drawdown": 0.15,  # %15
            "var_limit": 0.05,     # %5 VaR
            "correlation_threshold": 0.7,
            "portfolio_beta_limit": 1.5,
            "max_position_size": 0.1,  # %10
            "daily_loss_limit": -0.05,  # -%5
            "volatility_limit": 0.5,    # %50 volatilite
            "black_swan_protection": True
        }
        
        self.portfolio_history = []
        self.trade_history = []
        self.market_data = {}
        
        logger.info("⚖️ Gelişmiş Risk Yöneticisi Başlatıldı")
    
    def check_trade_risk(self, signal_data: Dict) -> Dict:
        """Trade için risk değerlendirmesi yap"""
        try:
            symbol = signal_data.get('symbol', '')
            signal = signal_data.get('signal', {})
            
            risk_checks = [
                self._check_position_size(signal),
                self._check_portfolio_concentration(symbol),
                self._check_correlation_risk(symbol),
                self._check_volatility_risk(signal),
                self._check_drawdown_risk(),
                self._check_var_risk(signal),
                self._check_black_swan_risk(symbol)
            ]
            
            # Tüm risk kontrollerini değerlendir
            approved = all(check['approved'] for check in risk_checks)
            reasons = [check['reason'] for check in risk_checks if not check['approved']]
            
            risk_score = self._calculate_risk_score(risk_checks)
            
            return {
                "approved": approved,
                "risk_score": risk_score,
                "reasons": reasons,
                "details": {
                    "position_size_risk": risk_checks[0]['risk_level'],
                    "concentration_risk": risk_checks[1]['risk_level'],
                    "correlation_risk": risk_checks[2]['risk_level'],
                    "volatility_risk": risk_checks[3]['risk_level'],
                    "drawdown_risk": risk_checks[4]['risk_level'],
                    "var_risk": risk_checks[5]['risk_level'],
                    "black_swan_risk": risk_checks[6]['risk_level']
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Risk check hatası: {e}")
            return {"approved": False, "risk_score": 10, "reasons": ["Risk analiz hatası"]}
    
    def _check_position_size(self, signal: Dict) -> Dict:
        """Pozisyon büyüklüğü riski"""
        try:
            position_size = signal.get('pozisyon_buyuklugu', 0)
            current_price = signal.get('mevcut_fiyat', 0)
            position_value = position_size * current_price
            
            max_position_value = self.config['max_position_size']
            
            if position_value > max_position_value:
                risk_level = "HIGH"
                approved = False
                reason = f"Pozisyon büyüklüğü limiti aşıldı: {position_value:,.2f} > {max_position_value:,.2f}"
            elif position_value > max_position_value * 0.8:
                risk_level = "MEDIUM"
                approved = True
                reason = "Pozisyon büyüklüğü yüksek"
            else:
                risk_level = "LOW"
                approved = True
                reason = "Pozisyon büyüklüğü uygun"
            
            return {"approved": approved, "risk_level": risk_level, "reason": reason}
            
        except Exception as e:
            return {"approved": False, "risk_level": "HIGH", "reason": f"Position size check error: {e}"}
    
    def _check_portfolio_concentration(self, symbol: str) -> Dict:
        """Portföy konsantrasyon riski"""
        try:
            # Mevcut portföydeki aynı sembol pozisyonlarını say
            same_symbol_positions = sum(1 for trade in self.trade_history 
                                      if trade.get('symbol') == symbol and trade.get('status') == 'active')
            
            if same_symbol_positions >= 3:
                risk_level = "HIGH"
                approved = False
                reason = f"Aynı sembolde çok fazla pozisyon: {same_symbol_positions}"
            elif same_symbol_positions >= 2:
                risk_level = "MEDIUM"
                approved = True
                reason = "Aynı sembolde birden fazla pozisyon"
            else:
                risk_level = "LOW"
                approved = True
                reason = "Konsantrasyon riski düşük"
            
            return {"approved": approved, "risk_level": risk_level, "reason": reason}
            
        except Exception as e:
            return {"approved": False, "risk_level": "HIGH", "reason": f"Concentration check error: {e}"}
    
    def _check_correlation_risk(self, symbol: str) -> Dict:
        """Korelasyon riski"""
        try:
            # Basit korelasyon analizi (gerçek uygulamada historical data kullan)
            crypto_correlations = {
                'BTC': ['ETH', 'ADA', 'SOL', 'DOT'],
                'ETH': ['BTC', 'ADA', 'SOL', 'DOT'],
                'ADA': ['BTC', 'ETH', 'SOL'],
                'SOL': ['BTC', 'ETH', 'ADA']
            }
            
            # Mevcut pozisyonlarla korelasyon kontrolü
            correlated_positions = 0
            for trade in self.trade_history:
                if trade.get('status') == 'active':
                    trade_symbol = trade.get('symbol', '')
                    base_symbol = symbol.split(':')[-1].replace('USDT', '')
                    
                    if base_symbol in crypto_correlations:
                        correlated_coins = crypto_correlations[base_symbol]
                        if any(coin in trade_symbol for coin in correlated_coins):
                            correlated_positions += 1
            
            if correlated_positions >= 3:
                risk_level = "HIGH"
                approved = False
                reason = f"Yüksek korelasyon riski: {correlated_positions} ilişkili pozisyon"
            elif correlated_positions >= 2:
                risk_level = "MEDIUM"
                approved = True
                reason = "Orta korelasyon riski"
            else:
                risk_level = "LOW"
                approved = True
                reason = "Korelasyon riski düşük"
            
            return {"approved": approved, "risk_level": risk_level, "reason": reason}
            
        except Exception as e:
            return {"approved": True, "risk_level": "MEDIUM", "reason": f"Correlation check error: {e}"}
    
    def _check_volatility_risk(self, signal: Dict) -> Dict:
        """Volatilite riski"""
        try:
            # Sinyal volatilite bilgisi
            volatility = signal.get('strategy_breakdown', {}).get('volatility', 0.02)
            
            if volatility > self.config['volatility_limit']:
                risk_level = "HIGH"
                approved = False
                reason = f"Yüksek volatilite: %{volatility*100:.1f}"
            elif volatility > self.config['volatility_limit'] * 0.7:
                risk_level = "MEDIUM"
                approved = True
                reason = f"Orta volatilite: %{volatility*100:.1f}"
            else:
                risk_level = "LOW"
                approved = True
                reason = f"Düşük volatilite: %{volatility*100:.1f}"
            
            return {"approved": approved, "risk_level": risk_level, "reason": reason}
            
        except Exception as e:
            return {"approved": True, "risk_level": "MEDIUM", "reason": f"Volatility check error: {e}"}
    
    def _check_drawdown_risk(self) -> Dict:
        """Drawdown riski"""
        try:
            if not self.portfolio_history:
                return {"approved": True, "risk_level": "LOW", "reason": "Yetersiz veri"}
            
            # Portfolio değerlerini al
            portfolio_values = [entry['value'] for entry in self.portfolio_history]
            
            # Maksimum drawdown hesapla
            peak = portfolio_values[0]
            max_drawdown = 0
            
            for value in portfolio_values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            if max_drawdown > self.config['max_drawdown']:
                risk_level = "HIGH"
                approved = False
                reason = f"Yüksek drawdown: %{max_drawdown*100:.1f}"
            elif max_drawdown > self.config['max_drawdown'] * 0.8:
                risk_level = "MEDIUM"
                approved = True
                reason = f"Orta drawdown: %{max_drawdown*100:.1f}"
            else:
                risk_level = "LOW"
                approved = True
                reason = f"Düşük drawdown: %{max_drawdown*100:.1f}"
            
            return {"approved": approved, "risk_level": risk_level, "reason": reason}
            
        except Exception as e:
            return {"approved": True, "risk_level": "MEDIUM", "reason": f"Drawdown check error: {e}"}
    
    def _check_var_risk(self, signal: Dict) -> Dict:
        """Value at Risk kontrolü"""
        try:
            position_size = signal.get('pozisyon_buyuklugu', 0)
            current_price = signal.get('mevcut_fiyat', 0)
            position_value = position_size * current_price
            
            # Basit VaR hesaplama (1 gün, %95 güven)
            volatility = signal.get('strategy_breakdown', {}).get('volatility', 0.02)
            var_95 = position_value * volatility * 1.645  # 1.645 = Z-score for 95%
            
            if var_95 > position_value * self.config['var_limit']:
                risk_level = "HIGH"
                approved = False
                reason = f"Yüksek VaR riski: ${var_95:,.2f}"
            else:
                risk_level = "LOW"
                approved = True
                reason = f"VaR riski kabul edilebilir: ${var_95:,.2f}"
            
            return {"approved": approved, "risk_level": risk_level, "reason": reason}
            
        except Exception as e:
            return {"approved": True, "risk_level": "MEDIUM", "reason": f"VaR check error: {e}"}
    
    def _check_black_swan_risk(self, symbol: str) -> Dict:
        """Black Swan riski (aşırı olaylar)"""
        try:
            if not self.config['black_swan_protection']:
                return {"approved": True, "risk_level": "LOW", "reason": "Black Swan protection kapalı"}
            
            # Basit black swan kontrolü
            # Gerçek uygulamada market stress göstergeleri kullanılmalı
            black_swan_indicators = {
                'vix_spike': False,
                'liquidity_crunch': False,
                'market_crash': False
            }
            
            # Örnek: Yüksek volatilite black swan işareti olabilir
            if self._get_market_stress_level() > 0.8:
                risk_level = "HIGH"
                approved = False
                reason = "Yüksek piyasa stresi - Black Swan riski"
            else:
                risk_level = "LOW"
                approved = True
                reason = "Black Swan riski düşük"
            
            return {"approved": approved, "risk_level": risk_level, "reason": reason}
            
        except Exception as e:
            return {"approved": True, "risk_level": "MEDIUM", "reason": f"Black Swan check error: {e}"}
    
    def _get_market_stress_level(self) -> float:
        """Piyasa stres seviyesi (0-1)"""
        # Basit implementasyon - gerçek uygulamada çeşitli göstergeler
        return 0.3  # Örnek değer
    
    def _calculate_risk_score(self, risk_checks: List[Dict]) -> float:
        """Toplam risk skoru hesapla (0-10)"""
        risk_weights = {
            "HIGH": 2.0,
            "MEDIUM": 1.0,
            "LOW": 0.3
        }
        
        total_score = 0
        for check in risk_checks:
            risk_level = check.get('risk_level', 'LOW')
            total_score += risk_weights.get(risk_level, 0.5)
        
        # Normalize to 0-10 scale
        max_possible_score = len(risk_checks) * risk_weights['HIGH']
        normalized_score = (total_score / max_possible_score) * 10
        
        return min(10, normalized_score)
    
    def update_portfolio_history(self, portfolio_value: float):
        """Portföy geçmişini güncelle"""
        self.portfolio_history.append({
            'timestamp': datetime.now().isoformat(),
            'value': portfolio_value
        })
        
        # Son 30 günlük veriyi tut
        if len(self.portfolio_history) > 30:
            self.portfolio_history = self.portfolio_history[-30:]
    
    def update_trade_history(self, trade_data: Dict):
        """Trade geçmişini güncelle"""
        self.trade_history.append(trade_data)
        
        # Son 100 trade'i tut
        if len(self.trade_history) > 100:
            self.trade_history = self.trade_history[-100:]
    
    def get_risk_report(self) -> Dict:
        """Detaylı risk raporu oluştur"""
        try:
            if not self.portfolio_history:
                return {"error": "Yetersiz veri"}
            
            portfolio_values = [entry['value'] for entry in self.portfolio_history]
            
            # Çeşitli risk metrikleri
            current_value = portfolio_values[-1]
            max_value = max(portfolio_values)
            min_value = min(portfolio_values)
            
            # Volatilite
            returns = []
            for i in range(1, len(portfolio_values)):
                ret = (portfolio_values[i] - portfolio_values[i-1]) / portfolio_values[i-1]
                returns.append(ret)
            
            volatility = np.std(returns) if returns else 0
            
            # Sharpe Ratio (basit)
            avg_return = np.mean(returns) if returns else 0
            sharpe_ratio = avg_return / volatility if volatility > 0 else 0
            
            # Maximum Drawdown
            peak = portfolio_values[0]
            max_dd = 0
            for value in portfolio_values:
                if value > peak:
                    peak = value
                dd = (peak - value) / peak
                if dd > max_dd:
                    max_dd = dd
            
            # VaR (Value at Risk)
            var_95 = np.percentile(returns, 5) if returns else 0
            
            # Beta (basit - portföyün piyasaya duyarlılığı)
            portfolio_beta = self._calculate_portfolio_beta()
            
            return {
                "current_value": current_value,
                "max_value": max_value,
                "min_value": min_value,
                "volatility": volatility,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_dd,
                "var_95": var_95,
                "portfolio_beta": portfolio_beta,
                "active_trades": len([t for t in self.trade_history if t.get('status') == 'active']),
                "total_trades": len(self.trade_history),
                "risk_score": self._calculate_overall_risk_score(volatility, max_dd, portfolio_beta)
            }
            
        except Exception as e:
            logger.error(f"❌ Risk report hatası: {e}")
            return {"error": str(e)}
    
    def _calculate_portfolio_beta(self) -> float:
        """Portföy beta katsayısı (basit implementasyon)"""
        # Gerçek uygulamada market returns vs portfolio returns correlation
        return 1.2  # Örnek değer
    
    def _calculate_overall_risk_score(self, volatility: float, max_dd: float, beta: float) -> float:
        """Genel risk skoru hesapla"""
        vol_score = min(10, volatility * 100 * 2)  # Volatilite skoru
        dd_score = min(10, max_dd * 100 * 1.5)    # Drawdown skoru
        beta_score = min(10, beta * 5)            # Beta skoru
        
        return (vol_score + dd_score + beta_score) / 3

# Risk Manager Factory
class RiskManagerFactory:
    @staticmethod
    def create_risk_manager(manager_type="advanced", config=None):
        if manager_type == "advanced":
            return RiskManager(config)
        else:
            return RiskManager(config)  # Fallback