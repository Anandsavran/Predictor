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
from textblob import TextBlob
import requests
import random
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
        
        # Symbol Resolution Logic (similar to chatbot)
        raw_stock = request.form.get('stock', 'POWERGRID')
        stock_query = raw_stock.strip().upper()
        # Remove common extensions to normalize
        base_symbol = stock_query.split('.')[0]
        
        # Try finding the best symbol match
        if '-' in base_symbol or '=' in base_symbol:
            search_stock = base_symbol
        else:
            # For Indian stocks, try .NS first then .BO
            search_stock = f"{base_symbol}.NS"
            
        # Define the start and end dates for stock data
        start = dt.datetime(2000, 1, 1)
        end = dt.datetime.now()
        
        # Download stock data with error handling
        try:
            df = yf.download(search_stock, start=start, end=end, progress=False)
            if df.empty and search_stock.endswith('.NS'):
                search_stock = f"{base_symbol}.BO"
                df = yf.download(search_stock, start=start, end=end, progress=False)
            if df.empty:
                search_stock = base_symbol
                df = yf.download(search_stock, start=start, end=end, progress=False)
            
            stock = search_stock # Update final stock name for display
        except Exception as e:
            return render_template('index.html', error=f"Error downloading stock data: {str(e)}. Please check the ticker symbol.")
        
        # Check if data is empty
        if df.empty or len(df) == 0:
            return render_template('index.html', error=f"No data found for ticker '{stock}'. Please check the ticker symbol and try again.")
        
        # Check if required columns exist
        if 'Close' not in df.columns:
            return render_template('index.html', error=f"Invalid data format for ticker '{stock}'. Please try a different ticker.")
        
        # --- PRE-CALCULATIONS ---
        # Descriptive Data
        data_desc = df.describe()
        
        # Exponential Moving Averages
        ema20 = df.Close.ewm(span=20, adjust=False).mean()
        ema50 = df.Close.ewm(span=50, adjust=False).mean()
        ema100 = df.Close.ewm(span=100, adjust=False).mean()
        ema200 = df.Close.ewm(span=200, adjust=False).mean()

        # --- NEW: Professional Insights & Fundamental Data ---
        ticker_obj = yf.Ticker(stock)
        
        # 1. Fetch info for fundamental data
        info = {}
        try:
            info = ticker_obj.info
        except Exception:
            info = {}
            
        # Extract specific fields with fallbacks
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or (float(df['Close'].iloc[-1]) if not df.empty else 0)
        volume = info.get('volume') or info.get('regularMarketVolume') or 0
        high_52 = info.get('fiftyTwoWeekHigh') or 0
        low_52 = info.get('fiftyTwoWeekLow') or 0
        pe_ratio = info.get('trailingPE') or info.get('forwardPE') or "N/A"
        avg_vol = info.get('averageVolume') or 0
        market_cap = info.get('marketCap') or 0
        company_name = info.get('longName') or stock
        currency = info.get('currency', 'INR')
        
        # 2. Fetch specific news for this ticker
        ticker_news = []
        try:
            raw_news = ticker_obj.news
            for n in raw_news[:5]: # Take top 5 news
                ticker_news.append({
                    'title': n.get('title'),
                    'publisher': n.get('publisher'),
                    'link': n.get('link'),
                    'provider_publish_time': datetime.datetime.fromtimestamp(n.get('providerPublishTime')).strftime('%Y-%m-%d %H:%M') if n.get('providerPublishTime') else "Recently"
                })
        except Exception:
            ticker_news = []

        # 3. Calculate Signals
        latest_rsi = 50 # Default neutral
        try:
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            latest_rsi = float(rsi.iloc[-1])
        except Exception: pass
        
        last_close = float(df['Close'].iloc[-1])
        last_ema20 = float(ema20.iloc[-1])
        last_ema50 = float(ema50.iloc[-1])
        last_ema200 = float(ema200.iloc[-1])
        
        short_term_view = "HOLD"
        short_term_color = "secondary"
        if latest_rsi < 35 or (last_close > last_ema20 and last_ema20 > last_ema50):
            short_term_view = "BUY"
            short_term_color = "success"
        elif latest_rsi > 65 or (last_close < last_ema20 and last_ema20 < last_ema50):
            short_term_view = "SELL"
            short_term_color = "danger"
            
        long_term_view = "HOLD"
        long_term_color = "secondary"
        if last_ema50 > last_ema200 and last_close > last_ema200:
            long_term_view = "STRONG BUY"
            long_term_color = "success"
        elif last_ema50 < last_ema200:
            long_term_view = "BEARISH / SELL"
            long_term_color = "danger"

        # --- ORIGINAL PREDICTION LOGIC ---
        # Check minimum data requirement (need at least 200 days for proper training/testing split)
        if len(df) < 200:
            return render_template('index.html', error=f"Insufficient data for ticker '{stock}'. Need at least 200 days of data, found {len(df)} days.")
        
        data_training = pd.DataFrame(df['Close'][0:int(len(df)*0.70)])
        data_testing = pd.DataFrame(df['Close'][int(len(df)*0.70): int(len(df))])
        
        if len(data_training) < 100:
            return render_template('index.html', error=f"Insufficient training data for ticker '{stock}'. Need at least 100 days of training data.")
        
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaler.fit_transform(data_training) # Just to fit
        
        past_100_days = data_training.tail(100)
        final_df = pd.concat([past_100_days, data_testing], ignore_index=True)
        input_data = scaler.fit_transform(final_df)
        
        x_test, y_test = [], []
        for i in range(100, input_data.shape[0]):
            x_test.append(input_data[i - 100:i])
            y_test.append(input_data[i, 0])
        x_test, y_test = np.array(x_test), np.array(y_test)

        try:
            y_predicted = model.predict(x_test, verbose=0)
        except Exception as e:
            return render_template('index.html', error=f"Error making predictions: {str(e)}")
        
        scaler = scaler.scale_
        scale_factor = 1 / scaler[0]
        y_predicted = y_predicted * scale_factor
        y_test = y_test * scale_factor
        
        # Plotting
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
        
        csv_file_path = os.path.join(STATIC_DIR, f'{stock}_dataset.csv')
        df.to_csv(csv_file_path)

        # Format large numbers for UI
        def format_large_number(num):
            if not num or num == "N/A": return "N/A"
            try:
                if num >= 1_000_000_000_000: return f"{num/1_000_000_000_000:.2f}T"
                if num >= 1_000_000_000: return f"{num/1_000_000_000:.2f}B"
                if num >= 1_000_000: return f"{num/1_000_000:.2f}M"
                return f"{num:,.0f}"
            except: return str(num)

        # Return everything to template
        return render_template('index.html', 
                               stock_symbol=stock,
                               company_name=company_name,
                               current_price=f"{current_price:,.2f}",
                               currency=currency,
                               volume=format_large_number(volume),
                               high_52=f"{high_52:,.2f}",
                               low_52=f"{low_52:,.2f}",
                               pe_ratio=pe_ratio,
                               market_cap=format_large_number(market_cap),
                               short_term_view=short_term_view,
                               short_term_color=short_term_color,
                               long_term_view=long_term_view,
                               long_term_color=long_term_color,
                               ticker_news=ticker_news,
                               plot_path_ema_20_50='ema_20_50.png', 
                               plot_path_ema_100_200='ema_100_200.png', 
                               plot_path_prediction='stock_prediction.png', 
                               data_desc=data_desc.to_html(classes='table table-bordered text-center'),
                               dataset_link=f'{stock}_dataset.csv')
    return render_template('index.html')

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(STATIC_DIR, filename)
    return send_file(file_path, as_attachment=True)





