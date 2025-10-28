# auto_trader.py - YENİ DOSYA
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sqlite3
import requests
import hmac
import hashlib
import urllib.parse

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoTrader:
    def __init__(self, config=None):
        self.config = config or {
            "paper_trading": True,
            "max_positions": 5,
            "daily_loss_limit": -0.1,  # -%10
            "min_signal_strength": 7,
            "max_position_size": 0.1,  # %10 portföy
            "default_leverage": "3x"
        }
        
        # Trading durumu
        self.is_running = False
        self.active_positions = []
        self.trade_history = []
        self.daily_pnl = 0
        
        # Exchange bağlantıları
        self.exchanges = {}
        self.init_exchanges()
        
        # Risk yöneticisi
        self.risk_manager = None
        
        logger.info("🤖 Auto Trader Başlatıldı")
    
    def init_exchanges(self):
        """Exchange bağlantılarını başlat"""
        try:
            # Binance entegrasyonu
            self.exchanges['binance'] = BinanceExchange()
            logger.info("✅ Binance exchange bağlantısı hazır")
        except Exception as e:
            logger.error(f"❌ Exchange bağlantı hatası: {e}")
    
    def execute_trade(self, signal_data: Dict) -> Dict:
        """Trade yürüt - ana fonksiyon"""
        try:
            symbol = signal_data.get('symbol', '')
            signal_type = signal_data.get('signal', {}).get('sinyal', 'BEKLE')
            
            if signal_type == 'BEKLE':
                return {"status": "skipped", "reason": "BEKLE sinyali"}
            
            # Risk kontrolü
            risk_check = self.check_trade_risk(signal_data)
            if not risk_check.get('approved', False):
                return {"status": "rejected", "reason": risk_check.get('reason', 'Risk limiti')}
            
            # Paper trading mi gerçek trading mi?
            if self.config['paper_trading']:
                return self.execute_paper_trade(signal_data)
            else:
                return self.execute_real_trade(signal_data)
                
        except Exception as e:
            logger.error(f"❌ Trade execution hatası: {e}")
            return {"status": "error", "reason": str(e)}
    
    def execute_paper_trade(self, signal_data: Dict) -> Dict:
        """Paper trade yürüt"""
        try:
            symbol = signal_data.get('symbol', '')
            signal = signal_data.get('signal', {})
            signal_type = signal.get('sinyal', 'BEKLE')
            
            # Paper trade detayları
            trade_details = {
                'trade_id': f"paper_{int(time.time())}",
                'symbol': symbol,
                'action': signal_type,
                'entry_price': signal.get('giris_fiyati', 0),
                'quantity': signal.get('pozisyon_buyuklugu', 0),
                'timestamp': datetime.now().isoformat(),
                'status': 'filled',
                'paper_trading': True,
                'risk_amount': signal.get('risk_miktari', 0),
                'leverage': signal.get('kaldıraç', '1x')
            }
            
            # Paper position'a ekle
            self.active_positions.append(trade_details)
            
            logger.info(f"📝 Paper Trade: {symbol} {signal_type} - ${trade_details['entry_price']:,.2f}")
            
            return {
                "status": "success",
                "trade_id": trade_details['trade_id'],
                "paper_trading": True,
                "details": trade_details
            }
            
        except Exception as e:
            logger.error(f"❌ Paper trade hatası: {e}")
            return {"status": "error", "reason": str(e)}
    
    def execute_real_trade(self, signal_data: Dict) -> Dict:
        """Gerçek trade yürüt"""
        try:
            symbol = signal_data.get('symbol', '')
            signal = signal_data.get('signal', {})
            signal_type = signal.get('sinyal', 'BEKLE')
            
            # Exchange'e göre sembol formatını düzenle
            exchange_symbol = self.format_symbol_for_exchange(symbol, 'binance')
            
            # Order parametreleri
            order_params = {
                'symbol': exchange_symbol,
                'side': 'BUY' if signal_type == 'AL' else 'SELL',
                'quantity': signal.get('pozisyon_buyuklugu', 0),
                'price': signal.get('giris_fiyati', 0),
                'leverage': signal.get('kaldıraç', '1x')
            }
            
            # Binance'e order gönder
            exchange = self.exchanges.get('binance')
            if exchange:
                order_result = exchange.place_order(order_params)
                
                if order_result.get('status') == 'FILLED':
                    # Trade history'e ekle
                    trade_record = {
                        'trade_id': order_result.get('orderId', ''),
                        'symbol': symbol,
                        'action': signal_type,
                        'entry_price': order_result.get('price', 0),
                        'quantity': order_result.get('executedQty', 0),
                        'timestamp': datetime.now().isoformat(),
                        'status': 'filled',
                        'paper_trading': False,
                        'exchange': 'binance'
                    }
                    
                    self.trade_history.append(trade_record)
                    self.active_positions.append(trade_record)
                    
                    logger.info(f"🎯 Real Trade: {symbol} {signal_type} - ${order_result.get('price', 0):,.2f}")
                    
                    return {
                        "status": "success",
                        "trade_id": trade_record['trade_id'],
                        "paper_trading": False,
                        "exchange": "binance",
                        "details": trade_record
                    }
                else:
                    return {
                        "status": "exchange_error",
                        "reason": order_result.get('msg', 'Exchange hatası')
                    }
            else:
                return {"status": "error", "reason": "Exchange bağlantısı yok"}
                
        except Exception as e:
            logger.error(f"❌ Real trade hatası: {e}")
            return {"status": "error", "reason": str(e)}
    
    def check_trade_risk(self, signal_data: Dict) -> Dict:
        """Trade risk kontrolü"""
        try:
            symbol = signal_data.get('symbol', '')
            signal = signal_data.get('signal', {})
            
            # 1. Sinyal gücü kontrolü
            signal_strength = signal.get('güç', 0)
            if signal_strength < self.config['min_signal_strength']:
                return {"approved": False, "reason": "Sinyal gücü yetersiz"}
            
            # 2. Pozisyon sayısı kontrolü
            if len(self.active_positions) >= self.config['max_positions']:
                return {"approved": False, "reason": "Maksimum pozisyon sayısı aşıldı"}
            
            # 3. Günlük kayıp limiti kontrolü
            if self.daily_pnl <= self.config['daily_loss_limit']:
                return {"approved": False, "reason": "Günlük kayıp limiti aşıldı"}
            
            # 4. Aynı sembolde açık pozisyon kontrolü
            existing_position = any(pos['symbol'] == symbol for pos in self.active_positions)
            if existing_position:
                return {"approved": False, "reason": "Aynı sembolde açık pozisyon var"}
            
            # 5. Position size kontrolü
            position_size = signal.get('pozisyon_buyuklugu', 0)
            position_value = position_size * signal.get('mevcut_fiyat', 0)
            if position_value > self.config['max_position_size']:
                return {"approved": False, "reason": "Pozisyon büyüklüğü limiti aşıldı"}
            
            return {"approved": True, "reason": "Risk kontrolü başarılı"}
            
        except Exception as e:
            logger.error(f"❌ Risk kontrol hatası: {e}")
            return {"approved": False, "reason": "Risk kontrol hatası"}
    
    def format_symbol_for_exchange(self, symbol: str, exchange: str) -> str:
        """Sembol formatını exchange'e göre düzenle"""
        if exchange == 'binance':
            # BINANCE:BTCUSDT -> BTCUSDT
            return symbol.replace('BINANCE:', '')
        return symbol
    
    def close_position(self, symbol: str, reason: str = "manual") -> Dict:
        """Pozisyonu kapat"""
        try:
            # Aktif pozisyonu bul
            position = next((pos for pos in self.active_positions if pos['symbol'] == symbol), None)
            
            if not position:
                return {"status": "error", "reason": "Pozisyon bulunamadı"}
            
            # Paper trading ise
            if position.get('paper_trading', True):
                # Simüle exit price (entry price ± %2)
                import random
                price_change = random.uniform(-0.02, 0.02)
                exit_price = position['entry_price'] * (1 + price_change)
                
                # P&L hesapla
                pnl = (exit_price - position['entry_price']) * position['quantity']
                if position['action'] == 'SAT':
                    pnl = -pnl  # Short pozisyon için tersi
                
                self.daily_pnl += pnl
                
                # Pozisyonu kapat
                self.active_positions.remove(position)
                
                # Trade history'i güncelle
                position['exit_price'] = exit_price
                position['pnl'] = pnl
                position['exit_reason'] = reason
                position['exit_timestamp'] = datetime.now().isoformat()
                
                logger.info(f"📝 Paper Position Closed: {symbol} - P&L: ${pnl:,.2f}")
                
                return {
                    "status": "success",
                    "pnl": pnl,
                    "exit_price": exit_price,
                    "paper_trading": True
                }
            else:
                # Gerçek pozisyon kapatma
                exchange = self.exchanges.get('binance')
                if exchange:
                    # Tersi yönde order oluştur
                    close_side = 'SELL' if position['action'] == 'AL' else 'BUY'
                    close_result = exchange.place_order({
                        'symbol': self.format_symbol_for_exchange(symbol, 'binance'),
                        'side': close_side,
                        'quantity': position['quantity'],
                        'price': 0,  # Market price
                        'type': 'MARKET'
                    })
                    
                    if close_result.get('status') == 'FILLED':
                        # P&L hesapla
                        exit_price = close_result.get('price', 0)
                        pnl = (exit_price - position['entry_price']) * position['quantity']
                        if position['action'] == 'SAT':
                            pnl = -pnl
                        
                        self.daily_pnl += pnl
                        self.active_positions.remove(position)
                        
                        logger.info(f"🎯 Real Position Closed: {symbol} - P&L: ${pnl:,.2f}")
                        
                        return {
                            "status": "success",
                            "pnl": pnl,
                            "exit_price": exit_price,
                            "paper_trading": False
                        }
                    else:
                        return {"status": "error", "reason": "Exchange kapatma hatası"}
                else:
                    return {"status": "error", "reason": "Exchange bağlantısı yok"}
                    
        except Exception as e:
            logger.error(f"❌ Position close hatası: {e}")
            return {"status": "error", "reason": str(e)}
    
    def get_portfolio_status(self) -> Dict:
        """Portföy durumunu getir"""
        total_value = 0
        total_pnl = 0
        
        for position in self.active_positions:
            current_value = position['quantity'] * position.get('current_price', position['entry_price'])
            total_value += current_value
            
            position_pnl = (position.get('current_price', position['entry_price']) - position['entry_price']) * position['quantity']
            if position['action'] == 'SAT':
                position_pnl = -position_pnl
            total_pnl += position_pnl
        
        return {
            'active_positions': len(self.active_positions),
            'total_value': total_value,
            'total_pnl': total_pnl,
            'daily_pnl': self.daily_pnl,
            'max_positions': self.config['max_positions']
        }
    
    def reset_daily_pnl(self):
        """Günlük P&L'ı sıfırla (gece yarısı çağrılmalı)"""
        self.daily_pnl = 0
        logger.info("🔄 Günlük P&L sıfırlandı")

