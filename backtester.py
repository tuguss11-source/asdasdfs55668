# backtester.py - YENİ DOSYA
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import warnings
warnings.filterwarnings('ignore')

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Backtester:
    def __init__(self, config=None):
        self.config = config or {
            "initial_capital": 1000,
            "commission": 0.001,  # %0.1
            "slippage": 0.002,    # %0.2
            "max_drawdown": 0.2,  # %20
            "risk_free_rate": 0.02  # %2
        }
        
        self.results = {}
        logger.info("🔧 Backtester Başlatıldı")
    
    def run_backtest(self, strategy: str, symbols: List[str], days: int = 30, 
                    initial_capital: float = 1000) -> Dict:
        """Backtest çalıştır"""
        try:
            logger.info(f"🧪 Backtest başlatılıyor: {strategy}, {len(symbols)} sembol, {days} gün")
            
            # Simüle historical data oluştur
            historical_data = self._generate_historical_data(symbols, days)
            
            # Stratejiye göre backtest çalıştır
            if strategy == "ai_trading":
                results = self._run_ai_strategy_backtest(historical_data, initial_capital)
            elif strategy == "momentum":
                results = self._run_momentum_strategy_backtest(historical_data, initial_capital)
            elif strategy == "mean_reversion":
                results = self._run_mean_reversion_backtest(historical_data, initial_capital)
            else:
                results = self._run_buy_hold_backtest(historical_data, initial_capital)
            
            self.results = results
            logger.info(f"✅ Backtest tamamlandı: {results.get('total_return', 0)*100:.2f}% getiri")
            return results
            
        except Exception as e:
            logger.error(f"❌ Backtest hatası: {e}")
            return {"error": str(e)}
    
    def _run_ai_strategy_backtest(self, historical_data: Dict, initial_capital: float) -> Dict:
        """AI stratejisi backtest"""
        try:
            capital = initial_capital
            portfolio = {}
            trades = []
            portfolio_values = [initial_capital]
            dates = list(historical_data.keys())
            dates.sort()
            
            for i, date in enumerate(dates):
                if i == 0:
                    continue
                
                daily_data = historical_data[date]
                previous_data = historical_data[dates[i-1]]
                
                # Her sembol için AI sinyali simüle et
                for symbol in daily_data.keys():
                    if symbol not in portfolio:
                        portfolio[symbol] = 0
                    
                    # Basit AI sinyal simülasyonu
                    signal = self._simulate_ai_signal(symbol, daily_data[symbol], previous_data.get(symbol, {}))
                    
                    if signal['action'] == 'BUY' and capital > 100:
                        # Position size hesapla
                        position_size = min(capital * 0.2, capital * 0.1)  # Max %20, typical %10
                        price = daily_data[symbol]['close'] * (1 + self.config['slippage'])
                        quantity = position_size / price
                        
                        # Alım yap
                        cost = quantity * price * (1 + self.config['commission'])
                        if cost <= capital:
                            capital -= cost
                            portfolio[symbol] += quantity
                            
                            trades.append({
                                'date': date,
                                'symbol': symbol,
                                'action': 'BUY',
                                'price': price,
                                'quantity': quantity,
                                'cost': cost
                            })
                    
                    elif signal['action'] == 'SELL' and portfolio[symbol] > 0:
                        # Satım yap
                        price = daily_data[symbol]['close'] * (1 - self.config['slippage'])
                        quantity = portfolio[symbol]
                        revenue = quantity * price * (1 - self.config['commission'])
                        
                        capital += revenue
                        portfolio[symbol] = 0
                        
                        trades.append({
                            'date': date,
                            'symbol': symbol,
                            'action': 'SELL',
                            'price': price,
                            'quantity': quantity,
                            'revenue': revenue
                        })
                
                # Portfolio değerini hesapla
                portfolio_value = capital
                for symbol, quantity in portfolio.items():
                    if quantity > 0:
                        portfolio_value += quantity * daily_data[symbol]['close']
                
                portfolio_values.append(portfolio_value)
            
            # Performans metriklerini hesapla
            return self._calculate_performance_metrics(portfolio_values, trades, initial_capital)
            
        except Exception as e:
            logger.error(f"❌ AI strategy backtest hatası: {e}")
            return {"error": str(e)}
    
    def _run_momentum_strategy_backtest(self, historical_data: Dict, initial_capital: float) -> Dict:
        """Momentum stratejisi backtest"""
        # Implementasyon benzer şekilde yapılabilir
        return self._run_buy_hold_backtest(historical_data, initial_capital)
    
    def _run_mean_reversion_backtest(self, historical_data: Dict, initial_capital: float) -> Dict:
        """Mean reversion stratejisi backtest"""
        # Implementasyon benzer şekilde yapılabilir
        return self._run_buy_hold_backtest(historical_data, initial_capital)
    
    def _run_buy_hold_backtest(self, historical_data: Dict, initial_capital: float) -> Dict:
        """Buy & Hold stratejisi backtest"""
        try:
            dates = list(historical_data.keys())
            dates.sort()
            
            if not dates:
                return {"error": "Yetersiz veri"}
            
            # İlk gün eşit dağılımda al
            first_date = dates[0]
            symbols = list(historical_data[first_date].keys())
            capital_per_symbol = initial_capital / len(symbols)
            
            portfolio = {}
            for symbol in symbols:
                price = historical_data[first_date][symbol]['close']
                portfolio[symbol] = capital_per_symbol / price
            
            # Portfolio değerlerini takip et
            portfolio_values = []
            for date in dates:
                portfolio_value = 0
                for symbol, quantity in portfolio.items():
                    if symbol in historical_data[date]:
                        portfolio_value += quantity * historical_data[date][symbol]['close']
                portfolio_values.append(portfolio_value)
            
            # Basit trade listesi oluştur
            trades = [{
                'date': first_date,
                'action': 'BUY',
                'symbol': 'ALL',
                'quantity': 1,
                'price': portfolio_values[0]
            }]
            
            return self._calculate_performance_metrics(portfolio_values, trades, initial_capital)
            
        except Exception as e:
            logger.error(f"❌ Buy & Hold backtest hatası: {e}")
            return {"error": str(e)}
    
    def _simulate_ai_signal(self, symbol: str, current_data: Dict, previous_data: Dict) -> Dict:
        """AI sinyali simüle et"""
        try:
            # Basit sinyal simülasyonu
            price_change = ((current_data['close'] - previous_data.get('close', current_data['close'])) 
                          / previous_data.get('close', current_data['close']))
            
            rsi = current_data.get('rsi', 50)
            macd = current_data.get('macd', 0)
            
            # Momentum bazlı sinyal
            if price_change > 0.02 and rsi < 70:  # %2'den fazla artış ve RSI aşırı alım değil
                return {'action': 'BUY', 'confidence': 0.7}
            elif price_change < -0.02 and rsi > 30:  # %2'den fazla düşüş ve RSI aşırı satım değil
                return {'action': 'SELL', 'confidence': 0.6}
            else:
                return {'action': 'HOLD', 'confidence': 0.5}
                
        except Exception as e:
            return {'action': 'HOLD', 'confidence': 0.5}
    
    def _generate_historical_data(self, symbols: List[str], days: int) -> Dict:
        """Historical data simüle et"""
        historical_data = {}
        start_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            date_str = current_date.strftime('%Y-%m-%d')
            historical_data[date_str] = {}
            
            for symbol in symbols:
                # Rastgele fiyat hareketleri simüle et
                if i == 0:
                    # Başlangıç fiyatları
                    base_prices = {
                        'BTCUSDT': 50000,
                        'ETHUSDT': 3000,
                        'ADAUSDT': 0.5,
                        'SOLUSDT': 100
                    }
                    base_price = base_prices.get(symbol.replace('BINANCE:', ''), 100)
                    price = base_price
                else:
                    # Önceki günün fiyatını al
                    prev_date = (start_date + timedelta(days=i-1)).strftime('%Y-%m-%d')
                    prev_data = historical_data[prev_date].get(symbol, {})
                    price = prev_data.get('close', 100)
                    
                    # Rastgele fiyat değişimi (%5 volatilite)
                    change = np.random.normal(0, 0.05)
                    price = price * (1 + change)
                    price = max(price, 0.01)  # Negatif fiyat olmasın
                
                # Teknik göstergeler simüle et
                historical_data[date_str][symbol] = {
                    'open': price * 0.99,
                    'high': price * 1.02,
                    'low': price * 0.98,
                    'close': price,
                    'volume': np.random.randint(1000000, 5000000),
                    'rsi': np.random.uniform(30, 70),
                    'macd': np.random.uniform(-10, 10),
                    'macd_signal': np.random.uniform(-8, 8)
                }
        
        return historical_data
    
    def _calculate_performance_metrics(self, portfolio_values: List[float], 
                                     trades: List[Dict], initial_capital: float) -> Dict:
        """Performans metriklerini hesapla"""
        try:
            if not portfolio_values:
                return {"error": "Portfolio values yok"}
            
            final_value = portfolio_values[-1]
            total_return = (final_value - initial_capital) / initial_capital
            
            # Returns hesapla
            returns = []
            for i in range(1, len(portfolio_values)):
                ret = (portfolio_values[i] - portfolio_values[i-1]) / portfolio_values[i-1]
                returns.append(ret)
            
            # Sharpe Ratio
            excess_returns = [r - self.config['risk_free_rate']/252 for r in returns]
            sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252) if returns and np.std(excess_returns) > 0 else 0
            
            # Maximum Drawdown
            peak = portfolio_values[0]
            max_drawdown = 0
            
            for value in portfolio_values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # Win rate
            profitable_trades = len([t for t in trades if t.get('revenue', 0) > t.get('cost', 0)])
            total_trades = len(trades)
            win_rate = profitable_trades / total_trades if total_trades > 0 else 0
            
            # Other metrics
            volatility = np.std(returns) * np.sqrt(252) if returns else 0
            avg_daily_return = np.mean(returns) * 252 if returns else 0
            
            return {
                "initial_capital": initial_capital,
                "final_value": final_value,
                "total_return": total_return,
                "total_return_percent": total_return * 100,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "max_drawdown_percent": max_drawdown * 100,
                "volatility": volatility,
                "win_rate": win_rate,
                "total_trades": total_trades,
                "profitable_trades": profitable_trades,
                "avg_daily_return": avg_daily_return,
                "calmar_ratio": total_return / max_drawdown if max_drawdown > 0 else 0,
                "sortino_ratio": self._calculate_sortino_ratio(returns),
                "portfolio_values": portfolio_values,
                "trades": trades[-20:]  # Son 20 trade
            }
            
        except Exception as e:
            logger.error(f"❌ Performance metrics hatası: {e}")
            return {"error": str(e)}
    
    def _calculate_sortino_ratio(self, returns: List[float]) -> float:
        """Sortino ratio hesapla"""
        if not returns:
            return 0
        
        excess_returns = [r - self.config['risk_free_rate']/252 for r in returns]
        downside_returns = [r for r in excess_returns if r < 0]
        
        if not downside_returns:
            return float('inf')
        
        downside_risk = np.std(downside_returns)
        avg_excess_return = np.mean(excess_returns)
        
        return avg_excess_return / downside_risk * np.sqrt(252) if downside_risk > 0 else 0

# Backtester Factory
class BacktesterFactory:
    @staticmethod
    def create_backtester(backtester_type="advanced", config=None):
        if backtester_type == "advanced":
            return Backtester(config)
        else:
            return Backtester(config)  # Fallback