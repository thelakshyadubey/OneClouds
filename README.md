# Unified Multi-Cloud Storage Web Application

A comprehensive web application that aggregates files from multiple cloud storage services (Google Drive, Dropbox, OneDrive) into a single unified interface. This application provides metadata-only access, duplicate detection, file preview capabilities, and more.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![React](https://img.shields.io/badge/react-18.2+-blue.svg)

## ✨ Features

- **🔗 Multi-Cloud Integration**: Connect Google Drive, Dropbox, OneDrive, and more
- **📁 Unified File View**: See all files from different providers in one interface
- **🔍 Duplicate Detection**: Find and remove duplicate files across all cloud storage
- **👁 File Preview**: Preview files without downloading them
- **🔒 Secure Authentication**: OAuth 2.0 integration with read-only access
- **⚡ Fast & Efficient**: Metadata-only processing for optimal performance
- **📱 Responsive Design**: Works on desktop, tablet, and mobile devices
- **🎨 Modern UI**: Beautiful, intuitive interface built with React and Tailwind CSS

## 🏗 Architecture

### Backend (Python Flask)
- **Flask**: Web framework for REST API
- **SQLAlchemy**: Database ORM with SQLite
- **OAuth Libraries**: Secure authentication with cloud providers
- **Modular Design**: Separate provider modules for easy extensibility

### Frontend (React)
- **React 18**: Modern React with hooks and functional components
- **Tailwind CSS**: Utility-first CSS framework for styling
- **React Router**: Client-side routing
- **Axios**: HTTP client for API communication

### Supported Cloud Providers
- ✅ **Google Drive**: Full integration with file listing and metadata
- ✅ **Dropbox**: Complete API integration
- ✅ **OneDrive**: Microsoft Graph API integration
- 🔄 **Terabox**: Planned for future releases

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn
- Git

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

# Copy environment file and configure
cp .env.example .env
# Edit .env with your API credentials (see Configuration section)

# Initialize database
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"

# Run the backend
python app.py
```

The backend will be available at `http://localhost:5000`

### 3. Frontend Setup

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

The frontend will be available at `http://localhost:3000`

## ⚙️ Configuration

### API Keys Setup

You'll need to obtain API credentials from each cloud provider:

#### Google Drive API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Drive API
4. Create credentials (OAuth 2.0 Client ID)
5. Add authorized redirect URI: `http://localhost:5000/api/auth/google/callback`
6. Copy Client ID and Client Secret to your `.env` file

#### Dropbox API

1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Create a new app with "Scoped access" and "App folder" or "Full Dropbox"
3. Add redirect URI: `http://localhost:5000/api/auth/dropbox/callback`
4. Copy App key and App secret to your `.env` file

#### Microsoft OneDrive API

1. Go to [Azure App Registrations](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)
2. Register a new application
3. Add platform → Web → Redirect URI: `http://localhost:5000/api/auth/microsoft/callback`
4. Generate client secret in "Certificates & secrets"
5. Copy Application ID and Client Secret to your `.env` file

### Environment Variables

Update your `backend/.env` file with the obtained credentials:

```env
# Flask Configuration
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=development

# Google Drive API
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Dropbox API
DROPBOX_CLIENT_ID=your-dropbox-client-id
DROPBOX_CLIENT_SECRET=your-dropbox-client-secret

# Microsoft OneDrive API
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
```

## 📖 API Documentation

### Authentication Endpoints

- `GET /api/auth/google` - Initiate Google OAuth flow
- `GET /api/auth/google/callback` - Google OAuth callback
- `GET /api/auth/dropbox` - Initiate Dropbox OAuth flow
- `GET /api/auth/dropbox/callback` - Dropbox OAuth callback

### Core API Endpoints

- `GET /api/user` - Get current user information
- `GET /api/storage-accounts` - List connected storage accounts
- `POST /api/storage-accounts/{id}/sync` - Sync files from storage account
- `GET /api/files` - List all files with filtering and sorting
- `GET /api/duplicates` - Get duplicate file groups
- `POST /api/duplicates/remove` - Remove duplicate files

### Query Parameters for `/api/files`

- `provider` - Filter by provider (google_drive, dropbox, onedrive)
- `search` - Search in file names
- `sort_by` - Sort by field (name, size, modified_at_source, created_at_source)
- `sort_order` - Sort order (asc, desc)
- `page` - Page number for pagination
- `per_page` - Items per page (default: 50, max: 100)

## 🚀 Deployment

### Deploy to Render (Recommended)

#### Backend Deployment

1. Create account on [Render](https://render.com/)
2. Connect your GitHub repository
3. Create new Web Service
4. Configure environment variables in Render dashboard
5. Deploy using the provided `render.yaml` configuration

#### Frontend Deployment

1. Build the React app: `npm run build`
2. Deploy to Vercel, Netlify, or Render Static Site
3. Update API base URL for production

### Deploy to Vercel (Frontend)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy from frontend directory
cd frontend
vercel --prod
```

### Deploy to Heroku (Alternative)

1. Install Heroku CLI
2. Create new Heroku app
3. Configure environment variables
4. Deploy using Git

```bash
heroku create your-app-name
heroku config:set SECRET_KEY=your-secret-key
# Set other environment variables...
git push heroku main
```

## 🛠 Development

### Backend Development

```bash
# Run with auto-reload
export FLASK_ENV=development
python app.py

# Run tests (when available)
pytest

# Database migrations
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Frontend Development

```bash
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

1. Create new provider module in `backend/storage_providers/`
2. Implement the `CloudStorageProvider` abstract class
3. Add OAuth configuration in `config.py`
4. Add authentication routes in `app.py`
5. Update frontend to include new provider

Example provider structure:
```python
class NewProvider(CloudStorageProvider):
    def get_provider_name(self) -> str:
        return "new_provider"
    
    def get_user_info(self) -> Dict[str, Any]:
        # Implementation here
        pass
    
    def list_files(self, page_token: str = None, max_results: int = 100) -> Dict[str, Any]:
        # Implementation here
        pass
```

## 🔒 Security Considerations

- **Read-Only Access**: Application only requests read permissions
- **No File Content**: Only metadata is accessed, never file contents
- **Secure Storage**: Tokens are encrypted in database
- **OAuth 2.0**: Industry-standard authentication
- **HTTPS**: Use HTTPS in production
- **Environment Variables**: Sensitive data in environment variables

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 🐛 Troubleshooting

### Common Issues

**Issue: Google Drive authentication fails**
- Ensure redirect URI is exactly: `http://localhost:5000/api/auth/google/callback`
- Check that Google Drive API is enabled in Google Cloud Console

**Issue: CORS errors in development**
- Backend and frontend are running on different ports (5000 and 3000)
- CORS is configured in Flask app

**Issue: Database errors**
- Make sure SQLite database is created: `python -c "from app import db; db.create_all()"`
- Check file permissions in project directory

**Issue: Frontend not connecting to backend**
- Verify backend is running on port 5000
- Check API base URL in frontend configuration

### Getting Help

- 📧 Email: support@example.com
- 💬 Discord: [Join our community](https://discord.gg/example)
- 🐛 Issues: [GitHub Issues](https://github.com/your-username/unified-cloud-storage/issues)

## 🙏 Acknowledgments

- Flask and React communities for excellent documentation
- Cloud storage providers for their APIs
- Contributors and beta testers

---

**Made with ❤️ by the UnifiedCloud Team**
