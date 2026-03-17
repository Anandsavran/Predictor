# Quick Start - Deploy Your App in 5 Minutes

## Step 1: Prepare Your Model
Make sure you have `stock_model.keras` in the `Templet/` folder. If not:
1. Open `Templet/Predictor.com.ipynb`
2. Run all cells
3. Model will be saved as `stock_model.keras`

## Step 2: Choose a Platform

### 🚀 Render (Easiest - Recommended)
1. Go to [render.com](https://render.com) and sign up
2. Click "New +" → "Web Service"
3. Connect your GitHub repo (or use public Git URL)
4. Settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app`
5. Click "Create Web Service"
6. Wait 5-10 minutes
7. Done! Your app is live 🎉

### 🚂 Railway (Alternative)
1. Go to [railway.app](https://railway.app) and sign up
2. Click "New Project" → "Deploy from GitHub"
3. Select your repository
4. Railway auto-detects everything
5. Deploy automatically
6. Done!

## Step 3: Test Your App
Visit your deployment URL and:
1. Enter a stock ticker (e.g., `AAPL`)
2. Click Submit
3. View the charts and predictions

## Troubleshooting

**Model not found?**
- Make sure `stock_model.keras` is committed to git
- Check file is in `Templet/` folder

**Build fails?**
- Check `requirements.txt` is present
- Verify Python version in `runtime.txt`

**App crashes?**
- Check deployment logs
- Verify all files are uploaded
- Test locally first: `python Templet/app.py`

## Need Help?
See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

