/**
 * Application configuration
 */

const config = {
  // API Configuration
  API_BASE_URL: "http://localhost:8000", // Updated to match backend port

  // Application Settings
  APP_NAME: "Unified Cloud Storage",
  APP_VERSION: "1.0.0",

  // File Management
  MAX_FILE_SIZE: 100 * 1024 * 1024, // 100MB
  SUPPORTED_FILE_TYPES: [
    // Images
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
    ".svg",
    // Videos
    ".mp4",
    ".avi",
    ".mov",
    ".wmv",
    ".flv",
    ".webm",
    ".mkv",
    // Documents
    ".pdf",
    ".doc",
    ".docx",
    ".txt",
    ".rtf",
    ".odt",
    // Spreadsheets
    ".xls",
    ".xlsx",
    ".csv",
    ".ods",
    // Presentations
    ".ppt",
    ".pptx",
    ".odp",
    // Archives
    ".zip",
    ".rar",
    ".7z",
    ".tar",
    ".gz",
    // Audio
    ".mp3",
    ".wav",
    ".flac",
    ".aac",
    ".ogg",
    ".m4a",
  ],

  // UI Settings
  DEFAULT_PAGE_SIZE: 50,
  MAX_PAGE_SIZE: 200,
  THUMBNAIL_SIZE: 200,
  PREVIEW_SIZE: 800,

  // Supported Cloud Providers
  CLOUD_PROVIDERS: [
    {
      id: "google_drive",
      name: "Google Drive",
      icon: "google-drive",
      color: "#4285f4",
      description: "Access your Google Drive files",
    },
    {
      id: "google_photos",
      name: "Google Photos",
      icon: "google-photos",
      color: "#ea4335",
      description: "Access your Google Photos",
    },
    {
      id: "dropbox",
      name: "Dropbox",
      icon: "dropbox",
      color: "#0061ff",
      description: "Access your Dropbox files",
    },
    {
      id: "onedrive",
      name: "OneDrive",
      icon: "onedrive",
      color: "#0078d4",
      description: "Access your OneDrive files",
    },
    {
      id: "terabox",
      name: "Terabox",
      icon: "terabox",
      color: "#ff6b35",
      description: "Access your Terabox files",
    },
  ],

  // File Type Icons
  FILE_TYPE_ICONS: {
    // Images
    image: "photo",
    jpg: "photo",
    jpeg: "photo",
    png: "photo",
    gif: "photo",
    bmp: "photo",
    webp: "photo",
    svg: "photo",

    // Videos
    video: "film",
    mp4: "film",
    avi: "film",
    mov: "film",
    wmv: "film",
    flv: "film",
    webm: "film",
    mkv: "film",

    // Documents
    pdf: "document-text",
    doc: "document-text",
    docx: "document-text",
    txt: "document-text",
    rtf: "document-text",

    // Spreadsheets
    xls: "table",
    xlsx: "table",
    csv: "table",

    // Presentations
    ppt: "presentation-chart-bar",
    pptx: "presentation-chart-bar",

    // Archives
    zip: "archive-box",
    rar: "archive-box",
    "7z": "archive-box",
    tar: "archive-box",
    gz: "archive-box",

    // Audio
    audio: "musical-note",
    mp3: "musical-note",
    wav: "musical-note",
    flac: "musical-note",
    aac: "musical-note",
    ogg: "musical-note",

    // Default
    default: "document",
  },

  // Error Messages
  ERRORS: {
    NETWORK_ERROR: "Network error. Please check your connection.",
    AUTH_REQUIRED: "Authentication required. Please sign in.",
    PERMISSION_DENIED:
      "Permission denied. Please check your account permissions.",
    FILE_NOT_FOUND: "File not found.",
    UPLOAD_FAILED: "Upload failed. Please try again.",
    DELETE_FAILED: "Delete failed. Please try again.",
    SYNC_FAILED: "Sync failed. Please try again.",
    INVALID_FILE_TYPE: "Invalid file type. Please check supported formats.",
    FILE_TOO_LARGE: "File too large. Maximum size is 100MB.",
    QUOTA_EXCEEDED: "Storage quota exceeded.",
    RATE_LIMIT: "Too many requests. Please wait and try again.",
    SERVER_ERROR: "Server error. Please try again later.",
  },

  // Success Messages
  SUCCESS: {
    AUTH_SUCCESS: "Successfully authenticated!",
    UPLOAD_SUCCESS: "File uploaded successfully!",
    DELETE_SUCCESS: "File deleted successfully!",
    SYNC_SUCCESS: "Sync completed successfully!",
    ACCOUNT_CONNECTED: "Account connected successfully!",
    ACCOUNT_DISCONNECTED: "Account disconnected successfully!",
    DUPLICATES_REMOVED: "Duplicate files removed successfully!",
  },
};

export default config;
