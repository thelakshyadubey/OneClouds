# 🔑 API Setup Guide - Cloud Provider Configuration

## 📋 **Current Status**
✅ **Backend & Frontend are fully functional**  
🔧 **Next Step**: Configure cloud provider API credentials

---

## 🚀 **Quick Test First (Optional)**
You can test the app **right now** without API keys:

1. **Start Backend**: `cd backend && uvicorn main:app --reload`
2. **Start Frontend**: `cd frontend && npm start`  
3. **Visit**: http://localhost:3000

The app will work, but cloud connections won't function until you add real API credentials below.

---

## 🔧 **API Configuration Steps**

### 📂 **Location**: `backend/.env`
You need to replace the placeholder values with real API credentials from each cloud provider.

---

## 1. 🟦 **Google Drive API Setup**

### **Create Google Cloud Project**:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Google Drive API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Configure OAuth consent screen
6. Set **Authorized redirect URIs**: `http://localhost:8000/api/auth/google_drive/callback`

### **Update .env**:
```env
GOOGLE_DRIVE_CLIENT_ID=your-actual-google-client-id
GOOGLE_DRIVE_CLIENT_SECRET=your-actual-google-client-secret
```

---

## 2. 📸 **Google Photos API Setup**

### **Same Google Cloud Project**:
1. Enable **Photos Library API** 
2. Use same OAuth credentials or create new ones
3. Add redirect URI: `http://localhost:8000/api/auth/google_photos/callback`

### **Update .env**:
```env
GOOGLE_PHOTOS_CLIENT_ID=your-actual-google-photos-client-id
GOOGLE_PHOTOS_CLIENT_SECRET=your-actual-google-photos-client-secret
```

---

## 3. 🟣 **Dropbox API Setup**

### **Create Dropbox App**:
1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. **Create App** → **Scoped Access** → **Full Dropbox**
3. Set **Redirect URIs**: `http://localhost:8000/api/auth/dropbox/callback`
4. Get **App key** and **App secret**

### **Update .env**:
```env
DROPBOX_CLIENT_ID=your-dropbox-app-key
DROPBOX_CLIENT_SECRET=your-dropbox-app-secret
```

---

## 4. 🟦 **Microsoft OneDrive API Setup**

### **Create Azure App Registration**:
1. Go to [Azure Portal](https://portal.azure.com/)
2. **Azure Active Directory** → **App Registrations** → **New Registration**
3. Set **Redirect URI**: `http://localhost:8000/api/auth/onedrive/callback`
4. **API Permissions** → Add **Microsoft Graph** → **Files.Read.All**
5. Get **Application (client) ID** and create **Client Secret**

### **Update .env**:
```env
ONEDRIVE_CLIENT_ID=your-azure-client-id
ONEDRIVE_CLIENT_SECRET=your-azure-client-secret
```

---

## 5. 📦 **Terabox API (Optional)**

### **Note**: Terabox has limited public API
```env
# Leave as placeholder for now
TERABOX_CLIENT_ID=your-terabox-client-id
TERABOX_CLIENT_SECRET=your-terabox-client-secret
```

---

## 📝 **Example .env Configuration**

```env
# Core Application Settings (✅ Already configured)
SECRET_KEY=your-super-secret-key-change-in-production-32chars-minimum
ENCRYPTION_KEY=0123456789abcdef0123456789abcdef
DEBUG=true

# Database Configuration (✅ Already configured)
DATABASE_URL=sqlite:///./unified_storage.db

# Application URLs (✅ Already configured)
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

# 🔧 REPLACE THESE WITH REAL VALUES:
GOOGLE_DRIVE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_DRIVE_CLIENT_SECRET=GOCSPX-your_actual_secret_here

DROPBOX_CLIENT_ID=your_dropbox_app_key
DROPBOX_CLIENT_SECRET=your_dropbox_app_secret

ONEDRIVE_CLIENT_ID=12345678-1234-1234-1234-123456789012
ONEDRIVE_CLIENT_SECRET=your_azure_client_secret
```

---

## ⚡ **Testing After API Setup**

1. **Start both servers**
2. **Go to Dashboard**: http://localhost:3000/dashboard
3. **Click "Connect" buttons** for each provider
4. **Authorize** your accounts
5. **Sync files** and see them in the Files page

---

## 🔒 **Security Notes**

### ✅ **Current Security** (Already Configured):
- JWT authentication
- Token encryption  
- Secure session handling
- Input validation

### 🛡️ **Production Security** (When ready):
- Change `SECRET_KEY` to a strong random value
- Set `DEBUG=false`
- Use PostgreSQL database
- Enable HTTPS
- Use production OAuth URLs

---

## 🎯 **Priority Setup Order**

**Start with these for best results**:
1. **Google Drive** (easiest, most documentation)
2. **Dropbox** (straightforward setup)
3. **OneDrive** (requires Azure account)
4. **Google Photos** (similar to Drive)
5. **Terabox** (optional, limited API)

---

## 🚀 **Ready to Go!**

Once you add **any one provider's credentials**, you can:
- ✅ Connect that cloud storage account
- ✅ Sync and view files
- ✅ Test the full application flow
- ✅ Add more providers incrementally

The app is **fully functional** - just needs your API keys to connect to real cloud storage! 🎉
