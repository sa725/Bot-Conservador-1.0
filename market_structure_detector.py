import pandas as pd
from datetime import datetime, timedelta
import requests

class MarketStructureDetector:
    def __init__(self, detection_type='filtered'):
        self.detection_type = detection_type
    
    def get_historical_data(self):
        url = "https://api.bybit.com/v5/market/kline"
        end_time = datetime.now()
        start_time = end_time - timedelta(days=15)
        
        params = {
            "category": "spot",
            "symbol": "MAVIAUSDT",
            "interval": "5",
            "start": int(start_time.timestamp() * 1000),
            "end": int(end_time.timestamp() * 1000),
            "limit": 4320
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        df = pd.DataFrame(data['result']['list'])
        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover']
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(float), unit='ms')
        
        for col in ['open', 'high', 'low', 'close']:
            df[col] = df[col].astype(float)
        
        return df

    def pivot_high(self, df, i, length):
        if i < length or i >= len(df) - length:
            return False
            
        high = df['high'].iloc[i]
        return (high > df['high'].iloc[i + 1] and 
                high > df['high'].iloc[i - 1] and
                high > df['high'].iloc[i + 2] and 
                high > df['high'].iloc[i - 2] and
                high > df['high'].iloc[i + 3] and 
                high > df['high'].iloc[i - 3])

    def pivot_low(self, df, i, length):
        if i < length or i >= len(df) - length:
            return False
            
        low = df['low'].iloc[i]
        return (low < df['low'].iloc[i + 1] and 
                low < df['low'].iloc[i - 1] and
                low < df['low'].iloc[i + 2] and 
                low < df['low'].iloc[i - 2] and
                low < df['low'].iloc[i + 3] and 
                low < df['low'].iloc[i - 3])

    def detect_structures(self, df):
        if self.detection_type == 'filtered':
            return self._detect_filtered(df)
        else:
            return self._detect_original(df)

    def _detect_filtered(self, df):
        structures = []
        df = df.copy()
        df = df.iloc[::-1]
        
        last_high = None
        last_high_time = None
        last_low = None
        last_low_time = None
        
        min_movement = 0.002
        
        for i in range(13, len(df)-3):
            if self.pivot_high(df, i, 5) and df['close'].iloc[i+1] < df['high'].iloc[i]:
                current_high = df['high'].iloc[i]
                current_time = df['timestamp'].iloc[i]
                
                if last_high is not None:
                    price_change = abs(current_high - last_high) / last_high
                    if price_change > min_movement:
                        for j in range(i, min(i + 20, len(df))):
                            if df['close'].iloc[j] > last_high:
                                valid_structure = True
                                for k in range(i-1, j):
                                    if df['close'].iloc[k] > last_high:
                                        valid_structure = False
                                        break
                                
                                if valid_structure:
                                    structures.append({
                                        'time_start': last_high_time,
                                        'time_end': df['timestamp'].iloc[j],
                                        'price_start': last_high,
                                        'price_end': last_high,
                                        'type': 'BOS',
                                        'direction': 'LONG',
                                        'structure_type': 'internal'
                                    })
                                break
                
                last_high = current_high
                last_high_time = current_time
                
            if self.pivot_low(df, i, 5) and df['close'].iloc[i+1] > df['low'].iloc[i]:
                current_low = df['low'].iloc[i]
                current_time = df['timestamp'].iloc[i]
                
                if last_low is not None:
                    price_change = abs(current_low - last_low) / last_low
                    if price_change > min_movement:
                        for j in range(i, min(i + 20, len(df))):
                            if df['close'].iloc[j] < last_low:
                                valid_structure = True
                                for k in range(i-1, j):
                                    if df['close'].iloc[k] < last_low:
                                        valid_structure = False
                                        break
                                
                                if valid_structure:
                                    structures.append({
                                        'time_start': last_low_time,
                                        'time_end': df['timestamp'].iloc[j],
                                        'price_start': last_low,
                                        'price_end': last_low,
                                        'type': 'BOS',
                                        'direction': 'SHORT',
                                        'structure_type': 'internal'
                                    })
                                break
                
                last_low = current_low
                last_low_time = current_time
        
        return pd.DataFrame(structures)

    def _detect_original(self, df):
        # Aquí implementaremos la versión que coincide exactamente con TradingView
        return self._detect_filtered(df)

