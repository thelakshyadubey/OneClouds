import React, { useState, useEffect, useCallback } from "react"; // Import useCallback
import { useNavigate, useLocation, Link } from "react-router-dom";
import {
  FaGoogle,
  FaDropbox,
  FaMicrosoft,
  FaSync,
  FaFile,
  FaCopy,
} from "react-icons/fa";
import toast from "react-hot-toast";
import api, { authService } from "../services/api";

// Skeleton Loader for a single stat card
const StatCardSkeleton = () => (
  <div className="bg-oc-white rounded-lg shadow p-6 animate-pulse">
    <div className="flex items-center">
      <div className="flex-shrink-0 w-8 h-8 bg-gray-300 rounded-full"></div>
      <div className="ml-5 w-0 flex-1">
        <div className="h-4 bg-gray-300 rounded w-3/4 mb-2"></div>
        <div className="h-6 bg-gray-300 rounded w-1/2"></div>
      </div>
    </div>
  </div>
);

// Skeleton Loader for an account item
const AccountSkeleton = () => (
  <div className="border border-oc-steel/20 rounded-lg p-4 flex items-center justify-between animate-pulse">
    <div className="flex items-center space-x-3">
      <div className="w-8 h-8 bg-gray-300 rounded-full"></div>
      <div>
        <div className="h-4 bg-gray-300 rounded w-32 mb-2"></div>
        <div className="h-3 bg-gray-300 rounded w-48"></div>
        <div className="h-3 bg-gray-300 rounded w-24 mt-1"></div>
      </div>
    </div>
    <div className="flex items-center space-x-2">
      <div className="h-4 bg-gray-300 rounded w-16"></div>
      <div className="h-8 bg-gray-300 rounded-md w-20"></div>
      <div className="h-8 bg-gray-300 rounded-md w-24"></div>
    </div>
  </div>
);