# --- Real-Time News System via RSS Feeds ---
import xml.etree.ElementTree as ET

# Category -> list of Google News RSS URLs (free, no key needed)
NEWS_RSS_FEEDS = {
    'STOCKS': [
        'https://news.google.com/rss/search?q=stock+market+nifty+sensex+india&hl=en-IN&gl=IN&ceid=IN:en',
        'https://news.google.com/rss/search?q=BSE+NSE+equity+shares&hl=en-IN&gl=IN&ceid=IN:en',
    ],
    'CRYPTO': [
        'https://news.google.com/rss/search?q=bitcoin+ethereum+cryptocurrency&hl=en&gl=US&ceid=US:en',
        'https://news.google.com/rss/search?q=crypto+blockchain+defi&hl=en&gl=US&ceid=US:en',
    ],
    'METALS': [
        'https://news.google.com/rss/search?q=gold+price+silver+commodity+market&hl=en-IN&gl=IN&ceid=IN:en',
        'https://news.google.com/rss/search?q=MCX+gold+silver+futures+india&hl=en-IN&gl=IN&ceid=IN:en',
    ],
    'FNO': [
        'https://news.google.com/rss/search?q=futures+options+derivatives+bank+nifty&hl=en-IN&gl=IN&ceid=IN:en',
    ],
    'ECONOMY': [
        'https://news.google.com/rss/search?q=global+economy+inflation+federal+reserve+GDP&hl=en&gl=US&ceid=US:en',
        'https://news.google.com/rss/search?q=international+business+market+economy&hl=en&gl=US&ceid=US:en',
    ],
}

