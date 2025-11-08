# 🚀 Deployment Guide

This guide provides step-by-step instructions for deploying the Unified Cloud Storage application to various free hosting platforms.

## 📋 Pre-deployment Checklist

- [ ] All API keys obtained from cloud providers
- [ ] Environment variables configured
- [ ] Application tested locally
- [ ] GitHub repository created and code pushed
- [ ] Production domains planned (for redirect URIs)

## 🌐 Production Environment Setup

### 1. Update OAuth Redirect URIs

For production deployment, you'll need to update the redirect URIs in your cloud provider applications:

**Google Drive API**:
- Add: `https://your-backend-domain.com/api/auth/google/callback`

**Dropbox API**:
- Add: `https://your-backend-domain.com/api/auth/dropbox/callback`

**Microsoft OneDrive API**:
- Add: `https://your-backend-domain.com/api/auth/microsoft/callback`

### 2. Environment Variables for Production

Create production environment variables with your actual domain:

```env
# Production Configuration
FLASK_ENV=production
SECRET_KEY=your-super-secure-production-key

# Updated redirect URIs for production
GOOGLE_REDIRECT_URI=https://your-backend-domain.com/api/auth/google/callback
DROPBOX_REDIRECT_URI=https://your-backend-domain.com/api/auth/dropbox/callback
MICROSOFT_REDIRECT_URI=https://your-backend-domain.com/api/auth/microsoft/callback
```

## 🎯 Deployment Options

## Option 1: Render (Recommended)

Render offers free hosting for both backend and frontend with automatic builds from GitHub.

### Backend on Render

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the `backend` directory as root

3. **Configure Service**
   ```
   Name: unified-cloud-storage-api
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn --bind 0.0.0.0:$PORT app:app
   ```

4. **Set Environment Variables**
   - Go to Environment tab
   - Add all variables from your `.env` file
   - Generate a secure SECRET_KEY

5. **Database Setup**
   - Create PostgreSQL database (free tier)
   - Update DATABASE_URL in environment variables
   - Render will provide the connection string

6. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy
   - Note your backend URL (e.g., `https://your-app.onrender.com`)

### Frontend on Render

1. **Create Static Site**
   - Click "New +" → "Static Site"
   - Connect your GitHub repository
   - Select the `frontend` directory as root

2. **Configure Build**
   ```
   Build Command: npm ci && npm run build
   Publish Directory: build
   ```

3. **Environment Variables**
   ```
   REACT_APP_API_URL=https://your-backend-url.onrender.com
   ```

4. **Deploy**
   - Click "Create Static Site"
   - Your frontend will be available at assigned URL

## Option 2: Vercel + Render

Use Vercel for frontend (excellent React support) and Render for backend.

### Frontend on Vercel

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Deploy from Frontend Directory**
   ```bash
   cd frontend
   vercel --prod
   ```

3. **Configure Environment Variables**
   - Go to Vercel dashboard → Project Settings → Environment Variables
   - Add: `REACT_APP_API_URL=https://your-backend-url.onrender.com`

4. **Automatic Deployments**
   - Connect GitHub repository
   - Auto-deploy on push to main branch

## Option 3: Heroku

Heroku offers free tier (with limitations) for both backend and frontend.

### Backend on Heroku

1. **Install Heroku CLI**
   - Download from [heroku.com](https://devcenter.heroku.com/articles/heroku-cli)

2. **Create Heroku App**
   ```bash
   cd backend
   heroku create your-app-name
   ```

3. **Add PostgreSQL**
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

4. **Set Environment Variables**
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set GOOGLE_CLIENT_ID=your-google-client-id
   heroku config:set GOOGLE_CLIENT_SECRET=your-google-client-secret
   # ... set all other environment variables
   ```

5. **Create Procfile**
   ```bash
   echo "web: gunicorn app:app" > Procfile
   ```

6. **Deploy**
   ```bash
   git push heroku main
   ```

## Option 4: Railway

Railway provides simple deployment with automatic builds.

### Backend on Railway

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign in with GitHub

2. **Deploy from GitHub**
   - Click "Deploy from GitHub repo"
   - Select your repository
   - Railway auto-detects Python app

3. **Environment Variables**
   - Go to Variables tab
   - Add all production environment variables

4. **Database**
   - Add PostgreSQL plugin
   - Railway provides DATABASE_URL automatically

## 🔧 Post-Deployment Configuration

### 1. Test Authentication Flows

After deployment, test each OAuth provider:

1. Visit your deployed frontend
2. Try connecting each cloud storage provider
3. Verify redirect URIs are working correctly

### 2. Update CORS Settings

If you encounter CORS errors, update your backend CORS configuration:

```python
# In app.py
from flask_cors import CORS

# Update with your frontend domain
CORS(app, 
     origins=["https://your-frontend-domain.com"],
     supports_credentials=True)
```

### 3. SSL/HTTPS Configuration

Most platforms automatically provide HTTPS, but verify:
- Check that all URLs use HTTPS
- Update OAuth redirect URIs to use HTTPS
- Test secure cookie functionality

## 🔄 Continuous Deployment

### Automatic Deployments

Set up automatic deployments for seamless updates:

1. **Render/Vercel**: Automatically deploy on git push
2. **Heroku**: Enable automatic deploys from GitHub
3. **Railway**: Auto-deploys on git push by default

### Environment-Specific Deployments

Create separate environments:

```bash
# Development
FLASK_ENV=development

# Staging
FLASK_ENV=staging

# Production
FLASK_ENV=production
```

## 🐛 Common Deployment Issues

### Issue: OAuth Redirect URI Mismatch
**Solution**: Ensure redirect URIs in cloud provider settings match exactly

### Issue: Environment Variables Not Loading
**Solution**: Check variable names and restart service

### Issue: Database Connection Errors
**Solution**: Verify DATABASE_URL format and database service status

### Issue: CORS Errors in Production
**Solution**: Update CORS origins to include production frontend domain

### Issue: Build Failures
**Solution**: Check Python/Node.js versions match local development

## 📊 Monitoring and Maintenance

### Application Monitoring

1. **Render**: Built-in metrics and logs
2. **Heroku**: Use Heroku metrics
3. **Vercel**: Analytics dashboard
4. **Railway**: Built-in observability

### Regular Maintenance

- **Weekly**: Check application status
- **Monthly**: Review logs for errors
- **Quarterly**: Update dependencies
- **Annually**: Rotate API keys and secrets

## 🔒 Production Security Checklist

- [ ] HTTPS enabled everywhere
- [ ] Secure session cookies
- [ ] Strong SECRET_KEY generated
- [ ] Environment variables not exposed
- [ ] API rate limiting configured
- [ ] CORS properly configured
- [ ] Database connections secured
- [ ] Regular security updates

## 📈 Scaling Considerations

### Free Tier Limitations

**Render Free**: 
- 512MB RAM, sleeps after 15 minutes inactivity
- 100GB bandwidth per month

**Heroku Free**: 
- Discontinued (paid plans available)

**Vercel Free**:
- 100GB bandwidth, 6000 minutes build time
- Serverless functions only

### Upgrade Paths

When ready to scale:
1. **Database**: Upgrade to managed PostgreSQL
2. **Compute**: Increase RAM/CPU resources
3. **CDN**: Add CloudFlare or similar
4. **Monitoring**: Add application monitoring
5. **Backup**: Implement database backups

---

## 🆘 Need Help?

If you encounter issues during deployment:

1. Check the application logs
2. Review the troubleshooting section in README.md
3. Search for similar issues in the GitHub repository
4. Create a new issue with deployment details

**Happy Deploying! 🚀**
