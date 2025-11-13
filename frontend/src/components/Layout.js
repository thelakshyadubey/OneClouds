import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  FaCloud,
  FaTachometerAlt,
  FaFile,
  FaCopy,
  FaCog,
  FaFileAlt,
  FaSync,
  FaPlusCircle,
  FaUserCircle,
  FaTimes,
} from "react-icons/fa";
import UploadModal from "./UploadModal"; // Import the new UploadModal
import api from "../services/api"; // Import API service
import toast from "react-hot-toast";
import {
  CircularProgress,
  Box,
  Typography,
  Menu,
  MenuItem,
  IconButton,
  LinearProgress,
  Button,
} from "@mui/material"; // Import Material-UI components

const Layout = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [isUploadModalOpen, setIsUploadModalOpen] = React.useState(false);
  const [isSyncingAll, setIsSyncingAll] = React.useState(false); // New state for global sync
  const [user, setUser] = React.useState(null);
  const [anchorEl, setAnchorEl] = React.useState(null); // For user menu

  const navigation = [
    { name: "Dashboard", href: "/dashboard", icon: FaTachometerAlt },
    { name: "Files", href: "/files", icon: FaFile },
    { name: "Duplicates", href: "/duplicates", icon: FaCopy },
    { name: "Large Files", href: "/large-files", icon: FaFileAlt },
    { name: "Accounts", href: "/accounts", icon: FaCloud },
    { name: "Sync Files", href: "#", icon: FaSync, action: "syncAll" }, // New: Sync All Files button
    { name: "Settings", href: "/settings", icon: FaCog },
  ];

  const isActive = (href) => {
    return location.pathname === href;
  };

  const formatBytes = (bytes, decimals = 2) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
  };

  const fetchUserProfile = React.useCallback(async () => {
    try {
      const response = await api.get("/api/user");
      setUser(response.data);
    } catch (error) {
      console.error("Failed to fetch user profile:", error);
      toast.error("Failed to load user profile.");
    }
  }, []);

  React.useEffect(() => {
    fetchUserProfile();
  }, [fetchUserProfile]);

  const handleSyncAllAccounts = async () => {
    setIsSyncingAll(true);
    toast.loading("Initiating sync for all eligible accounts...");
    try {
      const response = await api.post("/api/storage-accounts/sync-all");
      toast.dismiss();
      toast.success(
        response.data.message ||
          "All eligible accounts are syncing in the background."
      );
    } catch (error) {
      toast.dismiss();
      console.error("Failed to sync all accounts:", error);
      toast.error(
        error.response?.data?.detail ||
          "Failed to initiate sync for all accounts."
      );
    } finally {
      setIsSyncingAll(false);
    }
  };

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleSignOut = () => {
    // Clear tokens and user data
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    handleMenuClose();
    toast.success("You have been signed out.");
    // Redirect to login page
    navigate("/login");
  };

  const handleRedirectToSettings = (section) => {
    navigate("/settings", { state: { section } });
    handleMenuClose();
  };

  return (
    <div className="overall-container">
      <div className="min-h-screen bg-oc-white flex">
        {/* Left Sidebar */}
        <aside className="w-64 bg-oc-navy text-oc-white p-4 flex flex-col justify-between fixed h-full top-0 left-0 shadow-lg z-10">
          <div>
            {/* Logo */}
            <Link to="/dashboard" className="flex items-center mb-6">
              <FaCloud className="text-3xl text-oc-teal mr-2" />
              <span className="text-2xl font-bold text-oc-white">
                OneClouds
              </span>
            </Link>

            {/* Plus New Button */}
            <button
              onClick={() => setIsUploadModalOpen(true)}
              className="flex items-center justify-center w-full px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-oc-white bg-oc-teal hover:bg-oc-navy focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-oc-teal mb-6"
            >
              <FaPlusCircle className="-ml-1 mr-2 h-5 w-5" aria-hidden="true" />
              New
            </button>

            <div className="space-y-2">
              {navigation.map((item) => {
                const Icon = item.icon;
                if (item.action === "syncAll") {
                  return (
                    <button
                      key={item.name}
                      onClick={handleSyncAllAccounts}
                      disabled={isSyncingAll}
                      className={`flex items-center w-full px-3 py-2 rounded-md text-sm font-medium ${
                        isActive(item.href)
                          ? "bg-oc-teal text-oc-white"
                          : "text-oc-steel hover:bg-oc-steel/20 hover:text-oc-white"
                      } ${isSyncingAll ? "opacity-50 cursor-not-allowed" : ""}`}
                    >
                      {isSyncingAll ? (
                        <CircularProgress
                          size={20}
                          color="inherit"
                          className="mr-3"
                        />
                      ) : (
                        <Icon className="mr-3" />
                      )}
                      {isSyncingAll ? "Syncing All..." : item.name}
                    </button>
                  );
                }
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex items-center px-3 py-2 rounded-md text-sm font-medium ${
                      isActive(item.href)
                        ? "bg-oc-teal text-oc-white"
                        : "text-oc-steel hover:bg-oc-steel/20 hover:text-oc-white"
                    }`}
                  >
                    <Icon className="mr-3" />
                    {item.name}
                  </Link>
                );
              })}
            </div>
          </div>

          {/* User Account Info and Menu */}
          {user && (
            <Box
              sx={{
                mt: "auto",
                p: 2,
                borderTop: "1px solid #3A506B",
                display: "flex",
                alignItems: "center",
                cursor: "pointer",
                bgcolor: "#1C2541",
              }}
              onClick={handleMenuOpen}
            >
              <IconButton sx={{ p: 0 }}>
                <FaUserCircle className="text-3xl text-oc-white hover:text-oc-teal transition-colors" />
              </IconButton>
              <Box sx={{ ml: 1 }}>
                <Typography
                  variant="subtitle2"
                  noWrap
                  sx={{ color: "oc-white", fontWeight: "bold" }}
                >
                  {user.name || user.email}
                </Typography>
                <Typography variant="body2" noWrap sx={{ color: "oc-steel" }}>
                  {user.email}
                </Typography>
              </Box>
            </Box>
          )}
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            anchorOrigin={{
              vertical: "top",
              horizontal: "right",
            }}
            transformOrigin={{
              vertical: "bottom",
              horizontal: "left",
            }}
            PaperProps={{
              sx: {
                minWidth: 240,
                bgcolor: "#1C2541",
                color: "#ffffff",
                borderRadius: "8px",
                overflow: "hidden",
                boxShadow: "0px 4px 20px rgba(0, 0, 0, 0.3)",
                border: "1px solid #3A506B",
              },
            }}
            MenuListProps={{
              "aria-labelledby": "user-account-button",
              sx: {
                py: 0,
              },
            }}
          >
            <MenuItem
              onClick={() => handleRedirectToSettings("profile")}
              sx={{
                py: 1.5,
                px: 2,
                color: "#ffffff",
                "&:hover": { bgcolor: "#3A506B" },
              }}
            >
              <FaUserCircle className="mr-2" /> Profile
            </MenuItem>
            <MenuItem
              onClick={() => handleRedirectToSettings("account-management")}
              sx={{
                py: 1.5,
                px: 2,
                color: "#ffffff",
                "&:hover": { bgcolor: "#3A506B" },
              }}
            >
              <FaCog className="mr-2" /> Manage Account
            </MenuItem>
            <MenuItem
              onClick={() =>
                handleRedirectToSettings("profile-change-password")
              }
              sx={{
                py: 1.5,
                px: 2,
                color: "#ffffff",
                "&:hover": { bgcolor: "#3A506B" },
              }}
            >
              <FaUserCircle className="mr-2" /> Change Password
            </MenuItem>
            <MenuItem
              onClick={handleSignOut}
              sx={{
                py: 1.5,
                px: 2,
                color: "#ffffff",
                borderTop: "1px solid #3A506B",
                "&:hover": { bgcolor: "#3A506B" },
              }}
            >
              <FaTimes className="mr-2" /> Sign Out
            </MenuItem>
          </Menu>

          {/* Storage Display and Get More Storage Button */}
          {user &&
            user.total_files_count !== undefined &&
            user.total_size !== undefined && (
              <Box
                sx={{
                  mt: 4,
                  p: 2,
                  bgcolor: "#1C2541",
                  borderRadius: 2,
                  color: "oc-white",
                }}
              >
                <Typography variant="body2" sx={{ mb: 1 }}>
                  {user.total_size_formatted} of{" "}
                  {formatBytes(user.storage_limit || 0)} used
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={(user.total_size / (user.storage_limit || 1)) * 100}
                  sx={{ height: 8, borderRadius: 5, mb: 2 }}
                  color={
                    (user.total_size / (user.storage_limit || 1)) * 100 > 90
                      ? "error"
                      : (user.total_size / (user.storage_limit || 1)) * 100 > 70
                      ? "warning"
                      : "primary"
                  }
                />
                <Button
                  variant="contained"
                  sx={{
                    bgcolor: "oc-teal",
                    "&:hover": { bgcolor: "oc-steel" },
                    width: "100%",
                  }}
                  onClick={() =>
                    window.open("https://one.google.com/storage", "_blank")
                  }
                >
                  Get More Storage
                </Button>
              </Box>
            )}
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8 ml-64">{children}</main>
      </div>

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        selectedMode="full_access" // Default to full_access mode for upload
        onUploadSuccess={() => {
          /* Handle post-upload success actions, e.g., refresh file list */
        }}
      />
    </div>
  );
};

export default Layout;
