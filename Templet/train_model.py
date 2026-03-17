import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout
import os

def train_basic_model():
    print("Starting basic model training...")
    ticker = 'POWERGRID.NS'  # Using a standard ticker for training
    start_date = '2010-01-01'
    end_date = '2023-01-01'
    
    # Download data
    print(f"Downloading data for {ticker}...")
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    
    if df.empty:
        print("Error: No data downloaded.")
        return
    
    print(f"Data columns: {df.columns}")
    # Handle possible MultiIndex or simple Index
    if 'Close' in df.columns:
        data = df[['Close']]
    else:
        # Try to find 'Close' in MultiIndex levels
        try:
            data = df.xs('Close', axis=1, level=0)
            if isinstance(data, pd.Series):
                data = data.to_frame()
        except:
            print("Error: Could not find 'Close' column.")
            return

    print(f"Data shape after selection: {data.shape}")
    dataset = data.values
    
    # Scale data
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(dataset)
    
    # Create sequences
    x_train, y_train = [], []
    prediction_days = 100
    
    for x in range(prediction_days, len(scaled_data)):
        x_train.append(scaled_data[x-prediction_days:x, 0])
        y_train.append(scaled_data[x, 0])
    
    x_train, y_train = np.array(x_train), np.array(y_train)
    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))
    
    # Build Model
    print("Building LSTM model...")
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1], 1)))
    model.add(Dropout(0.2))
    model.add(LSTM(units=50, return_sequences=False))
    model.add(Dropout(0.2))
    model.add(Dense(units=1))
    
    model.compile(optimizer='adam', loss='mean_squared_error')
    
    # Train (briefly for initialization)
    print("Training model (this may take a minute)...")
    model.fit(x_train, y_train, epochs=2, batch_size=32, verbose=1)
    
    # Save Model
    model_path = 'stock_model.keras'
    model.save(model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train_basic_model()
