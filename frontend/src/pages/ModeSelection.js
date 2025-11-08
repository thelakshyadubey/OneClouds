import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Container, Button, Typography, Box } from "@mui/material";
import { FaLock, FaUnlockAlt, FaInfoCircle } from "react-icons/fa"; // Import icons
import { authService } from "../services/api";
import toast from "react-hot-toast";
import { useEffect } from "react";
import { tokenManager } from "../services/api";

const ModeSelection = () => {
  const navigate = useNavigate();
  const location = useLocation(); // Use useLocation to access query parameters
  const queryParams = new URLSearchParams(location.search);
  const provider = queryParams.get("provider"); // Get the provider from URL

  const handleModeSelect = async (mode) => {
    try {
      // Persist selected mode to backend
      await authService.updateMode(mode);

      if (provider) {
        // If a provider is present, initiate OAuth flow with the selected mode
        await authService.initiateAuth(provider, mode);
        // The initiateAuth function will handle the redirect to the OAuth provider
        // and then eventually back to /auth/success or /auth/error.
        // So, we don't need to navigate here if provider is present.
      } else {
        // If no provider, just navigate to dashboard after mode update
        localStorage.removeItem("showModeSelection");
        navigate("/dashboard");
      }
    } catch (err) {
      console.error("Failed to update mode or initiate OAuth:", err);
      toast.error(err.response?.data?.detail || "Failed to set mode or connect account. Please try again.");
    }
  };

  useEffect(() => {
    const showModeSelectionFlag = localStorage.getItem("showModeSelection");
    // If a provider is in the URL, we *must* stay on this page to let the user select a mode.
    // The showModeSelectionFlag is for initial registration flow, not for connecting accounts.
    if (!provider && !showModeSelectionFlag) {
      navigate("/dashboard");
    }

    // If not authenticated, redirect to login
    if (!tokenManager.get()) {
      navigate("/login");
    }
  }, [navigate, provider]); // Removed showModeSelectionFlag from dependency array as it's now internal to useEffect

  return (
    <Container
      component="main"
      maxWidth="md"
      sx={{ mt: 8, bgcolor: "background.default" }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          p: 4,
          boxShadow: 3,
          borderRadius: 2,
          bgcolor: "background.paper",
        }}
      >
        <Typography
          component="h1"
          variant="h4"
          gutterBottom
          sx={{ color: "text.primary" }}
        >
          Connect Your Cloud Storage Accounts
        </Typography>
        <Typography
          variant="body1"
          align="center"
          sx={{ mb: 4, color: "text.secondary" }}
        >
          Choose an operating mode for your cloud accounts.
        </Typography>

        <Box
          sx={{
            bgcolor: "primary.main",
            color: "primary.contrastText",
            p: 2,
            borderRadius: 1,
            mb: 4,
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <FaInfoCircle className="text-xl mr-2" />
          <Typography variant="body2" align="center">
            <strong>
              Your privacy matters. OneClouds never accesses or can view your
              file contents.
            </strong>{" "}
            In Metadata Mode we process only file metadata (names, sizes,
            timestamps); in Full Access Mode we act solely on your behalf to
            perform requested actions.
          </Typography>
        </Box>

        <Box
          sx={{
            display: "flex",
            flexDirection: { xs: "column", md: "row" },
            gap: 4,
            width: "100%",
          }}
        >
          {/* Metadata Mode Card */}
          <Box
            sx={{
              flex: 1,
              p: 3,
              border: "2px solid #5BC0BE",
              borderRadius: 2,
              textAlign: "center",
              bgcolor: "#E8F8F8",
              position: "relative",
              cursor: "pointer",
              "&:hover": { boxShadow: 6 },
            }}
            onClick={() => handleModeSelect("metadata")}
          >
            <FaLock className="text-5xl text-oc-teal mx-auto mb-3" />
            <Typography
              variant="h5"
              component="h2"
              sx={{ color: "text.primary", mb: 1 }}
            >
              Metadata Mode
            </Typography>
            <Typography variant="body2" sx={{ color: "text.secondary", mb: 2 }}>
              Fast and lightweight access to your files. OneClouds syncs only
              file names and metadata, allowing you to search and organize
              across all your cloud accounts. Note: File upload, deletion, and
              preview features are disabled in this mode.
            </Typography>
            <Box
              sx={{
                display: "inline-block",
                bgcolor: "#3A506B",
                color: "oc-white",
                px: 2,
                py: 0.5,
                borderRadius: 4,
                fontSize: "0.75rem",
                fontWeight: "bold",
              }}
            >
              View Only
            </Box>
            <Button
              variant="contained"
              color="primary"
              size="small"
              sx={{ mt: 3, width: "80%" }}
            >
              Select Metadata Mode
            </Button>
          </Box>

          {/* Full Management Mode Card */}
          <Box
            sx={{
              flex: 1,
              p: 3,
              border: "2px solid #0B132B",
              borderRadius: 2,
              textAlign: "center",
              bgcolor: "#F0F8FF",
              position: "relative",
              cursor: "pointer",
              "&:hover": { boxShadow: 6 },
            }}
            onClick={() => handleModeSelect("full_access")}
          >
            <FaUnlockAlt className="text-5xl text-oc-navy mx-auto mb-3" />
            <Typography
              variant="h5"
              component="h2"
              sx={{ color: "text.primary", mb: 1 }}
            >
              Privacy-Centric File Management Mode
            </Typography>
            <Typography variant="body2" sx={{ color: "text.secondary", mb: 2 }}>
              Complete file management across all your clouds. Upload, download,
              preview, and delete files seamlessly. OneClouds requires
              additional permissions for these operations, but your data remains
              end-to-end encrypted and completely private. We never access,
              store, or view your files—your privacy is our priority.
            </Typography>
            <Box
              sx={{
                display: "inline-block",
                bgcolor: "#5BC0BE",
                color: "oc-white",
                px: 2,
                py: 0.5,
                borderRadius: 4,
                fontSize: "0.75rem",
                fontWeight: "bold",
              }}
            >
              Full Control
            </Box>
            <Button
              variant="contained"
              color="secondary"
              size="small"
              sx={{ mt: 3, width: "80%" }}
            >
              Select Full Access Mode
            </Button>
          </Box>
        </Box>
      </Box>
    </Container>
  );
};

export default ModeSelection;