const Dashboard = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [storageAccounts, setStorageAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState({});
  const [stats, setStats] = useState({ total_files: 0, duplicate_groups: 0 }); // New state for overall stats

  const fetchStorageAccounts = useCallback(async () => {
    try {
      const response = await api.get("/api/storage-accounts");
      setStorageAccounts(response.data);
    } catch (error) {
      console.error("Failed to fetch storage accounts:", error);
      if (error.response?.status === 401) {
        // User not authenticated, redirect to landing page or show auth buttons
      } else {
        toast.error("Failed to load storage accounts");
      }
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const response = await api.get("/api/stats");
      setStats(response.data);
    } catch (error) {
      console.error("Failed to fetch stats:", error);
      toast.error("Failed to load dashboard statistics.");
    } finally {
      setLoading(false); // Set loading to false after both fetches are complete
    }
  }, []);

  useEffect(() => {
    // Fetch both accounts and stats
    fetchStorageAccounts();
    fetchStats();
  }, [fetchStorageAccounts, fetchStats]); // Add fetchStats to dependency array

  const handleDeleteAccount = async (accountId) => {
    if (
      window.confirm(
        "Are you sure you want to remove this account and all its associated files?"
      )
    ) {
      try {
        await api.delete(`/api/storage-accounts/${accountId}`);
        toast.success("Account removed successfully!");
        fetchStorageAccounts(); // Refresh the list of accounts
      } catch (error) {
        console.error("Failed to delete storage account:", error);
        toast.error(error.response?.data?.detail || "Failed to remove account");
      }
    }
  };

  const handleConnect = async (provider) => {
    navigate(`/mode-selection?provider=${provider}`);
  };

  const handleSync = async (accountId) => {
    setSyncing({ ...syncing, [accountId]: true });
    try {
      const response = await api.post(
        `/api/storage-accounts/${accountId}/sync`
      );
      toast.success(response.data.message);
      fetchStorageAccounts(); // Refresh accounts to show updated sync time
    } catch (error) {
      console.error("Sync failed:", error);
      toast.error(error.response?.data?.error || "Sync failed");
    } finally {
      setSyncing({ ...syncing, [accountId]: false });
    }
  };

  const formatLastSync = (lastSync) => {
    if (!lastSync) return "Never synced";
    const date = new Date(lastSync);
    return date.toLocaleString();
  };

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

  const getProviderIcon = (provider) => {
    switch (provider) {
      case "google_drive":
        return <FaGoogle className="text-google" />;
      case "dropbox":
        return <FaDropbox className="text-dropbox" />;
      case "onedrive":
        return <FaMicrosoft className="text-microsoft" />;
      default:
        return <FaFile />;
    }
  };

  const getProviderName = (provider) => {
    switch (provider) {
      case "google_drive":
        return "Google Drive";
      case "dropbox":
        return "Dropbox";
      case "onedrive":
        return "OneDrive";
      default:
        return provider;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-oc-dark">Dashboard</h1>
        <p className="text-oc-steel mt-2">
          Manage your cloud storage accounts and sync your files
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        {loading ? (
          <>
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
          </>
        ) : (
          <>
            <div className="bg-oc-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <FaFile className="text-2xl text-oc-teal" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-oc-steel truncate">
                      Connected Accounts
                    </dt>
                    <dd className="text-lg font-medium text-oc-dark">
                      {storageAccounts.length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>

            <div className="bg-oc-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <FaSync className="text-2xl text-oc-teal" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-oc-steel truncate">
                      Total Files
                    </dt>
                    <dd className="text-lg font-medium text-oc-dark">
                      {stats.total_files}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>

            <div className="bg-oc-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <FaCopy className="text-2xl text-oc-teal" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-oc-steel truncate">
                      Duplicates Found
                    </dt>
                    <dd className="text-lg font-medium text-oc-dark">
                      {stats.duplicate_groups}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>

            <div className="bg-oc-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <dt className="text-sm font-medium text-oc-steel">
                    Quick Actions
                  </dt>
                </div>
                <div className="flex space-x-2">
                  <Link
                    to="/files"
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-oc-white bg-oc-teal hover:bg-oc-steel"
                  >
                    View Files
                  </Link>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Connected Accounts */}
      <div className="bg-oc-white shadow rounded-lg mb-8">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-oc-dark mb-4">
            Connected Storage Accounts
          </h3>

          {loading ? (
            <div className="grid gap-4">
              <AccountSkeleton />
              <AccountSkeleton />
            </div>
          ) : storageAccounts.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-oc-steel mb-4">
                No storage accounts connected yet.
              </p>
              <p className="text-oc-steel text-sm">
                Connect your cloud storage accounts to get started.
              </p>
            </div>
          ) : (
            <div className="grid gap-4">
              {storageAccounts.map((account) => (
                <div
                  key={account.id}
                  className="border border-oc-steel/20 rounded-lg p-4 flex items-center justify-between"
                >
                  <div className="flex items-center space-x-3">
                    <div className="text-2xl">
                      {getProviderIcon(account.provider)}
                    </div>
                    <div>
                      <h4 className="font-medium text-oc-dark">
                        {getProviderName(account.provider)}
                      </h4>
                      <p className="text-sm text-oc-steel">
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
                          {formatLastSync(account.last_sync)}
                        </span>
                      </div>
                      {account.storage_used !== undefined &&
                        account.storage_limit !== undefined && (
                          <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700 mt-2">
                            <div
                              className="h-2.5 rounded-full"
                              style={{
                                width: `${
                                  (account.storage_used /
                                    account.storage_limit) *
                                  100
                                }%`,
                                backgroundColor: `hsl(${
                                  120 -
                                  (account.storage_used /
                                    account.storage_limit) *
                                    120
                                }, 70%, 50%)`,
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
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleSync(account.id)}
                      disabled={syncing[account.id]}
                      className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-oc-white bg-oc-teal hover:bg-oc-steel disabled:opacity-50 mr-2"
                    >
                      {syncing[account.id] ? (
                        <div className="spinner mr-2"></div>
                      ) : (
                        <FaSync className="mr-2" />
                      )}
                      {syncing[account.id] ? "Syncing..." : "Sync"}
                    </button>
                    <button
                      onClick={() => handleDeleteAccount(account.id)}
                      className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-oc-white bg-red-600 hover:bg-red-700"
                    >
                      Remove Account
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Total Storage Summary */}
      {!loading && storageAccounts.length > 0 && (
        <div className="bg-oc-white shadow rounded-lg p-6 mb-8">
          <h3 className="text-lg leading-6 font-medium text-oc-dark mb-4">
            Total Storage Summary
          </h3>
          {(() => {
            // Calculate totals from storageAccounts
            const totalUsed = storageAccounts.reduce(
              (sum, acc) => sum + (acc.storage_used || 0),
              0
            );
            const totalLimit = storageAccounts.reduce(
              (sum, acc) => sum + (acc.storage_limit || 0),
              0
            );
            const usagePercentage =
              totalLimit > 0 ? (totalUsed / totalLimit) * 100 : 0;

            return (
              <>
                <div className="w-full bg-gray-200 rounded-full h-4 dark:bg-gray-700 mb-2">
                  <div
                    className="h-4 rounded-full"
                    style={{
                      width: `${usagePercentage}%`,
                      backgroundColor: `hsl(${
                        120 - usagePercentage * 1.2
                      }, 70%, 50%)`,
                    }}
                  ></div>
                </div>
                <p className="text-sm text-oc-steel">
                  Overall Usage: {formatStorageSize(totalUsed)} of{" "}
                  {formatStorageSize(totalLimit)}
                </p>
              </>
            );
          })()}
          <div className="mt-4">
            <h4 className="text-md font-medium text-oc-dark mb-2">
              Breakdown by Provider:
            </h4>
            {storageAccounts.map((account) => (
              <div
                key={account.id}
                className="flex items-center justify-between text-sm text-oc-steel mb-1"
              >
                <span>
                  {getProviderName(account.provider)} (
                  {account.mode === "metadata" ? "Metadata" : "Full Access"}):
                </span>
                <span>
                  {formatStorageSize(account.storage_used)} /{" "}
                  {formatStorageSize(account.storage_limit)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Connect New Account */}
      <div className="bg-oc-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-oc-dark mb-4">
            Connect New Storage Account
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => handleConnect("google_drive")}
              className="flex items-center justify-center px-4 py-3 border border-oc-steel/20 rounded-md shadow-sm bg-oc-white text-sm font-medium text-oc-dark hover:bg-oc-steel/10"
            >
              <FaGoogle className="text-google mr-2" />
              Google Drive
            </button>

            <button
              onClick={() => handleConnect("dropbox")}
              className="flex items-center justify-center px-4 py-3 border border-oc-steel/20 rounded-md shadow-sm bg-oc-white text-sm font-medium text-oc-dark hover:bg-oc-steel/10"
            >
              <FaDropbox className="text-dropbox mr-2" />
              Dropbox
            </button>

            <button
              onClick={() => handleConnect("onedrive")}
              className="flex items-center justify-center px-4 py-3 border border-oc-steel/20 rounded-md shadow-sm bg-oc-white text-sm font-medium text-oc-dark hover:bg-oc-steel/10"
            >
              <FaMicrosoft className="text-microsoft mr-2" />
              OneDrive
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
