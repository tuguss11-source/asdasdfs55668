import requests
import sys
import os

# Python path'ini ayarla
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class FearGreedClient:
    def __init__(self):
        self.api_url = "https://api.alternative.me/fng/"
    
    def get_index(self):
        """Fear & Greed Index verisini çek"""
        try:
            response = requests.get(self.api_url, timeout=10)
            data = response.json()
            return data['data'][0]
        except:
            return {"value": 50, "value_classification": "Neutral"}