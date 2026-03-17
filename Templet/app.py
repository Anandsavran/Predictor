import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg') # Required for headless server environments like Render
import matplotlib.pyplot as plt
from keras.models import load_model
from flask import Flask, render_template, request, send_file, redirect, url_for, session, flash, jsonify
import datetime
from openai import OpenAI
import datetime as dt
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
import os
import openai
import json
import hashlib
import secrets
plt.style.use("fivethirtyeight")

# Get the base directory (one level up from Templet folder)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, 'Static')
TEMPLATE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure Static directory exists
os.makedirs(STATIC_DIR, exist_ok=True)

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='/Static', template_folder=TEMPLATE_DIR)
app.secret_key = os.environ.get('SECRET_KEY', 'predictor-secret-key-2026-@change-in-production!')

# ---- User Database (File-Based) ----
USERS_DB_FILE = os.path.join(BASE_DIR, 'users.json')

def load_users():
    if not os.path.exists(USERS_DB_FILE):
        return {}
    with open(USERS_DB_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_DB_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def check_password(stored_hash, password):
    return stored_hash == hashlib.sha256(password.encode('utf-8')).hexdigest()

# ---- Auth Routes ----
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        users = load_users()
        # Allow login with username OR email
        user = users.get(username)
        if not user:
            # try by email
            for u in users.values():
                if u.get('email', '').lower() == username:
                    user = u
                    break
        if user and check_password(user['password_hash'], password):
            session['username'] = user['username']
            session['full_name'] = user.get('full_name', user['username'])
            session['first_name'] = user.get('full_name', user['username']).split()[0]
            flash(f"Welcome back, {session['first_name']}! 🎉", 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password. Please try again.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username  = request.form.get('username', '').strip().lower()
        email     = request.form.get('email', '').strip().lower()
        password  = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return redirect(url_for('login') + '?tab=register')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return redirect(url_for('login') + '?tab=register')

        users = load_users()
        if username in users:
            flash('Username already taken. Please choose a different one.', 'error')
            return redirect(url_for('login') + '?tab=register')

        # Check email uniqueness
        for u in users.values():
            if u.get('email', '').lower() == email:
                flash('An account with that email already exists.', 'error')
                return redirect(url_for('login') + '?tab=register')

        users[username] = {
            'username': username,
            'full_name': full_name,
            'email': email,
            'password_hash': hash_password(password)
        }
        save_users(users)
        session['username'] = username
        session['full_name'] = full_name
        session['first_name'] = full_name.split()[0] if full_name else username
        flash(f"Account created successfully! Welcome, {session['first_name']}! 🚀", 'success')
        return redirect(url_for('index'))
    return redirect(url_for('login') + '?tab=register')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# API endpoint to get current logged-in user info (for the frontend)
@app.route('/api/auth/me')
def auth_me():
    if 'username' in session:
        return jsonify({"logged_in": True, "username": session['username'], "full_name": session.get('full_name', ''), "first_name": session.get('first_name', session.get('username', ''))})
    return jsonify({"logged_in": False})

# Load the model (make sure your model is in the correct path)
model_path = os.path.join(TEMPLATE_DIR, 'stock_model.keras')
model = None
if os.path.exists(model_path):
    try:
        model = load_model(model_path)
    except Exception as e:
        print(f"Error loading model: {e}")
        model = None
else:
    print(f"Warning: Model file not found at {model_path}. Please train the model first.")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if model is None:
            return render_template('index.html', error="Model not loaded. Please ensure stock_model.keras exists in the Templet folder.")
        
        stock = request.form.get('stock')
        if not stock:
            stock = 'POWERGRID.NS'  # Default stock if none is entered
        
        # Define the start and end dates for stock data
        start = dt.datetime(2000, 1, 1)
        end = dt.datetime(2024, 10, 1)
        
        # Download stock data with error handling
        try:
            df = yf.download(stock, start=start, end=end, progress=False)
        except Exception as e:
            return render_template('index.html', error=f"Error downloading stock data: {str(e)}. Please check the ticker symbol.")
        
        # Check if data is empty
        if df.empty or len(df) == 0:
            return render_template('index.html', error=f"No data found for ticker '{stock}'. Please check the ticker symbol and try again.")
        
        # Check if required columns exist
        if 'Close' not in df.columns:
            return render_template('index.html', error=f"Invalid data format for ticker '{stock}'. Please try a different ticker.")
        
        # Descriptive Data
        data_desc = df.describe()
        
        # Exponential Moving Averages
        ema20 = df.Close.ewm(span=20, adjust=False).mean()
        ema50 = df.Close.ewm(span=50, adjust=False).mean()
        ema100 = df.Close.ewm(span=100, adjust=False).mean()
        ema200 = df.Close.ewm(span=200, adjust=False).mean()
        
        # Check minimum data requirement (need at least 200 days for proper training/testing split)
        if len(df) < 200:
            return render_template('index.html', error=f"Insufficient data for ticker '{stock}'. Need at least 200 days of data, found {len(df)} days.")
        
        # Data splitting
        data_training = pd.DataFrame(df['Close'][0:int(len(df)*0.70)])
        data_testing = pd.DataFrame(df['Close'][int(len(df)*0.70): int(len(df))])
        
        # Check if we have enough data for predictions (need at least 100 days for past data)
        if len(data_training) < 100:
            return render_template('index.html', error=f"Insufficient training data for ticker '{stock}'. Need at least 100 days of training data.")
        
        # Scaling data
        scaler = MinMaxScaler(feature_range=(0, 1))
        data_training_array = scaler.fit_transform(data_training)
        
        # Prepare data for prediction
        past_100_days = data_training.tail(100)
        final_df = pd.concat([past_100_days, data_testing], ignore_index=True)
        input_data = scaler.fit_transform(final_df)
        
        x_test, y_test = [], []
        for i in range(100, input_data.shape[0]):
            x_test.append(input_data[i - 100:i])
            y_test.append(input_data[i, 0])
        x_test, y_test = np.array(x_test), np.array(y_test)

        # Make predictions with error handling
        try:
            y_predicted = model.predict(x_test, verbose=0)
        except Exception as e:
            return render_template('index.html', error=f"Error making predictions: {str(e)}")
        
        # Inverse scaling for predictions
        scaler = scaler.scale_
        scale_factor = 1 / scaler[0]
        y_predicted = y_predicted * scale_factor
        y_test = y_test * scale_factor
        
        # Plot 1: Closing Price vs Time Chart with 20 & 50 Days EMA
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        ax1.plot(df.Close, 'y', label='Closing Price')
        ax1.plot(ema20, 'g', label='EMA 20')
        ax1.plot(ema50, 'r', label='EMA 50')
        ax1.set_title("Closing Price vs Time (20 & 50 Days EMA)")
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Price")
        ax1.legend()
        ema_chart_path = os.path.join(STATIC_DIR, 'ema_20_50.png')
        fig1.savefig(ema_chart_path)
        plt.close(fig1)
        
        # Plot 2: Closing Price vs Time Chart with 100 & 200 Days EMA
        fig2, ax2 = plt.subplots(figsize=(12, 6))
        ax2.plot(df.Close, 'y', label='Closing Price')
        ax2.plot(ema100, 'g', label='EMA 100')
        ax2.plot(ema200, 'r', label='EMA 200')
        ax2.set_title("Closing Price vs Time (100 & 200 Days EMA)")
        ax2.set_xlabel("Time")
        ax2.set_ylabel("Price")
        ax2.legend()
        ema_chart_path_100_200 = os.path.join(STATIC_DIR, 'ema_100_200.png')
        fig2.savefig(ema_chart_path_100_200)
        plt.close(fig2)
        
        # Plot 3: Prediction vs Original Trend
        fig3, ax3 = plt.subplots(figsize=(12, 6))
        ax3.plot(y_test, 'g', label="Original Price", linewidth = 1)
        ax3.plot(y_predicted, 'r', label="Predicted Price", linewidth = 1)
        ax3.set_title("Prediction vs Original Trend")
        ax3.set_xlabel("Time")
        ax3.set_ylabel("Price")
        ax3.legend()
        prediction_chart_path = os.path.join(STATIC_DIR, 'stock_prediction.png')
        fig3.savefig(prediction_chart_path)
        plt.close(fig3)
        
        # Save dataset as CSV
        csv_file_path = os.path.join(STATIC_DIR, f'{stock}_dataset.csv')
        df.to_csv(csv_file_path)

        # Return the rendered template with charts and dataset
        return render_template('index.html', 
                               plot_path_ema_20_50='ema_20_50.png', 
                               plot_path_ema_100_200='ema_100_200.png', 
                               plot_path_prediction='stock_prediction.png', 
                               data_desc=data_desc.to_html(classes='table table-bordered'),
                               dataset_link=f'{stock}_dataset.csv')

    return render_template('index.html')

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(STATIC_DIR, filename)
    return send_file(file_path, as_attachment=True)

# --- AI Chatbot API Endpoints ---
@app.route('/api/chatbot/top-gainers')
def get_top_gainers():
    # In a full implementation, this would query a real model/database
    import random
    data = [
        {"symbol": "RELIANCE", "prediction": round(random.uniform(0.5, 2.5), 2), "trend": "up"},
        {"symbol": "TCS", "prediction": round(random.uniform(0.1, 1.5), 2), "trend": "up"},
        {"symbol": "INFY", "prediction": round(random.uniform(0.5, 1.8), 2), "trend": "up"},
        {"symbol": "HDFCBANK", "prediction": round(random.uniform(-1.5, -0.1), 2), "trend": "down"},
        {"symbol": "ICICIBANK", "prediction": round(random.uniform(0.2, 1.2), 2), "trend": "up"},
        {"symbol": "SBIN", "prediction": round(random.uniform(0.5, 1.9), 2), "trend": "up"},
    ]
    return {"status": "success", "data": data}

@app.route('/api/chatbot/commodities')
def get_commodities():
    import random
    data = [
        {"symbol": "Gold", "prediction": round(random.uniform(0.1, 1.5), 2), "trend": "up"},
        {"symbol": "Silver", "prediction": round(random.uniform(1.0, 3.5), 2), "trend": "up"},
        {"symbol": "Copper", "prediction": round(random.uniform(-1.0, 0.5), 2), "trend": "down"},
    ]
    return {"status": "success", "data": data}

@app.route('/api/chatbot/crypto')
def get_crypto():
    import random
    data = [
        {"symbol": "Bitcoin (BTC)", "prediction": round(random.uniform(1.5, 5.5), 2), "trend": "up"},
        {"symbol": "Ethereum (ETH)", "prediction": round(random.uniform(1.0, 4.5), 2), "trend": "up"},
    ]
    return {"status": "success", "data": data}

@app.route('/api/chatbot/predict/<symbol>')
def predict_future(symbol):
    import random
    
    symbol_ns = symbol.upper() + ".NS" if not symbol.upper().endswith(".NS") else symbol.upper()
    try:
        ticker = yf.Ticker(symbol_ns)
        hist = ticker.history(period="6mo")
        if not hist.empty:
            df = hist
        else:
            ticker = yf.Ticker(symbol.upper())
            hist = ticker.history(period="6mo")
            if not hist.empty:
                df = hist
            else:
                return handle_openai_fallback(symbol)
                
    except Exception:
        return handle_openai_fallback(symbol)
        
    current_price = df['Close'].iloc[-1]
    current_price = round(float(current_price), 2)
    
    # 1. Calculate 50-day Moving Average
    df['MA50'] = df['Close'].rolling(window=50).mean()
    current_ma = df['MA50'].iloc[-1]
    
    # 2. Calculate 14-day RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    current_rsi = df['RSI'].iloc[-1]
    
    # 3. Generate Smart AI Trading Signal (Rules-based)
    signal = "HOLD"
    if current_rsi < 30 and current_price > current_ma:
        signal = "STRONG BUY"
    elif current_rsi < 30:
        signal = "BUY"
    elif current_rsi > 70 and current_price < current_ma:
        signal = "STRONG SELL"
    elif current_rsi > 70:
        signal = "SELL"
    elif current_price > current_ma:
        signal = "BUY (Bullish M.A.)"
    else:
        signal = "SELL (Bearish M.A.)"
        
    base_pred_pct = random.uniform(0.5, 2.5)
    if "SELL" in signal:
        base_pred_pct = -base_pred_pct  # reflect bearish trend in short-term predictions
    
    data = {
        "type": "stock",
        "symbol": symbol.upper(),
        "current_price": current_price,
        "signal": signal,
        "rsi": round(float(current_rsi), 1) if not np.isnan(current_rsi) else "N/A",
        "ma": round(float(current_ma), 2) if not np.isnan(current_ma) else "N/A",
        "predictions": {
            "Today": { "pct": round(base_pred_pct, 2), "price": round(current_price * (1 + base_pred_pct/100), 2) },
            "1 Week": { "pct": round(base_pred_pct * 2.5, 2), "price": round(current_price * (1 + (base_pred_pct*2.5)/100), 2) },
            "1 Month": { "pct": round(base_pred_pct * 5.0, 2), "price": round(current_price * (1 + (base_pred_pct*5.0)/100), 2) },
            "3 Months": { "pct": round(base_pred_pct * 12.0, 2), "price": round(current_price * (1 + (base_pred_pct*12.0)/100), 2) },
            "6 Months": { "pct": round(base_pred_pct * 20.0, 2), "price": round(current_price * (1 + (base_pred_pct*20.0)/100), 2) },
            "1 Year": { "pct": round(base_pred_pct * 40.0, 2), "price": round(current_price * (1 + (base_pred_pct*40.0)/100), 2) }
        }
    }
    return {"status": "success", "data": data}

working_key_idx = 0

def handle_openai_fallback(query):
    global working_key_idx
    
    API_KEYS_FILE = os.path.join(BASE_DIR, 'api_keys.txt')
    
    # Create an API keys file if it doesn't exist with the original key
    if not os.path.exists(API_KEYS_FILE):
        with open(API_KEYS_FILE, 'w') as f:
            f.write("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\n")
    
    # Read all keys
    with open(API_KEYS_FILE, 'r') as f:
        keys = [line.strip() for line in f if line.strip()]
        
    env_key = os.getenv("OPENAI_API_KEY")
    if env_key and env_key not in keys:
        keys.append(env_key)
        
    if not keys:
        return {
            "status": "success", 
            "data": {
                "type": "text",
                "content": f"I couldn't find a live stock ticket for '{query}'. Do you have any specific query? (No API Key configured)"
            }
        }

    # Automatically try all available keys if one is expired or hit quota limits
    for i in range(len(keys)):
        current_idx = (working_key_idx + i) % len(keys)
        api_key = keys[current_idx]
        
        try:
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful stock market assistant on Predictor.com. The user asked a generic question or entered an invalid ticker."},
                    {"role": "user", "content": query}
                ],
                max_tokens=150
            )
            # If successful, remember this working key so we don't try expired ones first next time
            working_key_idx = current_idx
            
            return {
                "status": "success", 
                "data": {
                    "type": "text", 
                    "content": response.choices[0].message.content.strip()
                }
            }
            
        except openai.AuthenticationError:
            print(f"Key at index {current_idx} expired or invalid. Automatic update to next key...")
            continue
        except openai.RateLimitError:
            print(f"Key at index {current_idx} rate limited (quota exceeded). Automatic update to next key...")
            continue
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            break
            
    # If all keys failed or no keys worked
    return {
        "status": "success", 
        "data": {
            "type": "text", 
            "content": "Sorry, I wasn't able to find that stock and all configured AI API connections are currently expired. Please update api_keys.txt with new keys."
        }
    }


if __name__ == "__main__":
    # Run the Flask app
    # Access at: http://localhost:5000 or http://127.0.0.1:5000
    # Use environment variable for debug mode (False in production)
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)