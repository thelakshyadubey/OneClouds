import React, { useState, useEffect, useCallback } from "react";
import {
  FaCog,
  FaUserCircle,
  FaSync,
  FaSignOutAlt,
  FaTimes,
} from "react-icons/fa";
import { useLocation, useNavigate } from "react-router-dom";
import api from "../services/api";
import toast from "react-hot-toast";
import {
  Box,
  Typography,
  Button,
  FormControlLabel,
  Switch,
  TextField,
  MenuItem,
  Select,
  InputLabel,
  FormControl,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Checkbox,
  CircularProgress,
} from "@mui/material";
import { FaCloud } from "react-icons/fa";

const Settings = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loadingUser, setLoadingUser] = useState(true);
  const [autoSyncEnabled, setAutoSyncEnabled] = useState(true);
  const [syncInterval, setSyncInterval] = useState(30); // minutes
  const [theme, setTheme] = useState("light");
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [language, setLanguage] = useState("en");
  const [showAccountDisconnectConfirm, setShowAccountDisconnectConfirm] =
    useState(false);
  const [accountToDisconnect, setAccountToDisconnect] = useState(null);
  const [confirmDisconnectCheckbox, setConfirmDisconnectCheckbox] =
    useState(false);
  const [showModeSwitchConfirm, setShowModeSwitchConfirm] = useState(false);
  const [accountToSwitchMode, setAccountToSwitchMode] = useState(null);
  const [newMode, setNewMode] = useState(null);
  const [defaultUploadLocation, setDefaultUploadLocation] =
    useState("__root__"); // Default to root
  const [showEmailChangeDialog, setShowEmailChangeDialog] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [currentPasswordForEmail, setCurrentPasswordForEmail] = useState("");
  const [showPasswordChangeDialog, setShowPasswordChangeDialog] =
    useState(false);
  const [currentPasswordForPassword, setCurrentPasswordForPassword] =
    useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [show2FASetupDialog, setShow2FASetupDialog] = useState(false);
  const [setup2FAPassword, setSetup2FAPassword] = useState("");
  const [twoFAQrCodeUrl, setTwoFAQrCodeUrl] = useState("");
  const [twoFAOtpInput, setTwoFAOtpInput] = useState("");
  const [twoFASecret, setTwoFASecret] = useState(""); // To store the secret temporarily for verification
  const [is2FAVerified, setIs2FAVerified] = useState(false); // To track if 2FA is in verification step
  const [trustedDevices, setTrustedDevices] = useState([]); // New state for trusted devices
  const [showRevokeDeviceConfirm, setShowRevokeDeviceConfirm] = useState(false);
  const [deviceToRevoke, setDeviceToRevoke] = useState(null);
  const [showRevokeAllSessionsConfirm, setShowRevokeAllSessionsConfirm] =
    useState(false);
  const [currentPasswordForRevokeAll, setCurrentPasswordForRevokeAll] =
    useState("");
  const [showAccountDeletionConfirm, setShowAccountDeletionConfirm] =
    useState(false); // New state for account deletion
  const [passwordForAccountDeletion, setPasswordForAccountDeletion] =
    useState("");
  const [confirmAccountDeletionCheckbox, setConfirmAccountDeletionCheckbox] =
    useState(false);

  const handleProfileUpdate = (action) => {
    if (action === "email") {
      setNewEmail(user?.email || "");
      setCurrentPasswordForEmail("");
      setShowEmailChangeDialog(true);
    } else if (action === "password") {
      setCurrentPasswordForPassword("");
      setNewPassword("");
      setConfirmNewPassword("");
      setShowPasswordChangeDialog(true);
    } else if (action === "2fa") {
      if (user?.is_2fa_enabled) {
        toast(
          "2FA is already enabled. Functionality to disable/reset not yet implemented."
        );
      } else {
        setSetup2FAPassword("");
        setTwoFAOtpInput("");
        setTwoFAQrCodeUrl("");
        setTwoFASecret("");
        setIs2FAVerified(false);
        setShow2FASetupDialog(true);
      }
    } else if (action === "account_deletion") {
      setPasswordForAccountDeletion("");
      setConfirmAccountDeletionCheckbox(false);
      setShowAccountDeletionConfirm(true);
    } else {
      toast(`'${action}' functionality not yet implemented.`);
    }
  };

  const handleInitiate2FASetup = async () => {
    try {
      const response = await api.post("/api/user/2fa/setup", {
        password: setup2FAPassword,
      });
      setTwoFASecret(response.data.otp_secret); // Store secret temporarily for verification
      setTwoFAQrCodeUrl(response.data.qr_code_url);
      setIs2FAVerified(true); // Move to the verification step
      toast.success("2FA setup initiated. Scan the QR code and enter the OTP.");
    } catch (error) {
      console.error("Failed to initiate 2FA setup:", error);
      toast.error(
        error.response?.data?.detail || "Failed to initiate 2FA setup."
      );
    }
  };

  const handleVerify2FA = async () => {
    try {
      await api.post("/api/user/2fa/verify", { otp: twoFAOtpInput });
      toast.success("2FA enabled successfully!");
      setShow2FASetupDialog(false);
      fetchUserProfile(); // Refresh user data to show 2FA status
    } catch (error) {
      console.error("Failed to verify 2FA:", error);
      toast.error(error.response?.data?.detail || "Failed to verify 2FA.");
    }
  };

  const handleSubmitEmailChange = async () => {
    try {
      await api.put("/api/user/email", {
        new_email: newEmail,
        current_password: currentPasswordForEmail,
      });
      toast.success(
        "Email change initiated. Please check your new email for verification and re-login."
      );
      setShowEmailChangeDialog(false);
      // Force logout after email change
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
      navigate("/login"); // Redirect to login page
    } catch (error) {
      console.error("Failed to change email:", error);
      toast.error(error.response?.data?.detail || "Failed to change email.");
    }
  };

  const handleSubmitPasswordChange = async () => {
    if (newPassword !== confirmNewPassword) {
      toast.error("New password and confirmation do not match.");
      return;
    }
    try {
      await api.put("/api/user/password", {
        current_password: currentPasswordForPassword,
        new_password: newPassword,
        confirm_new_password: confirmNewPassword,
      });
      toast.success(
        "Password updated successfully. You have been logged out from all devices."
      );
      setShowPasswordChangeDialog(false);
      // Force logout after password change
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
      navigate("/login"); // Redirect to login page
    } catch (error) {
      console.error("Failed to change password:", error);
      toast.error(error.response?.data?.detail || "Failed to change password.");
    }
  };

  const fetchUserProfile = useCallback(async () => {
    setLoadingUser(true);
    try {
      const response = await api.get("/api/user");
      setUser(response.data);
      const userPreferences = response.data.preferences; // Access the nested preferences object
      setAutoSyncEnabled(userPreferences?.auto_sync_enabled ?? true);
      setSyncInterval(userPreferences?.sync_interval_minutes ?? 30);
      setTheme(userPreferences?.theme ?? "light");
      setNotificationsEnabled(userPreferences?.notifications_enabled ?? true);
      setLanguage(userPreferences?.language ?? "en");
      setDefaultUploadLocation(
        userPreferences?.default_upload_location ?? "__root__"
      ); // Load default upload location

      // Fetch trusted devices
      const devicesResponse = await api.get("/api/auth/devices");
      setTrustedDevices(devicesResponse.data);
    } catch (error) {
      console.error("Failed to fetch user profile or preferences:", error);
      toast.error("Failed to load user settings.");
    } finally {
      setLoadingUser(false);
    }
  }, []);

  useEffect(() => {
    fetchUserProfile();
  }, [fetchUserProfile]);

  useEffect(() => {
    if (
      location.state?.highlightAccount &&
      location.state?.targetMode &&
      user?.storage_accounts
    ) {
      // Find the actual account by ID from the user's storage accounts
      const account = user.storage_accounts.find(
        (acc) => acc.id === location.state.highlightAccount
      );

      if (account) {
        // Use the actual account data
        setAccountToSwitchMode(account);
        setNewMode(location.state.targetMode);
        setShowModeSwitchConfirm(true);
      }

      // Clear state so it doesn't re-trigger
      window.history.replaceState({}, document.title);
    }
  }, [location.state, user]);

  const handleAutoSyncToggle = async () => {
    const newValue = !autoSyncEnabled;
    setAutoSyncEnabled(newValue);
    try {
      await api.put("/api/user/preferences", { auto_sync_enabled: newValue });
      toast.success(newValue ? "Auto-sync enabled." : "Auto-sync disabled.");
    } catch (error) {
      console.error("Failed to update auto-sync preference:", error);
      toast.error("Failed to update auto-sync preference.");
      setAutoSyncEnabled(!newValue); // Revert on error
    }
  };

  const handleSyncIntervalChange = async (e) => {
    const newValue = e.target.value;
    setSyncInterval(newValue);
    try {
      await api.put("/api/user/preferences", {
        sync_interval_minutes: newValue,
      });
      toast.success("Sync interval updated.");
    } catch (error) {
      console.error("Failed to update sync interval:", error);
      toast.error("Failed to update sync interval.");
      fetchUserProfile(); // Revert on error
    }
  };

  const handleThemeChange = async (e) => {
    const newValue = e.target.value;
    setTheme(newValue);
    try {
      await api.put("/api/user/preferences", { theme: newValue });
      toast.success("Theme updated.");
      // Apply theme change to UI (e.g., update a CSS class on body or use context)
    } catch (error) {
      console.error("Failed to update theme preference:", error);
      toast.error("Failed to update theme.");
      fetchUserProfile(); // Revert on error
    }
  };

  const handleNotificationsToggle = async () => {
    const newValue = !notificationsEnabled;
    setNotificationsEnabled(newValue);
    try {
      await api.put("/api/user/preferences", {
        notifications_enabled: newValue,
      });
      toast.success(
        newValue ? "Notifications enabled." : "Notifications disabled."
      );
    } catch (error) {
      console.error("Failed to update notification preference:", error);
      toast.error("Failed to update notifications preference.");
      setNotificationsEnabled(!newValue); // Revert on error
    }
  };

  const handleLanguageChange = async (e) => {
    const newValue = e.target.value;
    setLanguage(newValue);
    try {
      await api.put("/api/user/preferences", { language: newValue });
      toast.success("Language updated.");
    } catch (error) {
      console.error("Failed to update language preference:", error);
      toast.error("Failed to update language.");
      fetchUserProfile(); // Revert on error
    }
  };

  const handleDefaultUploadLocationChange = async (e) => {
    const newValue = e.target.value;
    setDefaultUploadLocation(newValue);
    try {
      await api.put("/api/user/preferences", {
        default_upload_location: newValue,
      });
      toast.success("Default upload location updated.");
    } catch (error) {
      console.error("Failed to update default upload location:", error);
      toast.error("Failed to update default upload location.");
      fetchUserProfile(); // Revert on error
    }
  };

  const openAccountDisconnectConfirm = (account) => {
    setAccountToDisconnect(account);
    setShowAccountDisconnectConfirm(true);
  };

  const handleDisconnectAccount = async () => {
    if (!accountToDisconnect || !confirmDisconnectCheckbox) return;

    try {
      await api.delete(`/api/storage-accounts/${accountToDisconnect.id}`);
      toast.success(
        `${accountToDisconnect.provider.replace(
          "_",
          " "
        )} account disconnected.`
      );
      fetchUserProfile(); // Refresh user accounts after disconnect
      setShowAccountDisconnectConfirm(false);
      setAccountToDisconnect(null);
      setConfirmDisconnectCheckbox(false);
    } catch (error) {
      console.error("Failed to disconnect account:", error);
      toast.error(
        error.response?.data?.detail || "Failed to disconnect account."
      );
    }
  };

  const handleCancelDisconnect = () => {
    setShowAccountDisconnectConfirm(false);
    setAccountToDisconnect(null);
    setConfirmDisconnectCheckbox(false);
  };

  const openModeSwitchConfirm = (account, mode) => {
    setAccountToSwitchMode(account);
    setNewMode(mode);
    setShowModeSwitchConfirm(true);
  };

  const handleSwitchMode = async () => {
    if (!accountToSwitchMode || !newMode) return;

    try {
      // Call the API to get the OAuth URL with authentication
      const response = await api.get(
        `/api/auth/${accountToSwitchMode.provider}`,
        {
          params: { mode: newMode },
        }
      );

      // Show toast notification
      toast(
        `Initiating mode switch for ${accountToSwitchMode.provider.replace(
          "_",
          " "
        )} to ${
          newMode === "metadata" ? "Metadata Mode" : "Full Access Mode"
        }. You will be redirected to re-authenticate.`,
        {
          duration: 4000,
        }
      );

      // Redirect to the OAuth URL from backend response
      window.location.href = response.data.oauth_url;

      // Close the dialog immediately after redirect to prevent user from interacting further
      setShowModeSwitchConfirm(false);
      setAccountToSwitchMode(null);
      setNewMode(null);
    } catch (error) {
      console.error("Failed to switch mode:", error);
      toast.error(error.response?.data?.detail || "Failed to switch mode.");
    }
  };

  const handleCancelModeSwitch = () => {
    setShowModeSwitchConfirm(false);
    setAccountToSwitchMode(null);
    setNewMode(null);
  };

  const openRevokeDeviceConfirm = (device) => {
    setDeviceToRevoke(device);
    setShowRevokeDeviceConfirm(true);
  };

  const handleRevokeDevice = async () => {
    if (!deviceToRevoke) return;
    try {
      await api.delete(`/api/auth/devices/${deviceToRevoke.id}`);
      toast.success("Device revoked successfully.");
      fetchUserProfile(); // Refresh the list of trusted devices
      setShowRevokeDeviceConfirm(false);
      setDeviceToRevoke(null);
    } catch (error) {
      console.error("Failed to revoke device:", error);
      toast.error(error.response?.data?.detail || "Failed to revoke device.");
    }
  };

  const handleCancelRevokeDevice = () => {
    setShowRevokeDeviceConfirm(false);
    setDeviceToRevoke(null);
  };

  const openRevokeAllSessionsConfirm = () => {
    setCurrentPasswordForRevokeAll("");
    setShowRevokeAllSessionsConfirm(true);
  };

  const handleRevokeAllSessions = async () => {
    try {
      await api.delete("/api/user/sessions/all", {
        data: { current_password: currentPasswordForRevokeAll },
      }); // Use data for DELETE with body
      toast.success(
        "All sessions and trusted devices revoked. You will be logged out."
      );
      setShowRevokeAllSessionsConfirm(false);
      // Force logout after revoking all sessions
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
      navigate("/login"); // Redirect to login page
    } catch (error) {
      console.error("Failed to revoke all sessions:", error);
      toast.error(
        error.response?.data?.detail || "Failed to revoke all sessions."
      );
    }
  };

  const handleCancelRevokeAllSessions = () => {
    setShowRevokeAllSessionsConfirm(false);
    setCurrentPasswordForRevokeAll("");
  };

  const handleDeleteAccount = async () => {
    if (!confirmAccountDeletionCheckbox) {
      toast.error("Please confirm you understand the irreversible action.");
      return;
    }
    try {
      // API call to delete user account
      // This endpoint needs to be created in the backend
      await api.delete("/api/user", {
        data: { current_password: passwordForAccountDeletion },
      });
      toast.success(
        "Your account has been successfully deleted. You will be logged out."
      );
      setShowAccountDeletionConfirm(false);
      // Clear tokens and redirect to landing/login page
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
      navigate("/"); // Or '/login' if a dedicated login page exists
    } catch (error) {
      console.error("Failed to delete account:", error);
      toast.error(error.response?.data?.detail || "Failed to delete account.");
    }
  };

  const handleCancelAccountDeletion = () => {
    setShowAccountDeletionConfirm(false);
    setPasswordForAccountDeletion("");
    setConfirmAccountDeletionCheckbox(false);
  };

  if (loadingUser) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 text-center">
        <CircularProgress className="text-oc-teal" />
        <Typography sx={{ mt: 2, color: "text.secondary" }}>
          Loading settings...
        </Typography>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-oc-dark">Settings</h1>
        <p className="text-oc-steel mt-2">
          Manage your account and application preferences
        </p>
      </div>

      {/* User Profile Section */}
      <Box
        sx={{
          bgcolor: "background.paper",
          p: 4,
          borderRadius: 2,
          boxShadow: 1,
          mb: 4,
        }}
      >
        <Typography
          variant="h5"
          sx={{
            mb: 3,
            color: "text.primary",
            display: "flex",
            alignItems: "center",
          }}
        >
          <FaUserCircle className="mr-2 text-oc-steel" /> User Profile
        </Typography>
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle1" sx={{ color: "text.secondary" }}>
            Email:
          </Typography>
          <Typography
            variant="body1"
            sx={{ color: "text.primary", fontWeight: "medium" }}
          >
            {user?.email}
          </Typography>
        </Box>
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" sx={{ color: "text.secondary" }}>
            Name:
          </Typography>
          <Typography
            variant="body1"
            sx={{ color: "text.primary", fontWeight: "medium" }}
          >
            {user?.name || "N/A"}
          </Typography>
        </Box>
        <Button
          variant="outlined"
          sx={{ mr: 2 }}
          onClick={() => handleProfileUpdate("password")}
        >
          Change Password
        </Button>
        <Button
          variant="contained"
          color="error"
          sx={{ ml: 2 }}
          onClick={() => handleProfileUpdate("account_deletion")}
        >
          Delete Account
        </Button>
      </Box>

      {/* Application Preferences Section */}
      <Box
        sx={{
          bgcolor: "background.paper",
          p: 4,
          borderRadius: 2,
          boxShadow: 1,
          mb: 4,
        }}
      >
        <Typography
          variant="h5"
          sx={{
            mb: 3,
            color: "text.primary",
            display: "flex",
            alignItems: "center",
          }}
        >
          <FaCog className="mr-2 text-oc-steel" /> Application Preferences
        </Typography>

        <Box sx={{ mb: 3 }}>
          <FormControlLabel
            control={
              <Switch
                checked={autoSyncEnabled}
                onChange={handleAutoSyncToggle}
                color="primary"
              />
            }
            label={
              <Typography variant="subtitle1" sx={{ color: "text.primary" }}>
                Enable Auto-Sync
              </Typography>
            }
          />
          <Typography variant="body2" sx={{ color: "text.secondary", ml: 4 }}>
            Automatically synchronize files from your connected cloud accounts.
          </Typography>
        </Box>

        {autoSyncEnabled && (
          <Box sx={{ mb: 3, ml: 4 }}>
            <FormControl variant="outlined" size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Sync Interval</InputLabel>
              <Select
                value={syncInterval}
                onChange={handleSyncIntervalChange}
                label="Sync Interval"
              >
                <MenuItem value={15}>Every 15 minutes</MenuItem>
                <MenuItem value={30}>Every 30 minutes</MenuItem>
                <MenuItem value={60}>Every hour</MenuItem>
                <MenuItem value={360}>Every 6 hours</MenuItem>
                <MenuItem value={720}>Every 12 hours</MenuItem>
                <MenuItem value={1440}>Every 24 hours</MenuItem>
              </Select>
            </FormControl>
            <Typography variant="body2" sx={{ color: "text.secondary", mt: 1 }}>
              How often OneClouds should check for new or updated files.
            </Typography>
          </Box>
        )}

        <Box sx={{ mb: 3 }}>
          <FormControl
            variant="outlined"
            size="small"
            sx={{ minWidth: 200, mr: 3 }}
          >
            <InputLabel>Default Upload Location</InputLabel>
            <Select
              value={defaultUploadLocation}
              onChange={handleDefaultUploadLocationChange}
              label="Default Upload Location"
            >
              {/* Dynamically load connected accounts here, filtered by full_access mode */}
              {/* For now, placeholder options */}
              <MenuItem value="__root__">My Drive (Root)</MenuItem>
              <MenuItem value="__last_used__">Last Used Location</MenuItem>
              {/* Example: <MenuItem value="{account_id}">Google Drive ({account_email})</MenuItem> */}
            </Select>
          </FormControl>
          <FormControl variant="outlined" size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Theme</InputLabel>
            <Select value={theme} onChange={handleThemeChange} label="Theme">
              <MenuItem value="light">Light</MenuItem>
              <MenuItem value="dark">Dark</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <Box>
          <FormControlLabel
            control={
              <Switch
                checked={notificationsEnabled}
                onChange={handleNotificationsToggle}
                color="primary"
              />
            }
            label={
              <Typography variant="subtitle1" sx={{ color: "text.primary" }}>
                Enable Notifications
              </Typography>
            }
          />
          <Typography variant="body2" sx={{ color: "text.secondary", ml: 4 }}>
            Receive alerts for sync status, new files, and other important
            events.
          </Typography>
        </Box>
      </Box>

      {/* Account Disconnect Confirmation Dialog */}
      <Dialog
        open={showAccountDisconnectConfirm}
        onClose={handleCancelDisconnect}
      >
        <DialogTitle>Confirm Disconnect Account</DialogTitle>
        <DialogContent>
          <Typography sx={{ mb: 2 }}>
            Are you sure you want to disconnect
            <span className="font-semibold">
              {accountToDisconnect?.account_email} (
              {accountToDisconnect?.provider.replace("_", " ")})
            </span>
            ? Your files will remain in the cloud, but they won't be accessible
            through OneClouds.
          </Typography>
          <FormControlLabel
            control={
              <Checkbox
                checked={confirmDisconnectCheckbox}
                onChange={(e) => setConfirmDisconnectCheckbox(e.target.checked)}
                name="confirmDisconnect"
                color="primary"
              />
            }
            label="I understand this action cannot be undone."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelDisconnect}>Cancel</Button>
          <Button
            onClick={handleDisconnectAccount}
            color="error"
            variant="contained"
            disabled={!confirmDisconnectCheckbox}
          >
            Disconnect
          </Button>
        </DialogActions>
      </Dialog>

      {/* Mode Switch Confirmation Dialog */}
      <Dialog open={showModeSwitchConfirm} onClose={handleCancelModeSwitch}>
        <DialogTitle>Confirm Mode Switch</DialogTitle>
        <DialogContent>
          <Typography sx={{ mb: 2 }}>
            Are you sure you want to switch
            <span className="font-semibold">
              {accountToSwitchMode?.account_email} (
              {accountToSwitchMode?.provider.replace("_", " ")})
            </span>
            to{" "}
            <span className="font-semibold">
              {newMode === "metadata" ? "Metadata Mode" : "Full Access Mode"}
            </span>
            ?
          </Typography>
          <Typography variant="body2" color="error" sx={{ mb: 2 }}>
            Warning: Changing modes requires re-authentication and may
            temporarily disconnect your account. Existing metadata will be
            preserved, but you'll need to re-authenticate through the provider
            after confirming.
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Current Mode:{" "}
            <span className="font-semibold">
              {accountToSwitchMode?.mode === "metadata"
                ? "Metadata Mode"
                : "Full Access Mode"}
            </span>
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            New Mode:{" "}
            <span className="font-semibold">
              {newMode === "metadata"
                ? "Metadata Mode (View Only)"
                : "Full Access Mode (Full Control)"}
            </span>
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelModeSwitch}>Cancel</Button>
          <Button
            onClick={handleSwitchMode}
            color="primary"
            variant="contained"
          >
            Continue & Re-authenticate
          </Button>
        </DialogActions>
      </Dialog>

      {/* Email Change Dialog */}
      <Dialog
        open={showEmailChangeDialog}
        onClose={() => setShowEmailChangeDialog(false)}
      >
        <DialogTitle>Change Email</DialogTitle>
        <DialogContent>
          <Typography sx={{ mb: 2 }}>
            Enter your new email address and current password to change your
            email.
          </Typography>
          <TextField
            autoFocus
            margin="dense"
            id="new-email"
            label="New Email Address"
            type="email"
            fullWidth
            variant="outlined"
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            id="current-password-email"
            label="Current Password"
            type="password"
            fullWidth
            variant="outlined"
            value={currentPasswordForEmail}
            onChange={(e) => setCurrentPasswordForEmail(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowEmailChangeDialog(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmitEmailChange}
            color="primary"
            variant="contained"
          >
            Change Email
          </Button>
        </DialogActions>
      </Dialog>

      {/* Password Change Dialog */}
      <Dialog
        open={showPasswordChangeDialog}
        onClose={() => setShowPasswordChangeDialog(false)}
      >
        <DialogTitle>Change Password</DialogTitle>
        <DialogContent>
          <Typography sx={{ mb: 2 }}>
            Enter your current password and a new password.
          </Typography>
          <TextField
            autoFocus
            margin="dense"
            id="current-password-password"
            label="Current Password"
            type="password"
            fullWidth
            variant="outlined"
            value={currentPasswordForPassword}
            onChange={(e) => setCurrentPasswordForPassword(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            id="new-password"
            label="New Password"
            type="password"
            fullWidth
            variant="outlined"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            id="confirm-new-password"
            label="Confirm New Password"
            type="password"
            fullWidth
            variant="outlined"
            value={confirmNewPassword}
            onChange={(e) => setConfirmNewPassword(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowPasswordChangeDialog(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmitPasswordChange}
            color="primary"
            variant="contained"
          >
            Change Password
          </Button>
        </DialogActions>
      </Dialog>

      {/* 2FA Setup Dialog */}
      <Dialog
        open={show2FASetupDialog}
        onClose={() => setShow2FASetupDialog(false)}
      >
        <DialogTitle>
          {is2FAVerified ? "Verify 2FA" : "Setup Two-Factor Authentication"}
        </DialogTitle>
        <DialogContent>
          {!is2FAVerified ? (
            <Box>
              <Typography sx={{ mb: 2 }}>
                Enter your current password to initiate Two-Factor
                Authentication setup.
              </Typography>
              <TextField
                autoFocus
                margin="dense"
                id="2fa-password"
                label="Current Password"
                type="password"
                fullWidth
                variant="outlined"
                value={setup2FAPassword}
                onChange={(e) => setSetup2FAPassword(e.target.value)}
              />
            </Box>
          ) : (
            <Box sx={{ textAlign: "center" }}>
              <Typography sx={{ mb: 2 }}>
                Scan the QR code with your authenticator app (e.g., Google
                Authenticator) and enter the 6-digit code below.
              </Typography>
              {twoFAQrCodeUrl && (
                <img
                  src={twoFAQrCodeUrl}
                  alt="QR Code"
                  style={{ width: 200, height: 200, margin: "0 auto 16px" }}
                />
              )}
              <Typography
                variant="body2"
                sx={{ mb: 2, color: "text.secondary" }}
              >
                Your secret key:{" "}
                <span className="font-mono font-semibold text-oc-teal">
                  {twoFASecret}
                </span>{" "}
                (manual entry)
              </Typography>
              <TextField
                margin="dense"
                id="2fa-otp"
                label="6-digit OTP"
                type="text"
                fullWidth
                variant="outlined"
                value={twoFAOtpInput}
                onChange={(e) => setTwoFAOtpInput(e.target.value)}
                inputProps={{ maxLength: 6, pattern: "[0-9]{6}" }}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShow2FASetupDialog(false)}>Cancel</Button>
          {!is2FAVerified ? (
            <Button
              onClick={handleInitiate2FASetup}
              color="primary"
              variant="contained"
              disabled={!setup2FAPassword}
            >
              Initiate Setup
            </Button>
          ) : (
            <Button
              onClick={handleVerify2FA}
              color="primary"
              variant="contained"
              disabled={twoFAOtpInput.length !== 6}
            >
              Verify & Enable 2FA
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Revoke Device Confirmation Dialog */}
      <Dialog open={showRevokeDeviceConfirm} onClose={handleCancelRevokeDevice}>
        <DialogTitle>Confirm Device Revocation</DialogTitle>
        <DialogContent>
          <Typography sx={{ mb: 2 }}>
            Are you sure you want to revoke access for the device
            <span className="font-semibold">
              {deviceToRevoke?.name || "Unknown Device"}
            </span>
            ?
          </Typography>
          <Typography variant="body2" color="error">
            This device will be logged out and will need to re-authenticate.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelRevokeDevice}>Cancel</Button>
          <Button
            onClick={handleRevokeDevice}
            color="error"
            variant="contained"
          >
            Revoke Device
          </Button>
        </DialogActions>
      </Dialog>

      {/* Revoke All Sessions Confirmation Dialog */}
      <Dialog
        open={showRevokeAllSessionsConfirm}
        onClose={handleCancelRevokeAllSessions}
      >
        <DialogTitle>Confirm Revoke All Sessions</DialogTitle>
        <DialogContent>
          <Typography sx={{ mb: 2 }}>
            Are you sure you want to revoke all active sessions and trusted
            devices? You will be logged out from all devices, including this
            one.
          </Typography>
          <Typography variant="body2" color="error" sx={{ mb: 2 }}>
            This action cannot be undone and requires your current password for
            confirmation.
          </Typography>
          <TextField
            autoFocus
            margin="dense"
            id="revoke-all-password"
            label="Current Password"
            type="password"
            fullWidth
            variant="outlined"
            value={currentPasswordForRevokeAll}
            onChange={(e) => setCurrentPasswordForRevokeAll(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelRevokeAllSessions}>Cancel</Button>
          <Button
            onClick={handleRevokeAllSessions}
            color="error"
            variant="contained"
            disabled={!currentPasswordForRevokeAll}
          >
            Revoke All
          </Button>
        </DialogActions>
      </Dialog>

      {/* Account Deletion Confirmation Dialog */}
      <Dialog
        open={showAccountDeletionConfirm}
        onClose={handleCancelAccountDeletion}
      >
        <DialogTitle>Confirm Account Deletion</DialogTitle>
        <DialogContent>
          <Typography sx={{ mb: 2 }}>
            You are about to permanently delete your OneClouds account. This
            action is irreversible and will remove all your data, including
            connected cloud accounts and file metadata.
          </Typography>
          <Typography variant="body2" color="error" sx={{ mb: 2 }}>
            To confirm this action, please enter your current password and check
            the confirmation box.
          </Typography>
          <TextField
            autoFocus
            margin="dense"
            id="delete-account-password"
            label="Current Password"
            type="password"
            fullWidth
            variant="outlined"
            value={passwordForAccountDeletion}
            onChange={(e) => setPasswordForAccountDeletion(e.target.value)}
            sx={{ mb: 2 }}
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={confirmAccountDeletionCheckbox}
                onChange={(e) =>
                  setConfirmAccountDeletionCheckbox(e.target.checked)
                }
                name="confirmAccountDeletion"
                color="primary"
              />
            }
            label="I understand that deleting my account is a permanent and irreversible action."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelAccountDeletion}>Cancel</Button>
          <Button
            onClick={handleDeleteAccount}
            color="error"
            variant="contained"
            disabled={
              !passwordForAccountDeletion || !confirmAccountDeletionCheckbox
            }
          >
            Delete Account
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default Settings;
