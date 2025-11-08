/**
 * API Service for backend communication
 */

import axios from "axios";
import config from "../config";
import toast from "react-hot-toast";

// Create axios instance
const api = axios.create({
  baseURL: config.API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Token management
export const tokenManager = {
  get: () => localStorage.getItem("accessToken"),
  set: (token) => localStorage.setItem("accessToken", token),
  remove: () => {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
  },
  getDeviceFingerprint: () => {
    let fingerprint = localStorage.getItem("deviceFingerprint");
    if (!fingerprint) {
      fingerprint =
        Date.now().toString() + Math.random().toString(36).substring(2, 15);
      localStorage.setItem("deviceFingerprint", fingerprint);
    }
    return fingerprint;
  },
  setTokens: (accessToken, refreshToken) => {
    localStorage.setItem("accessToken", accessToken);
    localStorage.setItem("refreshToken", refreshToken);
  },
};

// Request interceptor - Add authentication token
api.interceptors.request.use(
  (config) => {
    const accessToken = tokenManager.get();
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle errors - No auth redirect
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Log error but don't redirect on 401 during testing
    console.log("API Error:", error.response?.status, error.message);
    return Promise.reject(error);
  }
);

// API Services
export const authService = {
  // User login
  login: async (email, password, deviceFingerprint) => {
    try {
      const response = await api.post("/api/auth/login", {
        email,
        password,
        device_fingerprint: deviceFingerprint,
      });
      const { access_token, refresh_token, requires_2fa, device_trusted } =
        response.data;
      if (access_token && refresh_token) {
        tokenManager.setTokens(access_token, refresh_token);
      }
      return { access_token, refresh_token, requires_2fa, device_trusted };
    } catch (error) {
      console.error("Login error:", error);
      throw error;
    }
  },

  // User registration
  register: async (email, name, password, confirmPassword) => {
    return api.post("/api/auth/register", {
      email,
      name,
      password,
      confirm_password: confirmPassword,
    });
  },

  verifyOtp: async (email, otp, deviceFingerprint = null) => {
    try {
      const response = await api.post("/api/auth/verify-otp", {
        email,
        otp,
        device_fingerprint: deviceFingerprint,
      });
      const { access_token, refresh_token, requires_2fa, device_trusted } =
        response.data;
      if (access_token && refresh_token) {
        tokenManager.setTokens(access_token, refresh_token);
      }
      return { access_token, refresh_token, requires_2fa, device_trusted };
    } catch (error) {
      console.error("Error verifying OTP:", error);
      throw error;
    }
  },

  // Check authentication status
  checkAuth: async () => {
    try {
      const response = await api.get("/api/user");
      return response.data;
    } catch (error) {
      tokenManager.remove();
      throw error;
    }
  },

  // Get connected providers
  getConnectedProviders: async () => {
    const response = await api.get("/api/storage-accounts");
    return response.data;
  },

  // Initiate OAuth flow
  initiateAuth: async (provider, mode) => {
    try {
      const response = await api.get(`/api/auth/${provider}?mode=${mode}`);
      // The backend will return a RedirectResponse, which axios might not directly follow.
      // We expect the backend to give us a URL to redirect to.
      // For FastAPI RedirectResponse, the URL is in the 'Location' header, but for a direct response,
      // it might be in the response data itself. Let's assume it's in response.data.oauth_url
      // based on typical API patterns.
      window.location.href =
        response.data.oauth_url || response.request.responseURL;
    } catch (error) {
      console.error("Error initiating OAuth flow:", error);
      toast.error(
        error.response?.data?.detail || "Failed to initiate OAuth flow."
      );
      throw error;
    }
  },

  // Handle auth callback
  handleAuthCallback: (token) => {
    tokenManager.set(token);
  },

  // Logout
  logout: () => {
    tokenManager.remove();
  },

  // Update user mode
  updateMode: async (mode) => {
    try {
      const response = await api.put("/api/user/mode", { mode });
      return response.data;
    } catch (error) {
      console.error("Error updating user mode:", error);
      throw error;
    }
  },
};

export const fileService = {
  // Get files with filtering and pagination
  getFiles: async (params = {}) => {
    const response = await api.get("/api/files", { params });
    return response.data;
  },

  // Get file by ID
  getFile: async (fileId) => {
    const response = await api.get(`/api/files/${fileId}`);
    return response.data;
  },

  // Get file preview
  getFilePreview: async (fileId) => {
    const response = await api.get(`/api/files/${fileId}/preview`);
    return response.data;
  },

  // Delete file
  deleteFile: async (fileId) => {
    const response = await api.delete(`/api/files/${fileId}`);
    return response.data;
  },

  // Upload file
  uploadFile: async (file, provider, folderPath = "/", onProgress = null) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("provider", provider);
    formData.append("folder_path", folderPath);

    const response = await api.post("/api/files/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(progress);
        }
      },
    });

    return response.data;
  },
};

export const duplicateService = {
  // Get duplicate files
  getDuplicates: async () => {
    const response = await api.get("/api/duplicates");
    return response.data;
  },

  // Remove duplicates
  removeDuplicates: async (fileIds, keepStrategy = "newest") => {
    const response = await api.post("/api/duplicates/remove", {
      file_ids: fileIds,
      keep_strategy: keepStrategy,
    });
    return response.data;
  },
};

export const storageService = {
  // Get storage accounts
  getStorageAccounts: async () => {
    const response = await api.get("/api/storage-accounts");
    return response.data;
  },

  // Sync storage account
  syncAccount: async (accountId) => {
    const response = await api.post(`/api/storage-accounts/${accountId}/sync`);
    return response.data;
  },
};

export const statsService = {
  // Get user statistics
  getStats: async () => {
    const response = await api.get("/api/stats");
    return response.data;
  },
};

// Error handling helper
export const handleApiError = (error) => {
  if (error.response) {
    const status = error.response.status;
    const message =
      error.response.data?.detail ||
      error.response.data?.message ||
      "Unknown error";

    switch (status) {
      case 400:
        return { type: "validation", message };
      case 401:
        return { type: "auth", message: config.ERRORS.AUTH_REQUIRED };
      case 403:
        return { type: "permission", message: config.ERRORS.PERMISSION_DENIED };
      case 404:
        return { type: "not_found", message: config.ERRORS.FILE_NOT_FOUND };
      case 413:
        return {
          type: "file_too_large",
          message: config.ERRORS.FILE_TOO_LARGE,
        };
      case 429:
        return { type: "rate_limit", message: config.ERRORS.RATE_LIMIT };
      case 500:
      default:
        return { type: "server", message: config.ERRORS.SERVER_ERROR };
    }
  } else if (error.request) {
    return { type: "network", message: config.ERRORS.NETWORK_ERROR };
  } else {
    return {
      type: "unknown",
      message: error.message || "Unknown error occurred",
    };
  }
};

// Export the main API instance
export default api;
