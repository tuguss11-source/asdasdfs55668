# multi_exchange.py - YENİ DOSYA
import time
import hmac
import hashlib
import urllib.parse
import requests
from typing import Dict, List, Optional
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiExchangeManager:
    def __init__(self, config=None):
        self.config = config or {
            "exchanges": {
                "binance": {"enabled": True, "testnet": True},
                "kucoin": {"enabled": False},
                "bybit": {"enabled": False}
            }
        }
        
        self.exchanges = {}
        self.active_exchanges = []
        self.init_exchanges()
        
        logger.info("🌐 Multi-Exchange Manager Başlatıldı")
    
    def init_exchanges(self):
        """Exchange'leri başlat"""
        try:
            for exchange_name, exchange_config in self.config["exchanges"].items():
                if exchange_config.get("enabled", False):
                    if exchange_name == "binance":
                        self.exchanges[exchange_name] = BinanceExchange(exchange_config)
                        self.active_exchanges.append(exchange_name)
                        logger.info(f"✅ {exchange_name} exchange bağlantısı hazır")
                    # Diğer exchange'ler eklenebilir
                    
        except Exception as e:
            logger.error(f"❌ Exchange initialization hatası: {e}")
    
    def get_balance(self, exchange: str = "binance") -> Dict:
        """Bakiye bilgisini getir"""
        try:
            if exchange in self.exchanges:
                return self.exchanges[exchange].get_balance()
            else:
                return {"error": f"Exchange bulunamadı: {exchange}"}
        except Exception as e:
            logger.error(f"❌ Balance check hatası: {e}")
            return {"error": str(e)}
    
    def place_order(self, exchange: str, order_params: Dict) -> Dict:
        """Order yerleştir"""
        try:
            if exchange in self.exchanges:
                return self.exchanges[exchange].place_order(order_params)
            else:
                return {"error": f"Exchange bulunamadı: {exchange}"}
        except Exception as e:
            logger.error(f"❌ Order placement hatası: {e}")
            return {"error": str(e)}
    
    def get_ticker(self, exchange: str, symbol: str) -> Dict:
        """Ticker bilgisini getir"""
        try:
            if exchange in self.exchanges:
                return self.exchanges[exchange].get_ticker(symbol)
            else:
                return {"error": f"Exchange bulunamadı: {exchange}"}
        except Exception as e:
            logger.error(f"❌ Ticker hatası: {e}")
            return {"error": str(e)}
    
    def get_all_balances(self) -> Dict:
        """Tüm exchange'lerin bakiyelerini getir"""
        balances = {}
        total_balance = 0
        
        for exchange_name in self.active_exchanges:
            balance = self.get_balance(exchange_name)
            balances[exchange_name] = balance
            if 'total' in balance:
                total_balance += balance['total']
        
        balances['total'] = total_balance
        return balances

class BinanceExchange:
    """Binance exchange entegrasyonu"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.testnet = self.config.get("testnet", True)
        self.api_key = self.config.get("api_key", "")
        self.api_secret = self.config.get("api_secret", "")
        
        self.base_url = "https://testnet.binance.vision" if self.testnet else "https://api.binance.com"
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({'X-MBX-APIKEY': self.api_key})
    
    def get_balance(self) -> Dict:
        """Bakiye bilgisini getir"""
        try:
            if not self.api_key:
                # Simüle bakiye
                return {
                    "total": 1000,
                    "available": 800,
                    "in_orders": 200,
                    "currencies": {
                        "USDT": {"total": 1000, "available": 800},
                        "BTC": {"total": 0.02, "available": 0.02}
                    }
                }
            
            endpoint = "/api/v3/account"
            params = {'timestamp': int(time.time() * 1000)}
            params['signature'] = self._generate_signature(params)
            
            response = self.session.get(self.base_url + endpoint, params=params)
            
            if response.status_code == 200:
                data = response.json()
                balances = {}
                total_balance = 0
                
                for balance in data['balances']:
                    asset = balance['asset']
                    free = float(balance['free'])
                    locked = float(balance['locked'])
                    total = free + locked
                    
                    if total > 0:
                        balances[asset] = {
                            "free": free,
                            "locked": locked,
                            "total": total
                        }
                        # USDT cinsinden değer hesapla (basit)
                        if asset == 'USDT':
                            total_balance += total
                        elif asset == 'BTC':
                            total_balance += total * 50000  # Örnek BTC fiyatı
                
                return {
                    "total": total_balance,
                    "available": total_balance * 0.8,  # Örnek
                    "in_orders": total_balance * 0.2,  # Örnek
                    "currencies": balances
                }
            else:
                return {"error": response.text}
                
        except Exception as e:
            logger.error(f"❌ Binance balance hatası: {e}")
            return {"error": str(e)}
    
    def place_order(self, order_params: Dict) -> Dict:
        """Order yerleştir"""
        try:
            # Testnet için simüle order
            if not self.api_key:
                return self._simulate_order(order_params)
            
            endpoint = "/api/v3/order"
            params = {
                'symbol': order_params['symbol'],
                'side': order_params['side'],
                'type': order_params.get('type', 'LIMIT'),
                'quantity': order_params['quantity'],
                'timestamp': int(time.time() * 1000)
            }
            
            if params['type'] == 'LIMIT':
                params['price'] = order_params['price']
                params['timeInForce'] = 'GTC'
            
            params['signature'] = self._generate_signature(params)
            
            response = self.session.post(self.base_url + endpoint, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.text}
                
        except Exception as e:
            logger.error(f"❌ Binance order hatası: {e}")
            return {"error": str(e)}
    
    def get_ticker(self, symbol: str) -> Dict:
        """Ticker bilgisini getir"""
        try:
            endpoint = "/api/v3/ticker/price"
            params = {'symbol': symbol}
            
            response = self.session.get(self.base_url + endpoint, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.text}
                
        except Exception as e:
            logger.error(f"❌ Binance ticker hatası: {e}")
            return {"error": str(e)}
    
    def _simulate_order(self, order_params: Dict) -> Dict:
        """Test için simüle order"""
        time.sleep(0.5)
        
        return {
            "orderId": int(time.time()),
            "symbol": order_params['symbol'],
            "status": "FILLED",
            "clientOrderId": f"sim_{int(time.time())}",
            "price": order_params.get('price', 0),
            "origQty": str(order_params['quantity']),
            "executedQty": str(order_params['quantity']),
            "cummulativeQuoteQty": str(float(order_params.get('price', 0)) * float(order_params['quantity'])),
            "type": order_params.get('type', 'LIMIT'),
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

# Exchange Factory
class ExchangeFactory:
    @staticmethod
    def create_exchange_manager(manager_type="multi", config=None):
        if manager_type == "multi":
            return MultiExchangeManager(config)
        else:
            return MultiExchangeManager(config)  # Fallback