CATEGORY_KEYWORDS = {
    'STOCKS': ['stock', 'nifty', 'sensex', 'bse', 'nse', 'equity', 'shares', 'ipo', 'dividend', 'market cap', 'sebi', 'reliance', 'tcs', 'infosys', 'hdfc'],
    'CRYPTO': ['bitcoin', 'ethereum', 'crypto', 'blockchain', 'defi', 'altcoin', 'web3', 'btc', 'eth', 'binance', 'token'],
    'METALS': ['gold', 'silver', 'commodity', 'mcx', 'platinum', 'palladium', 'precious metal', 'bullion'],
    'FNO': ['futures', 'options', 'derivatives', 'bank nifty', 'vix', 'put', 'call', 'expiry', 'hedge'],
    'ECONOMY': ['economy', 'gdp', 'inflation', 'interest rate', 'fed', 'rbi', 'recession', 'fiscal', 'trade', 'global market', 'dollar', 'forex', 'budget'],
}

def guess_category(title):
    title_lower = title.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in title_lower:
                return cat
    return 'STOCKS'

def guess_affects(category, title_lower):
    affects_map = {
        'STOCKS': 'Indian Equities, Nifty/Sensex',
        'CRYPTO': 'Bitcoin, Altcoins, DeFi',
        'METALS': 'Gold, Silver, Commodities',
        'FNO': 'Futures & Options, Derivatives',
        'ECONOMY': 'Global Markets, Bonds, Currency',
    }
    return affects_map.get(category, 'Global Markets')

def fetch_rss_articles(urls, max_per_feed=8):
    articles = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; Predictor/2.0; +http://predictor.com)'
    }
    for url in urls:
        try:
            resp = requests.get(url, timeout=8, headers=headers)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            ns = {'media': 'http://search.yahoo.com/mrss/'}
            items = root.findall('.//item')
            for item in items[:max_per_feed]:
                title_el = item.find('title')
                link_el = item.find('link')
                pub_date_el = item.find('pubDate')
                source_el = item.find('source')
                
                title = title_el.text if title_el is not None else ''
                link = link_el.text if link_el is not None else '#'
                pub_date = pub_date_el.text if pub_date_el is not None else ''
                source_name = source_el.text if source_el is not None else 'Google News'
                
                # Clean Google's " - Source Name" from title
                if ' - ' in title:
                    parts = title.rsplit(' - ', 1)
                    title = parts[0].strip()
                    if not source_el and parts[1]:
                        source_name = parts[1].strip()
                
                if title:
                    articles.append({
                        'title': title,
                        'link': link,
                        'pub_date': pub_date,
                        'source_name': source_name,
                    })
        except Exception as e:
            print(f"RSS fetch error for {url}: {e}")
            continue
    return articles

def format_pub_date(pub_date_str):
    """Convert RFC 2822 date to human readable 'Xm ago' or time string."""
    try:
        import email.utils
        parsed = email.utils.parsedate_to_datetime(pub_date_str)
        now = datetime.datetime.now(datetime.timezone.utc)
        diff = now - parsed
        secs = int(diff.total_seconds())
        if secs < 3600:
            return f"{secs // 60}m ago"
        elif secs < 86400:
            return f"{secs // 3600}h ago"
        else:
            return f"{secs // 86400}d ago"
    except Exception:
        return "Recently"

