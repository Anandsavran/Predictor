from textblob import TextBlob
try:
    analysis = TextBlob("Test sentence")
    print(f"Polarity: {analysis.sentiment.polarity}")
except Exception as e:
    print(f"Error: {e}")