class BinanceExchange:
    """Binance exchange entegrasyonu"""
    
    def __init__(self, api_key="", api_secret="", testnet=True):
        self.base_url = "https://testnet.binance.vision" if testnet else "https://api.binance.com"
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({'X-MBX-APIKEY': api_key})
    
    def place_order(self, order_params: Dict) -> Dict:
        """Order yerleştir"""
        try:
            # Testnet için simüle response
            if not self.api_key:
                return self._simulate_order(order_params)
            
            # Gerçek Binance API call
            endpoint = "/api/v3/order"
            params = {
                'symbol': order_params['symbol'],
                'side': order_params['side'],
                'type': 'LIMIT',
                'quantity': order_params['quantity'],
                'price': order_params['price'],
                'timeInForce': 'GTC'
            }
            
            # Signature ekle
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
            
            response = self.session.post(self.base_url + endpoint, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "msg": response.text}
                
        except Exception as e:
            logger.error(f"❌ Binance order hatası: {e}")
            return {"status": "error", "msg": str(e)}
    
    def _simulate_order(self, order_params: Dict) -> Dict:
        """Test için simüle order"""
        time.sleep(0.5)  # Simüle latency
        
        return {
            "orderId": int(time.time()),
            "symbol": order_params['symbol'],
            "status": "FILLED",
            "clientOrderId": f"sim_{int(time.time())}",
            "price": order_params['price'],
            "origQty": str(order_params['quantity']),
            "executedQty": str(order_params['quantity']),
            "cummulativeQuoteQty": str(float(order_params['price']) * float(order_params['quantity'])),
            "type": "LIMIT",
            "side": order_params['side'],
            "transactTime": int(time.time() * 1000)
        }
    
    def _generate_signature(self, params: Dict) -> str:
        """API signature oluştur"""
        query_string = urllib.parse.urlencode(params)
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def get_account_info(self) -> Dict:
        """Hesap bilgilerini getir"""
        try:
            endpoint = "/api/v3/account"
            params = {'timestamp': int(time.time() * 1000)}
            params['signature'] = self._generate_signature(params)
            
            response = self.session.get(self.base_url + endpoint, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.text}
        except Exception as e:
            return {"error": str(e)}

# Trade Manager Factory
class TradeManagerFactory:
    @staticmethod
    def create_trader(trader_type="auto", config=None):
        if trader_type == "auto":
            return AutoTrader(config)
        else:
            return AutoTrader(config)  # Fallback