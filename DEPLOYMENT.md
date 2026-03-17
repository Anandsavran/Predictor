# Deployment Guide for Predictor.com

This guide will help you deploy your stock prediction Flask application to various platforms.

## Prerequisites

1. **Trained Model**: Make sure you have `stock_model.keras` in the `Templet/` folder
   - Run the Jupyter notebook `Predictor.com.ipynb` to generate the model
   - Or copy your trained model file to `Templet/stock_model.keras`

2. **Git Repository**: Initialize git if not already done
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

## Deployment Options

### Option 1: Render (Recommended - Free Tier Available)

1. **Sign up** at [render.com](https://render.com)

2. **Create a New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Or use "Public Git repository" and paste your repo URL

3. **Configure the service**:
   - **Name**: predictor-com (or your choice)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn Templet.app:app`
   - **Plan**: Free (or choose a paid plan)

4. **Environment Variables** (if needed):
   - No environment variables required for basic setup

5. **Deploy**: Click "Create Web Service"

6. **Wait for deployment** (5-10 minutes for first deployment)

Your app will be live at: `https://your-app-name.onrender.com`

---

### Option 2: Railway

1. **Sign up** at [railway.app](https://railway.app)

2. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo" (or upload files)

3. **Configure**:
   - Railway auto-detects Python projects
   - It will use `requirements.txt` automatically
   - Update start command if needed: `gunicorn Templet.app:app`

4. **Deploy**: Railway will automatically deploy

Your app will be live at: `https://your-app-name.up.railway.app`

---

### Option 3: Heroku

1. **Install Heroku CLI**: [heroku.com/cli](https://devcenter.heroku.com/articles/heroku-cli)

2. **Login**:
   ```bash
   heroku login
   ```

3. **Create App**:
   ```bash
   heroku create your-app-name
   ```

4. **Deploy**:
   ```bash
   git push heroku main
   ```

5. **Open App**:
   ```bash
   heroku open
   ```

---

### Option 4: PythonAnywhere

1. **Sign up** at [pythonanywhere.com](https://www.pythonanywhere.com)

2. **Upload Files**:
   - Use the Files tab to upload your project
   - Or use Git to clone your repository

3. **Configure Web App**:
   - Go to Web tab
   - Create new web app
   - Set source code path
   - Set WSGI file to `wsgi.py`

4. **Install Dependencies**:
   - Use Bash console: `pip3.10 install --user -r requirements.txt`

5. **Reload Web App**

---

## Important Notes

### Model File Size
- If your model file is large (>100MB), consider:
  - Using Git LFS (Large File Storage)
  - Uploading model to cloud storage (S3, Google Drive) and downloading on startup
  - Using a model hosting service

### Static Files
- The `Static/` folder will be created automatically
- Generated images and CSVs are saved here
- Make sure the folder has write permissions

### Memory Requirements
- TensorFlow/Keras models can be memory-intensive
- Free tiers may have limitations
- Consider upgrading if you encounter memory errors

### First Request
- The first request after deployment may be slow (cold start)
- Subsequent requests will be faster

---

## Testing Locally Before Deployment

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app**:
   ```bash
   cd Templet
   python app.py
   ```

3. **Test at**: `http://localhost:5000`

---

## Troubleshooting

### Model Not Found Error
- Ensure `stock_model.keras` is in the `Templet/` folder
- Check file permissions
- Verify the file was committed to git

### Import Errors
- Check `requirements.txt` has all dependencies
- Verify Python version matches `runtime.txt`

### Static Files Not Loading
- Check Flask static folder configuration
- Verify file paths are correct
- Check file permissions

### Memory Errors
- Upgrade to a paid plan with more RAM
- Consider optimizing the model size
- Use model quantization

---

## Quick Deploy Checklist

- [ ] Model file (`stock_model.keras`) exists in `Templet/` folder
- [ ] All files committed to git
- [ ] `requirements.txt` is up to date
- [ ] `Procfile` exists (for Heroku/Render)
- [ ] Tested locally
- [ ] Chosen deployment platform
- [ ] Created account on deployment platform
- [ ] Connected repository
- [ ] Deployed successfully
- [ ] Tested live URL

---

## Support

If you encounter issues:
1. Check deployment platform logs
2. Verify all files are present
3. Test locally first
4. Check platform-specific documentation

Good luck with your deployment! 🚀

