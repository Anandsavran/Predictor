# Data Pipeline for Machine Learning Platform
import yfinance as yf
import pandas as pd
import numpy as np

class StockDataPipeline:
    def __init__(self, use_mock_db=True):
        self.use_mock_db = use_mock_db

    def fetch_live_data(self, ticker, period="1y"):
        """Fetches live stock data using yfinance API"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            if hist.empty:
                raise ValueError(f"No data found for {ticker}")
            return hist
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return pd.DataFrame()

    def fetch_top_gainers(self):
        """Mock function to fetch top gainers (will connect to DB in future)"""
        # In a real environment, you'd calculate this or fetch from an API like NSE/BSE
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]

    def fetch_commodities(self):
        """Fetch GC=F (Gold), SI=F (Silver), HG=F (Copper)"""
        return {"Gold": "GC=F", "Silver": "SI=F", "Copper": "HG=F"}

    def fetch_crypto(self):
        """Fetch BTC-USD and ETH-USD"""
        return {"BTC": "BTC-USD", "ETH": "ETH-USD"}

    def save_to_database(self, df, table_name):
        """Mock database connection (MongoDB / PostgreSQL)"""
        if self.use_mock_db:
            print(f"Mock Save: Saved {len(df)} rows to {table_name}")
            return True
        # Real DB logic would go here:
        # engine = create_engine('postgresql://user:pass@localhost/db')
        # df.to_sql(table_name, engine)
        pass

if __name__ == "__main__":
    pipeline = StockDataPipeline()
    reliance_data = pipeline.fetch_live_data("RELIANCE.NS", "1mo")
    print(reliance_data.head())
