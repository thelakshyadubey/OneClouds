# Unified Multi-Cloud Storage - Complete Setup Guide

This guide provides step-by-step instructions to set up the Unified Multi-Cloud Storage application from scratch. The application allows you to view, manage, and organize files from multiple cloud storage providers (Google Drive, Google Photos, Dropbox, OneDrive, and Terabox) in one unified interface.

## 🏗️ Architecture Overview

### Backend (FastAPI + Python)
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: Database ORM with SQLite/PostgreSQL support
- **OAuth 2.0**: Secure authentication with all cloud providers
- **Async Support**: Asynchronous operations for better performance
- **Comprehensive Security**: Token encryption, rate limiting, input validation

### Frontend (React)
- **React 18**: Modern React with hooks and functional components
- **Tailwind CSS**: Utility-first CSS framework for styling
- **React Router**: Client-side routing
- **Axios**: HTTP client for API communication

### Supported Cloud Providers
- ✅ **Google Drive**: Full integration with file listing, metadata, upload/download
- ✅ **Google Photos**: Photo and video management with advanced features
- ✅ **Dropbox**: Complete API integration with file operations
- ✅ **OneDrive**: Microsoft Graph API integration
- ⚠️ **Terabox**: Basic implementation (limited API documentation)

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**: Download from [python.org](https://python.org)
- **Node.js 16+**: Download from [nodejs.org](https://nodejs.org)
- **Git**: For cloning the repository

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/unified-cloud-storage.git
cd unified-cloud-storage
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Edit .env with your API credentials (see next section)
# You can use any text editor, for example:
notepad .env  # Windows
# nano .env   # Linux/macOS
```

### 3. API Keys Configuration

You need to obtain API credentials from each cloud provider. This section provides detailed instructions for each provider.

#### 🔧 Google Drive API Setup

1. **Go to Google Cloud Console**
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable APIs**
   - Navigate to "APIs & Services" → "Library"
   - Search for and enable "Google Drive API"
   - Search for and enable "Google Photos Library API" (if you want Photos support)

3. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Configure consent screen if prompted
   - Choose "Web application" as application type
   - Add authorized redirect URIs:
     - `http://localhost:8000/api/auth/google_drive/callback`
     - `http://localhost:8000/api/auth/google_photos/callback`

4. **Copy Credentials to .env**
   ```env
   GOOGLE_DRIVE_CLIENT_ID=your-google-client-id
   GOOGLE_DRIVE_CLIENT_SECRET=your-google-client-secret
   GOOGLE_PHOTOS_CLIENT_ID=your-google-client-id  # Usually same as Drive
   GOOGLE_PHOTOS_CLIENT_SECRET=your-google-client-secret
   ```

#### 📦 Dropbox API Setup

1. **Create Dropbox App**
   - Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
   - Click "Create App"
   - Choose "Scoped access" and "Full Dropbox" access
   - Give your app a name

2. **Configure OAuth**
   - In app settings, add redirect URI: `http://localhost:8000/api/auth/dropbox/callback`
   - Note down the "App key" and "App secret"

3. **Add to .env**
   ```env
   DROPBOX_CLIENT_ID=your-dropbox-app-key
   DROPBOX_CLIENT_SECRET=your-dropbox-app-secret
   ```

#### 🏢 Microsoft OneDrive API Setup

1. **Register Azure App**
   - Go to [Azure App Registrations](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps)
   - Click "New registration"
   - Choose "Accounts in any organizational directory and personal Microsoft accounts"

2. **Configure Authentication**
   - Go to "Authentication" → "Add platform" → "Web"
   - Add redirect URI: `http://localhost:8000/api/auth/onedrive/callback`

3. **Create Client Secret**
   - Go to "Certificates & secrets" → "Client secrets"
   - Click "New client secret" and save the value

4. **Set Permissions**
   - Go to "API permissions" → "Add permission"
   - Add "Microsoft Graph" → "Delegated permissions"
   - Add: `Files.Read.All`, `User.Read`

5. **Add to .env**
   ```env
   ONEDRIVE_CLIENT_ID=your-azure-application-id
   ONEDRIVE_CLIENT_SECRET=your-client-secret-value
   ```

#### 📂 Terabox API Setup (Optional)

*Note: Terabox API documentation is limited. This integration is experimental.*

1. **Contact Terabox**
   - Terabox doesn't have public API documentation
   - You may need to contact them directly for API access

2. **Add to .env** (if you have credentials)
   ```env
   TERABOX_CLIENT_ID=your-terabox-client-id
   TERABOX_CLIENT_SECRET=your-terabox-client-secret
   ```

### 4. Security Configuration

Update these important security settings in your `.env` file:

```env
# Generate a strong secret key (32+ characters)
SECRET_KEY=your-super-secret-key-change-in-production-32chars-minimum

# Generate an encryption key (exactly 32 characters)
ENCRYPTION_KEY=your-encryption-key-32-characters!
```

**Important**: In production, use cryptographically secure random keys:
```python
import secrets
print("SECRET_KEY:", secrets.token_urlsafe(64))
print("ENCRYPTION_KEY:", secrets.token_urlsafe(24))  # Will be 32 chars when base64 encoded
```

### 5. Initialize Database

```bash
# Still in backend directory with activated virtual environment
python -c "from database import engine, Base; Base.metadata.create_all(bind=engine)"

# Or run the main application once to create tables automatically
python main.py
```

### 6. Start Backend Server

```bash
# Development server with auto-reload
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at: `http://localhost:8000`
- API Documentation: `http://localhost:8000/api/docs`
- Alternative docs: `http://localhost:8000/api/redoc`

### 7. Frontend Setup

Open a new terminal and navigate to the frontend directory:

```bash
# From project root
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

The frontend will be available at: `http://localhost:3000`

## 🔧 Configuration Reference

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | JWT signing secret | - | ✅ |
| `ENCRYPTION_KEY` | Token encryption key (32 chars) | - | ✅ |
| `DATABASE_URL` | Database connection string | `sqlite:///./unified_storage.db` | ✅ |
| `FRONTEND_URL` | Frontend application URL | `http://localhost:3000` | ✅ |
| `BACKEND_URL` | Backend API URL | `http://localhost:8000` | ✅ |
| `DEBUG` | Enable debug mode | `true` | - |
| `MAX_REQUESTS_PER_MINUTE` | API rate limit | `60` | - |
| `MAX_FILES_PER_SYNC` | Max files per sync operation | `1000` | - |

### Cloud Provider Settings

Each provider requires `CLIENT_ID`, `CLIENT_SECRET`, and `REDIRECT_URI` configuration.

## 🚀 Production Deployment

### Backend Deployment (Render)

1. **Create Render Account**
   - Sign up at [render.com](https://render.com)
   - Connect your GitHub repository

2. **Create Web Service**
   - Choose "New Web Service"
   - Select your repository
   - Configure:
     - **Build Command**: `cd backend && pip install -r requirements.txt`
     - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
     - **Environment**: `python3`

3. **Set Environment Variables**
   Add all your `.env` variables in Render dashboard, including:
   ```
   SECRET_KEY=your-production-secret-key
   ENCRYPTION_KEY=your-production-encryption-key
   DATABASE_URL=your-production-database-url
   FRONTEND_URL=https://your-frontend-domain.com
   ```

4. **Database Setup**
   - For production, use PostgreSQL:
   ```bash
   # Add to requirements.txt
   psycopg2-binary==2.9.9
   ```
   - Set `DATABASE_URL` to your PostgreSQL connection string

### Frontend Deployment (Vercel)

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Deploy**
   ```bash
   cd frontend
   # Update API base URL in src/config.js to your backend URL
   vercel --prod
   ```

### Alternative: Docker Deployment

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/unified_storage
    depends_on:
      - db
  
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
  
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: unified_storage
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 🛠️ Development

### Backend Development

```bash
# Auto-reload development server
cd backend
python main.py

# Run with specific host/port
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests (when available)
pytest

# Database migrations with Alembic
alembic init alembic
alembic revision --autogenerate -m "Initial migration"  
alembic upgrade head
```

### Frontend Development

```bash
cd frontend

# Start development server
npm start

# Run tests
npm test

# Build for production
npm run build

# Analyze bundle size
npm run build && npx serve -s build
```

### Adding New Cloud Providers

1. **Create Provider Class**
   ```python
   # backend/storage_providers/new_provider.py
   from .base import CloudStorageProvider
   
   class NewProvider(CloudStorageProvider):
       def get_provider_name(self) -> str:
           return "new_provider"
       
       async def get_user_info(self) -> Dict[str, Any]:
           # Implementation
           pass
       
       async def list_files(self, page_token: str = None, max_results: int = 100):
           # Implementation  
           pass
   ```

2. **Register Provider**
   ```python
   # backend/storage_providers/__init__.py
   from .new_provider import NewProvider
   PROVIDER_CLASSES['new_provider'] = NewProvider
   ```

3. **Add Configuration**
   ```python
   # backend/config.py
   NEW_PROVIDER_CLIENT_ID = os.getenv("NEW_PROVIDER_CLIENT_ID")
   NEW_PROVIDER_CLIENT_SECRET = os.getenv("NEW_PROVIDER_CLIENT_SECRET")
   ```

4. **Update Frontend**
   Add provider support in React components and routing.

## 🔒 Security Best Practices

### Production Security Checklist

- [ ] Use strong, unique SECRET_KEY and ENCRYPTION_KEY
- [ ] Enable HTTPS in production
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set up proper CORS policies
- [ ] Enable rate limiting
- [ ] Use environment variables for all secrets
- [ ] Regular security updates
- [ ] Monitor for suspicious activity
- [ ] Implement proper logging
- [ ] Use secure session cookies

### Token Security

- All OAuth tokens are encrypted before storage
- Tokens are never logged or exposed in API responses
- Automatic token refresh when expired
- Secure token transmission over HTTPS

## 🐛 Troubleshooting

### Common Issues

**Issue: Google Drive authentication fails**
- Verify redirect URI is exactly: `http://localhost:8000/api/auth/google_drive/callback`
- Ensure Google Drive API is enabled in Google Cloud Console
- Check that OAuth consent screen is configured

**Issue: Database errors**
- Ensure database file has write permissions
- Check DATABASE_URL format
- For SQLite: ensure directory exists

**Issue: CORS errors**
- Backend runs on port 8000, frontend on 3000
- CORS is configured in main.py
- Check FRONTEND_URL in .env matches your frontend URL

**Issue: Token encryption errors**
- Ensure ENCRYPTION_KEY is exactly 32 characters
- Don't change ENCRYPTION_KEY after tokens are stored (they'll become unreadable)

**Issue: Frontend not connecting to backend**
- Verify backend is running on correct port
- Check API base URL in frontend configuration
- Ensure no firewall blocking connections

### Getting Help

- 📧 **Email**: Create GitHub issues for support
- 💬 **Discord**: Join our community (link in README)
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-username/unified-cloud-storage/issues)

## 📈 Performance Optimization

### Backend Optimization
- Use Redis for caching (set REDIS_URL)
- Enable database connection pooling
- Implement background tasks for large syncs
- Use CDN for static files

### Frontend Optimization
- Implement lazy loading for file lists
- Use virtual scrolling for large lists
- Optimize image loading with thumbnails
- Implement proper caching strategies

## 🔄 Backup and Maintenance

### Regular Maintenance Tasks
- Update dependencies regularly
- Monitor disk space usage
- Clean up old sync logs
- Review security logs
- Update API credentials before expiration

### Backup Strategy
- Regular database backups
- Environment configuration backup
- Code repository backup
- Monitor backup integrity

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI and React communities
- Cloud storage provider APIs
- All contributors and users
- Open source security tools

---

**Made with ❤️ for the developer community**

For more information, see the main [README.md](README.md) file.
