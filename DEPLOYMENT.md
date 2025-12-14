# Render.com Deployment Guide

## The Problem We Fixed

The original deployment error was caused by render.com trying to use the local `.venv` directory which contained incompatible package versions for Python 3.13. Specifically, older versions of `antlr4-python3-runtime` don't work with Python 3.13.

## What We Changed

### 1. **render.yaml** - Render.com Configuration
- Specifies Python 3.13.1 as the runtime
- Uses `build.sh` script for clean dependency installation
- Configures environment variables (TX_ENDPOINT, LOGFILENAME)
- Sets proper start command

### 2. **.renderignore** - Exclude Files from Deployment
- Excludes `.venv` directory (critical fix)
- Excludes test files and unnecessary files
- Reduces deployment size and prevents conflicts

### 3. **build.sh** - Build Script
- Upgrades pip to latest version
- Installs dependencies from requirements.txt
- Creates necessary directories (logs)
- Ensures clean build environment

### 4. **.python-version** - Python Version Specification
- Explicitly specifies Python 3.13.1
- Helps render.com use the correct Python runtime

### 5. **main.py Updates**
- Uses `PORT` environment variable (required by render.com)
- Disables debug mode in production
- Automatically creates logs directory if missing
- Falls back to port 5001 for local development

## How to Deploy on Render.com

### Option 1: Use render.yaml (Recommended)

1. **Push your changes to GitHub** (already done ✓)

2. **Create a new Web Service on Render.com**:
   - Go to https://render.com/dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub repository: `mjosborne1/ecl_expressions`
   - Render will automatically detect the `render.yaml` file

3. **Verify Settings** (should be auto-configured from render.yaml):
   - Name: `ecl-expressions`
   - Environment: `Python 3`
   - Build Command: `./build.sh`
   - Start Command: `python main.py`

4. **Deploy**:
   - Click "Create Web Service"
   - Render will build and deploy automatically

### Option 2: Manual Configuration

If you prefer to configure manually:

1. **Create Web Service**:
   - Repository: `mjosborne1/ecl_expressions`
   - Branch: `main`
   
2. **Settings**:
   - **Name**: `ecl-expressions`
   - **Environment**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `python main.py`
   - **Python Version**: Add environment variable `PYTHON_VERSION=3.13.1`

3. **Environment Variables**:
   ```
   TX_ENDPOINT=https://tx.ontoserver.csiro.au/fhir
   LOGFILENAME=./logs/ecl.log
   ```

4. **Deploy**: Click "Create Web Service"

## What to Expect

### Build Process
```
==> Building...
==> Running ./build.sh
Collecting Flask==2.3.3
Collecting antlr4-python3-runtime==4.13.2
...
==> Build successful 🎉
```

### Deployment
```
==> Deploying...
==> Running 'python main.py'
 * Serving Flask app 'main'
 * Running on http://0.0.0.0:10000
```

### Your App URL
After deployment, your app will be available at:
```
https://ecl-expressions.onrender.com
```
(or whatever name you chose)

## Troubleshooting

### If Build Still Fails

1. **Check Python Version**:
   - Ensure render.com is using Python 3.13.1
   - Check build logs for Python version line

2. **Clear Build Cache**:
   - In render.com dashboard: Settings → "Clear build cache & deploy"

3. **Verify requirements.txt**:
   ```bash
   # Make sure you have the latest version
   antlr4-python3-runtime==4.13.2
   ```

4. **Check .renderignore**:
   - Ensure `.venv` is listed (it is ✓)

### If App Starts But Doesn't Work

1. **Check Logs**:
   - In render.com dashboard: Logs tab
   - Look for Flask startup messages

2. **Verify Environment Variables**:
   - Settings → Environment Variables
   - Ensure TX_ENDPOINT and LOGFILENAME are set

3. **Test Locally First**:
   ```bash
   # Simulate production environment
   export PORT=10000
   python main.py
   # Visit http://localhost:10000
   ```

## Local Development vs Production

### Local Development (debug mode on)
```bash
python main.py
# Runs on http://localhost:5001
# Debug mode enabled
# Auto-reloads on code changes
```

### Production (render.com)
```bash
# Automatically uses PORT from environment
# Debug mode disabled
# Optimized for production
```

## Key Files Summary

- **render.yaml**: Main render.com configuration
- **.renderignore**: Files to exclude from deployment
- **build.sh**: Custom build script
- **.python-version**: Specifies Python 3.13.1
- **requirements.txt**: Python dependencies (already correct)
- **main.py**: Updated to work with render.com

## Next Steps

1. ✅ Changes pushed to GitHub
2. ⏭️ Create Web Service on render.com
3. ⏭️ Wait for build and deployment
4. ⏭️ Test your deployed app
5. ⏭️ Share the URL!

## Need Help?

- **Render.com Docs**: https://render.com/docs/deploy-flask
- **Render Support**: https://render.com/docs/troubleshooting-deploys
- **This Project**: Check the logs in render.com dashboard