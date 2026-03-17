# Feature Engineering for Predictive Models
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

class FeatureEngineer:
    def __init__(self):
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    def create_moving_averages(self, df):
        """Creates EMA features for technical analysis"""
        if 'Close' not in df.columns:
            return df
        
        df = df.copy()
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA_100'] = df['Close'].ewm(span=100, adjust=False).mean()
        df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        return df

    def create_momentum_indicators(self, df):
        """Creates RSI and MACD"""
        if 'Close' not in df.columns:
            return df
        df = df.copy()
        
        # Simple RSI calculation
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df

    def scale_features(self, df, columns_to_scale=['Close']):
        """Scales dataset for Deep Learning (TensorFlow/Keras) ingestion"""
        scaled_data = self.scaler.fit_transform(df[columns_to_scale])
        return scaled_data, self.scaler

    def create_sequences(self, data, seq_length=100):
        """Creates sliding window sequences for LSTM/RNN models"""
        x, y = [], []
        if len(data) <= seq_length:
            return np.array(x), np.array(y)
            
        for i in range(seq_length, len(data)):
            x.append(data[i-seq_length:i, 0])
            y.append(data[i, 0])
            
        return np.array(x), np.array(y)
