# Localhost Access Guide

## Understanding Your Application

This is a **Flask application** that serves both frontend and backend together:
- **Backend**: Flask server (Python) - handles requests, processes data, runs predictions
- **Frontend**: HTML templates served by Flask - the web interface you see in the browser

They are **not separate** - Flask serves everything on one port.

## How to Run Locally

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Navigate to Templet Folder
```bash
cd Templet
```

### Step 3: Run the Application
```bash
python app.py
```

### Step 4: Access the Application

Once the server starts, you'll see output like:
```
 * Running on http://127.0.0.1:5000
```

## Access URLs

### Main Application (Frontend + Backend)
- **URL**: `http://localhost:5000`
- **Alternative**: `http://127.0.0.1:5000`
- **What you see**: The web interface with form to enter stock ticker

### API Endpoints (Backend)

The Flask app has these routes:

1. **Main Page** (GET/POST)
   - `http://localhost:5000/`
   - Shows the form and results

2. **Download Files** (GET)
   - `http://localhost:5000/download/<filename>`
   - Downloads CSV files from Static folder
   - Example: `http://localhost:5000/download/POWERGRID.NS_dataset.csv`

## Important Notes

### Single Port Architecture
- **Frontend**: Served at `http://localhost:5000/` (HTML templates)
- **Backend**: Same port, handles POST requests and API calls
- **Static Files**: Served at `http://localhost:5000/static/<filename>`

### File Structure
```
Frontend (HTML):     Templet/index.html
Backend (Python):    Templet/app.py
Static Files:        Static/ folder (charts, CSVs)
Templates:           Served by Flask from Templet/
```

## Testing the Application

1. **Start the server**:
   ```bash
   cd Templet
   python app.py
   ```

2. **Open browser** and go to:
   ```
   http://localhost:5000
   ```

3. **Test the form**:
   - Enter a stock ticker (e.g., `AAPL`, `MSFT`, `POWERGRID.NS`)
   - Click "Submit"
   - View charts and predictions

4. **Check static files** (if generated):
   ```
   http://localhost:5000/static/ema_20_50.png
   http://localhost:5000/static/stock_prediction.png
   ```

## Troubleshooting

### Port Already in Use
If port 5000 is busy, change it in `app.py`:
```python
app.run(host='127.0.0.1', port=8080, debug=True)  # Use port 8080 instead
```
Then access at: `http://localhost:8080`

### Cannot Access from Other Devices
To access from other devices on your network:
```python
app.run(host='0.0.0.0', port=5000, debug=True)  # Listen on all interfaces
```
Then access from other devices using your computer's IP:
```
http://YOUR_IP_ADDRESS:5000
```

### Model Not Found Error
- Make sure `stock_model.keras` exists in `Templet/` folder
- Run the Jupyter notebook to generate it if missing

## Summary

| Component | URL | Description |
|-----------|-----|-------------|
| **Web Interface** | `http://localhost:5000` | Main page with form |
| **Backend API** | `http://localhost:5000/` | Same URL, handles POST requests |
| **Static Files** | `http://localhost:5000/static/<file>` | Charts and CSV files |
| **Downloads** | `http://localhost:5000/download/<file>` | Download endpoint |

**Remember**: Everything runs on **one port (5000)** because Flask serves both frontend and backend together!

