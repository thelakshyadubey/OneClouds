import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { FaSync, FaTrash, FaExchangeAlt, FaCloud } from "react-icons/fa";
import toast from "react-hot-toast";
import api from "../services/api";
import config from "../config"; // Import the default export config
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  CircularProgress,
  LinearProgress,
  Checkbox,
  FormControlLabel,
  List,
  ListItem,
  ListItemText,
} from "@mui/material";

// Utility to get provider icon (can be moved to a shared utility or config)
const getProviderIcon = (providerId) => {
  const provider = config.CLOUD_PROVIDERS.find((p) => p.id === providerId);
  return provider ? provider.icon : <FaCloud />;
};

// Utility to get provider name (can be moved to a shared utility or config)
const getProviderName = (providerId) => {
  const provider = config.CLOUD_PROVIDERS.find((p) => p.id === providerId);
  return provider ? provider.name : providerId;
};

const formatLastSync = (lastSync) => {
  if (!lastSync) return "Never synced";

  // Ensure the date string is treated as UTC by appending 'Z' if not present
  let dateString = lastSync;
  if (!dateString.endsWith("Z") && !dateString.includes("+")) {
    dateString = dateString + "Z";
  }

  const date = new Date(dateString);

  // Format with 12-hour time and AM/PM in user's local timezone
  const options = {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  };

  return date.toLocaleString("en-US", options);
};

// Utility to format storage size (bytes to GB or MB)
const formatStorageSize = (bytes) => {
  if (!bytes || bytes === 0) return "0 MB";
  const gb = bytes / 1024 ** 3;
  if (gb >= 1) {
    return `${Math.round(gb * 100) / 100} GB`;
  } else {
    const mb = bytes / 1024 ** 2;
    return `${Math.round(mb * 100) / 100} MB`;
  }
};

