# Predictor.com - Stock Price Prediction Web Application 

A Flask-based web application that predicts stock prices using LSTM (Long Short-Term Memory) neural networks. The app provides interactive charts, exponential moving averages, and downloadable datasets.

## Features

- 📈 **Stock Price Prediction**: Uses deep learning LSTM model to predict stock prices
- 📊 **Interactive Charts**: Visualizes closing prices with EMA (20, 50, 100, 200 days)
- 📉 **Prediction Comparison**: Compares predicted vs actual prices
- 💾 **Data Export**: Download stock datasets as CSV files
- 🔍 **Multiple Stocks**: Support for any stock ticker from Yahoo Finance

## Tech Stack

- **Backend**: Flask (Python)
- **Machine Learning**: Keras/TensorFlow (LSTM)
- **Data Processing**: Pandas, NumPy
- **Visualization**: Matplotlib
- **Stock Data**: yfinance

## Project Structure

```
Predictor.com/
├── Templet/
│   ├── app.py              # Flask application
│   ├── index.html          # Web interface
│   ├── Predictor.com.ipynb # Model training notebook
│   ├── stock_model.keras   # Trained LSTM model (needs to be generated)
│   └── powergrid.csv       # Sample data
├── Static/                 # Generated charts and datasets
│   ├── ema_20_50.png
│   ├── ema_100_200.png
│   └── *.csv files
├── requirements.txt        # Python dependencies
├── Procfile               # Deployment configuration
├── wsgi.py                # WSGI entry point
└── DEPLOYMENT.md          # Deployment guide
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Train the Model

1. Open `Templet/Predictor.com.ipynb` in Jupyter Notebook
2. Run all cells to train the LSTM model
3. The model will be saved as `stock_model.keras` in the `Templet/` folder

### 3. Run Locally

```bash
cd Templet
python app.py
```

Visit `http://localhost:5000` in your browser.

## Usage

1. Enter a stock ticker symbol (e.g., `AAPL`, `MSFT`, `POWERGRID.NS`)
2. Click "Submit"
3. View the generated charts and statistics
4. Download the dataset if needed

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions to:
- Render (Recommended)
- Railway
- Heroku
- PythonAnywhere

## Requirements

- Python 3.11+
- Trained model file (`stock_model.keras`)
- Internet connection (for downloading stock data)

## Notes

- The model needs to be trained before the app can make predictions
- First request may take longer due to model loading
- Free hosting tiers may have memory limitations

## License

This project is open source and available for educational purposes.