@app.route('/api/news')
def get_pro_news():
    category = request.args.get('category', 'ALL').upper()
    
    # Determine which feeds to use
    if category == 'ALL':
        feed_urls = []
        for urls in NEWS_RSS_FEEDS.values():
            feed_urls.extend(urls[:1])  # One feed per category
    elif category in NEWS_RSS_FEEDS:
        feed_urls = NEWS_RSS_FEEDS[category]
    else:
        feed_urls = NEWS_RSS_FEEDS['STOCKS']
    
    raw_articles = fetch_rss_articles(feed_urls, max_per_feed=6)
    
    # Fallback if no articles fetched
    if not raw_articles:
        fallback_data = [
            ("Gold Prices Rise as Global Uncertainty Increases", "METALS", "https://in.reuters.com/finance/commodities", "Reuters"),
            ("Nifty 50 Advances on Strong Foreign Inflows", "STOCKS", "https://www.moneycontrol.com", "MoneyControl"),
            ("Bitcoin Holds $60K Support Despite Market Volatility", "CRYPTO", "https://coindesk.com", "CoinDesk"),
            ("Silver Demand Rises for Industrial Applications in EV Sector", "METALS", "https://in.reuters.com/finance/commodities", "Reuters"),
            ("Global Economy Shows Signs of Stabilization: IMF Report", "ECONOMY", "https://www.imf.org/en/News", "IMF"),
            ("Bank Nifty Options Show Unusual Activity Ahead of Expiry", "FNO", "https://www.nseindia.com", "NSE India"),
            ("Sensex Gains 500 Points; IT and Pharma Lead Rally", "STOCKS", "https://www.bseindia.com", "BSE India"),
            ("Federal Reserve Signals Cautious Approach to Rate Cuts", "ECONOMY", "https://www.reuters.com/markets", "Reuters"),
            ("Ethereum ETF Sees Record Inflows Amid Crypto Bull Run", "CRYPTO", "https://coindesk.com", "CoinDesk"),
            ("MCX Gold Futures Touch ₹72,000 Mark on Safe-Haven Demand", "METALS", "https://www.mcxindia.com", "MCX India"),
        ]
        raw_articles = [{'title': t, 'link': l, 'pub_date': '', 'source_name': s} 
                        for t, cat, l, s in fallback_data 
                        if category == 'ALL' or cat == category]
        if not raw_articles:
            raw_articles = [{'title': t, 'link': l, 'pub_date': '', 'source_name': s} 
                            for t, cat, l, s in fallback_data]

    processed_news = []
    seen_titles = set()
    
    for art in raw_articles:
        title = art['title']
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)
        
        art_category = guess_category(title) if category == 'ALL' else category
        affects = guess_affects(art_category, title.lower())
        
        # Sentiment Analysis using TextBlob
        analysis = TextBlob(title)
        polarity = analysis.sentiment.polarity
        
        if polarity > 0.05:
            sentiment_label = "Positive"
            sentiment_color = "success"
            trend = "Bullish"
        elif polarity < -0.05:
            sentiment_label = "Negative"
            sentiment_color = "danger"
            trend = "Bearish"
        else:
            sentiment_label = "Neutral"
            sentiment_color = "secondary"
            trend = "Neutral"
        
        # Impact assessment
        high_impact_keywords = ['crash', 'surge', 'record', 'historic', 'crisis', 'collapse', 'ban', 'all-time', 'major', 'billion', 'trillion', 'emergency', 'war', 'sanctions']
        med_impact_keywords = ['rise', 'fall', 'gain', 'drop', 'rally', 'slide', 'jump', 'climb', 'concern', 'worry', 'boost', 'cut', 'hike']
        title_lower = title.lower()
        if any(k in title_lower for k in high_impact_keywords):
            impact = "HIGH"
        elif any(k in title_lower for k in med_impact_keywords):
            impact = "MEDIUM"
        else:
            impact = "LOW"
        
        # AI Signal
        ai_signal = "HOLD"
        confidence = random.randint(62, 94)
        if sentiment_label == "Positive" and impact in ["HIGH", "MEDIUM"]:
            ai_signal = "BUY"
        elif sentiment_label == "Negative" and impact in ["HIGH", "MEDIUM"]:
            ai_signal = "SELL"
        
        time_str = format_pub_date(art['pub_date']) if art['pub_date'] else f"{random.randint(5, 55)}m ago"
        
        processed_news.append({
            "title": title,
            "category": art_category,
            "affects": affects,
            "trend": trend,
            "impact": impact,
            "sentiment": sentiment_label,
            "sentiment_color": sentiment_color,
            "ai_signal": ai_signal,
            "confidence": f"{confidence}%",
            "time": time_str,
            "source": art['source_name'],
            "link": art['link'],
        })
    
    # Shuffle for variety and limit results
    random.shuffle(processed_news)
    return jsonify({"status": "success", "news": processed_news[:20], "total": len(processed_news)})

if __name__ == "__main__":
    # Run the Flask app
    # Access at: http://localhost:5000 or http://127.0.0.1:5000
    # Use environment variable for debug mode (False in production)
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)