const Accounts = () => {
  const navigate = useNavigate();
  const [storageAccounts, setStorageAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState({});
  const [showDisconnectConfirm, setShowDisconnectConfirm] = useState(false);
  const [accountToDisconnect, setAccountToDisconnect] = useState(null);
  const [confirmDisconnectCheckbox, setConfirmDisconnectCheckbox] =
    useState(false);
  const [showModeSwitchConfirm, setShowModeSwitchConfirm] = useState(false);
  const [accountToSwitchMode, setAccountToSwitchMode] = useState(null);
  const [newMode, setNewMode] = useState(null);

  const fetchStorageAccounts = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get("/api/storage-accounts");
      setStorageAccounts(response.data);
    } catch (error) {
      console.error("Failed to fetch storage accounts:", error);
      toast.error("Failed to load storage accounts.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStorageAccounts();
  }, [fetchStorageAccounts]);

  const handleSyncAccount = async (accountId) => {
    setSyncing((prev) => ({ ...prev, [accountId]: true }));
    try {
      await api.post(`/api/storage-accounts/${accountId}/sync`);
      toast.success("Sync initiated successfully!");
      fetchStorageAccounts(); // Refresh accounts to show updated sync time
    } catch (error) {
      console.error("Failed to sync account:", error);
      toast.error(error.response?.data?.detail || "Failed to initiate sync.");
    } finally {
      setSyncing((prev) => ({ ...prev, [accountId]: false }));
    }
  };

  const openDisconnectConfirm = (account) => {
    setAccountToDisconnect(account);
    setShowDisconnectConfirm(true);
  };

  const handleDisconnectAccount = async () => {
    if (!accountToDisconnect || !confirmDisconnectCheckbox) return;

    try {
      await api.delete(`/api/storage-accounts/${accountToDisconnect.id}`);
      toast.success(
        `${getProviderName(accountToDisconnect.provider)} account disconnected.`
      );
      fetchStorageAccounts();
      setShowDisconnectConfirm(false);
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
    setShowDisconnectConfirm(false);
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
      // In a real scenario, this would initiate an OAuth flow for re-authentication
      // For now, we simulate success and update locally
      toast.info(
        `Switching ${getProviderName(accountToSwitchMode.provider)} to ${
          newMode === "metadata" ? "Metadata Mode" : "Full Access Mode"
        }. Please re-authenticate through the provider.`
      );
      // await api.put(`/api/storage-accounts/${accountToSwitchMode.id}/mode`, { mode: newMode });
      // For now, simulate by navigating to settings page or auth callback (if re-auth needed)
      navigate("/settings", {
        state: {
          highlightAccount: accountToSwitchMode.id,
          targetMode: newMode,
        },
      });
      setShowModeSwitchConfirm(false);
      setAccountToSwitchMode(null);
      setNewMode(null);
      // After successful re-authentication, fetchStorageAccounts would be called to update UI
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

  const totalStorageUsed = storageAccounts.reduce(
    (sum, acc) => sum + (acc.storage_used || 0),
    0
  );
  const totalStorageLimit = storageAccounts.reduce(
    (sum, acc) => sum + (acc.storage_limit || 0),
    0
  );
  const overallUsagePercentage =
    totalStorageLimit > 0 ? (totalStorageUsed / totalStorageLimit) * 100 : 0;

  const getStorageBarColor = (percentage) => {
    if (percentage > 90) return "#EF4444"; // Red
    if (percentage > 70) return "#F59E0B"; // Orange
    return "#10B981"; // Green
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-oc-dark mb-6">
        Your Connected Accounts
      </h1>

      {loading ? (
        <div className="grid gap-4">
          <CircularProgress
            color="inherit"
            size={24}
            className="text-oc-teal"
          />
          <Typography variant="body1" sx={{ mt: 2, color: "text.secondary" }}>
            Loading accounts...
          </Typography>
        </div>
      ) : storageAccounts.length === 0 ? (
        <div className="bg-oc-white rounded-lg shadow p-12 text-center">
          <p className="text-oc-steel text-lg mb-4">
            No cloud storage accounts connected yet.
          </p>
          <Button
            variant="contained"
            color="primary"
            onClick={() => navigate("/dashboard")}
          >
            Connect Your First Account
          </Button>
        </div>
      ) : (
        <div className="space-y-6">
          {storageAccounts.map((account) => {
            const usagePercentage =
              account.storage_limit > 0
                ? (account.storage_used / account.storage_limit) * 100
                : 0;
            const storageBarColor = getStorageBarColor(usagePercentage);

            return (
              <div
                key={account.id}
                className="bg-oc-white rounded-lg shadow p-6 flex flex-col md:flex-row items-center justify-between border border-oc-steel/20"
              >
                <div className="flex items-center space-x-4 mb-4 md:mb-0">
                  <div className="text-4xl text-oc-navy">
                    {getProviderIcon(account.provider)}
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-oc-dark">
                      {getProviderName(account.provider)}
                    </h3>
                    <p className="text-oc-steel text-sm">
                      {account.account_email}
                    </p>
                    <div className="flex items-center mt-1">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          account.mode === "metadata"
                            ? "bg-gray-200 text-gray-700"
                            : "bg-oc-teal/20 text-oc-navy"
                        }`}
                      >
                        {account.mode === "metadata"
                          ? "Metadata Mode"
                          : "Full Access Mode"}
                      </span>
                      <span className="ml-3 text-xs text-oc-steel">
                        Last sync: {formatLastSync(account.last_sync)}
                      </span>
                    </div>
                    {account.storage_used !== undefined &&
                      account.storage_limit !== undefined && (
                        <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700 mt-2">
                          <div
                            className="h-2.5 rounded-full"
                            style={{
                              width: `${usagePercentage}%`,
                              backgroundColor: storageBarColor,
                            }}
                          ></div>
                          <p className="text-xs text-oc-steel mt-1">
                            {formatStorageSize(account.storage_used)} /{" "}
                            {formatStorageSize(account.storage_limit)} Used
                          </p>
                        </div>
                      )}
                  </div>
                </div>
                <div className="flex flex-wrap justify-center gap-3">
                  <Button
                    variant="outlined"
                    color="primary"
                    size="small"
                    onClick={() =>
                      openModeSwitchConfirm(
                        account,
                        account.mode === "metadata" ? "full_access" : "metadata"
                      )
                    }
                    startIcon={<FaExchangeAlt />}
                  >
                    Switch to{" "}
                    {account.mode === "metadata" ? "Full Access" : "Metadata"}
                  </Button>
                  <Button
                    variant="outlined"
                    color="error"
                    size="small"
                    onClick={() => openDisconnectConfirm(account)}
                    startIcon={<FaTrash />}
                  >
                    Disconnect
                  </Button>
                  <Button
                    variant="contained"
                    color="primary"
                    size="small"
                    onClick={() => handleSyncAccount(account.id)}
                    disabled={syncing[account.id]}
                    startIcon={
                      syncing[account.id] ? (
                        <CircularProgress size={16} color="inherit" />
                      ) : (
                        <FaSync />
                      )
                    }
                  >
                    {syncing[account.id] ? "Syncing..." : "Sync Now"}
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Total Storage Summary */}
      {!loading && storageAccounts.length > 0 && (
        <Box
          sx={{
            mt: 8,
            p: 4,
            bgcolor: "background.paper",
            borderRadius: 2,
            boxShadow: 3,
            border: "1px solid #e0e0e0",
          }}
        >
          <Typography
            variant="h5"
            component="h2"
            gutterBottom
            sx={{ color: "text.primary" }}
          >
            Total Storage Overview
          </Typography>
          <LinearProgress
            variant="determinate"
            value={overallUsagePercentage}
            sx={{ height: 10, borderRadius: 5, mb: 2 }}
            color={
              overallUsagePercentage > 90
                ? "error"
                : overallUsagePercentage > 70
                ? "warning"
                : "primary"
            }
          />
          <Typography variant="body1" sx={{ color: "text.secondary", mb: 3 }}>
            Overall Usage:{" "}
            {Math.round((totalStorageUsed / 1024 ** 3) * 100) / 100} GB of
            {Math.round((totalStorageLimit / 1024 ** 3) * 100) / 100} GB (
            {overallUsagePercentage.toFixed(2)}% used)
          </Typography>

          <Typography variant="h6" sx={{ color: "text.primary", mb: 2 }}>
            Breakdown by Provider:
          </Typography>
          <List>
            {storageAccounts.map((account) => (
              <ListItem key={account.id} disablePadding sx={{ mb: 1 }}>
                <Box
                  sx={{ display: "flex", alignItems: "center", width: "100%" }}
                >
                  <div className="text-xl mr-2">
                    {getProviderIcon(account.provider)}
                  </div>
                  <ListItemText
                    primary={`${getProviderName(account.provider)} (${
                      account.mode === "metadata" ? "Metadata" : "Full Access"
                    })`}
                    secondary={
                      <Typography
                        component="span"
                        variant="body2"
                        color="text.secondary"
                      >
                        {formatStorageSize(account.storage_used)} /{" "}
                        {formatStorageSize(account.storage_limit)}
                      </Typography>
                    }
                  />
                  <LinearProgress
                    variant="determinate"
                    value={
                      account.storage_limit > 0
                        ? (account.storage_used / account.storage_limit) * 100
                        : 0
                    }
                    sx={{ width: "100px", height: 6, borderRadius: 3, ml: 2 }}
                    color={
                      (account.storage_limit > 0
                        ? (account.storage_used / account.storage_limit) * 100
                        : 0) > 90
                        ? "error"
                        : (account.storage_limit > 0
                            ? (account.storage_used / account.storage_limit) *
                              100
                            : 0) > 70
                        ? "warning"
                        : "primary"
                    }
                  />
                </Box>
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      {/* Disconnect Account Confirmation Dialog */}
      <Dialog open={showDisconnectConfirm} onClose={handleCancelDisconnect}>
        <DialogTitle>Confirm Disconnect Account</DialogTitle>
        <DialogContent>
          <Typography sx={{ mb: 2 }}>
            Are you sure you want to disconnect
            <span className="font-semibold">
              {accountToDisconnect?.account_email} (
              {getProviderName(accountToDisconnect?.provider)})
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
              {getProviderName(accountToSwitchMode?.provider)})
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
            preserved, but you\'ll need to re-authenticate through the provider
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
    </div>
  );
};

export default Accounts;
