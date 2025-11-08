import React, { useState, useCallback, useEffect } from "react";
import {
  FaCloudUploadAlt,
  FaTimes,
  FaGoogle,
  FaDropbox,
  FaMicrosoft,
  FaPlusCircle,
  FaFileAlt,
} from "react-icons/fa";
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
  IconButton,
  Tooltip,
  MenuItem,
  FormControl,
  Select,
  InputLabel,
} from "@mui/material";
import { useDropzone } from "react-dropzone";
import toast from "react-hot-toast";
import api from "../services/api";
import config from "../config"; // Import the default export config

const UploadModal = ({ isOpen, onClose, onUploadSuccess }) => {
  const [selectedAccount, setSelectedAccount] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [storageAccounts, setStorageAccounts] = useState([]);
  const [loadingAccounts, setLoadingAccounts] = useState(true);
  const [uploadError, setUploadError] = useState("");

  const fetchStorageAccounts = useCallback(async () => {
    setLoadingAccounts(true);
    try {
      const response = await api.get("/api/storage-accounts");
      // Filter for full_access mode accounts
      setStorageAccounts(
        response.data.filter((account) => account.mode === "full_access")
      );
    } catch (error) {
      console.error("Failed to fetch storage accounts:", error);
      toast.error("Failed to load storage accounts.");
    } finally {
      setLoadingAccounts(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchStorageAccounts();
      setSelectedAccount("");
      setUploadProgress(0);
      setSelectedFiles([]);
      setUploadError("");
    }
  }, [isOpen, fetchStorageAccounts]);

  const onDrop = useCallback((acceptedFiles) => {
    setSelectedFiles((prev) => [
      ...prev,
      ...acceptedFiles.map((file) =>
        Object.assign(file, {
          preview: URL.createObjectURL(file),
        })
      ),
    ]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    noClick: true, // Prevent opening file dialog on click to handle it manually if needed
    multiple: true,
  });

  const handleRemoveFile = (fileName) => {
    setSelectedFiles((prev) => prev.filter((file) => file.name !== fileName));
  };

  const handleUpload = async () => {
    if (!selectedAccount) {
      setUploadError("Please select a cloud storage account.");
      return;
    }
    if (selectedFiles.length === 0) {
      setUploadError("Please select files to upload.");
      return;
    }

    setUploading(true);
    setUploadError("");
    setUploadProgress(0);

    try {
      // Find the selected storage account to get provider info
      const account = storageAccounts.find(
        (acc) => acc.id === parseInt(selectedAccount)
      );
      if (!account) {
        throw new Error("Selected storage account not found");
      }

      // Upload files sequentially
      let successCount = 0;
      let failCount = 0;

      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        const formData = new FormData();
        formData.append("file", file);
        formData.append("provider", account.provider);
        formData.append("folder_path", "/");

        console.log("=== UPLOAD DEBUG ===");
        console.log("Account:", account);
        console.log("Provider:", account.provider);
        console.log("File:", file.name);
        console.log("FormData entries:", Array.from(formData.entries()));
        console.log("==================");

        try {
          await api.post("/api/files/upload", formData, {
            headers: {
              "Content-Type": "multipart/form-data",
            },
            onUploadProgress: (progressEvent) => {
              const fileProgress = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              );
              const totalProgress = Math.round(
                ((i + fileProgress / 100) / selectedFiles.length) * 100
              );
              setUploadProgress(totalProgress);
            },
          });
          successCount++;
        } catch (fileError) {
          console.error(`Failed to upload ${file.name}:`, fileError);
          failCount++;
        }
      }

      if (successCount > 0) {
        toast.success(
          `Successfully uploaded ${successCount} file(s)${
            failCount > 0 ? `, ${failCount} failed` : ""
          }`
        );
        onClose();
        onUploadSuccess(); // Trigger a refresh in parent component
      } else {
        throw new Error("All uploads failed");
      }
    } catch (error) {
      console.error("File upload failed:", error);

      // Handle different error response formats
      let errorMessage = config.ERRORS.UPLOAD_FAILED;

      if (error.response?.data) {
        const errorData = error.response.data;

        // Handle FastAPI validation errors (array of error objects)
        if (Array.isArray(errorData.detail)) {
          errorMessage = errorData.detail
            .map((err) => {
              if (typeof err === "object" && err.msg) {
                return err.msg;
              }
              return String(err);
            })
            .join(", ");
        }
        // Handle simple string detail
        else if (typeof errorData.detail === "string") {
          errorMessage = errorData.detail;
        }
        // Handle error object with message
        else if (errorData.message) {
          errorMessage = errorData.message;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }

      setUploadError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setUploading(false);
      setSelectedFiles([]);
      setSelectedAccount("");
    }
  };

  const getProviderIcon = (providerId) => {
    const provider = config.CLOUD_PROVIDERS.find((p) => p.id === providerId);
    // Use FaGoogle, FaDropbox, FaMicrosoft directly if they are icons
    if (providerId === "google_drive" || providerId === "google_photos")
      return <FaGoogle />;
    if (providerId === "dropbox") return <FaDropbox />;
    if (providerId === "onedrive") return <FaMicrosoft />;
    return <FaCloudUploadAlt />; // Default icon
  };

  return (
    <Dialog open={isOpen} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Upload Files to Cloud Storage
        <IconButton
          aria-label="close"
          onClick={onClose}
          sx={{
            position: "absolute",
            right: 8,
            top: 8,
            color: (theme) => theme.palette.grey[500],
          }}
        >
          <FaTimes />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers sx={{ minHeight: "400px" }}>
        {loadingAccounts ? (
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              minHeight: "300px",
            }}
          >
            <CircularProgress />
            <Typography sx={{ ml: 2 }}>Loading accounts...</Typography>
          </Box>
        ) : storageAccounts.length === 0 ? (
          <Box sx={{ textAlign: "center", mt: 4 }}>
            <FaCloudUploadAlt className="text-6xl text-oc-teal mb-4" />
            <Typography variant="h6" mb={2}>
              No Full Access Cloud Accounts Connected
            </Typography>
            <Typography variant="body1" mb={3}>
              Please connect an account in 'Full Access Mode' to upload files.
            </Typography>
            <Button
              variant="contained"
              onClick={() => {
                onClose();
                // navigate('/accounts'); // Uncomment if you have a navigation prop
              }}
            >
              Connect Account
            </Button>
          </Box>
        ) : (
          <Box>
            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel id="select-account-label">
                Upload to Cloud Account
              </InputLabel>
              <Select
                labelId="select-account-label"
                id="select-account"
                value={selectedAccount}
                label="Upload to Cloud Account"
                onChange={(e) => setSelectedAccount(e.target.value)}
              >
                {storageAccounts.map((account) => (
                  <MenuItem key={account.id} value={account.id}>
                    <Box sx={{ display: "flex", alignItems: "center" }}>
                      {getProviderIcon(account.provider)}{" "}
                      <Typography sx={{ ml: 1 }}>
                        {account.provider.replace("_", " ")} (
                        {account.account_email})
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Box
              {...getRootProps()}
              sx={{
                border: "2px dashed #e0e0e0",
                borderRadius: 2,
                p: 4,
                textAlign: "center",
                cursor: "pointer",
                borderColor: isDragActive ? "primary.main" : "#e0e0e0",
                bgcolor: isDragActive ? "primary.light" : "transparent",
                transition: "border-color 0.3s, background-color 0.3s",
                mb: 3,
              }}
            >
              <input {...getInputProps()} />
              <FaCloudUploadAlt className="text-5xl text-oc-teal mb-3" />
              <Typography>
                Drag 'n' drop some files here, or click to select files
              </Typography>
              <Button
                variant="contained"
                sx={{ mt: 2 }}
                onClick={() =>
                  document.querySelector('input[type="file"]').click()
                }
              >
                Browse Files
              </Button>
            </Box>

            {selectedFiles.length > 0 && (
              <Box
                sx={{
                  mt: 3,
                  maxHeight: "200px",
                  overflowY: "auto",
                  border: "1px solid #e0e0e0",
                  borderRadius: 1,
                  p: 2,
                }}
              >
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Selected Files:
                </Typography>
                {selectedFiles.map((file, index) => (
                  <Box
                    key={index}
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      mb: 1,
                      p: 1,
                      bgcolor: "#f9f9f9",
                      borderRadius: 1,
                    }}
                  >
                    <Box sx={{ display: "flex", alignItems: "center" }}>
                      <FaFileAlt className="text-lg text-oc-steel mr-2" />
                      <Typography variant="body2" sx={{ mr: 1 }}>
                        {file.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        ({(file.size / (1024 * 1024)).toFixed(2)} MB)
                      </Typography>
                    </Box>
                    <IconButton
                      size="small"
                      onClick={() => handleRemoveFile(file.name)}
                    >
                      <FaTimes />
                    </IconButton>
                  </Box>
                ))}
              </Box>
            )}

            {uploading && (
              <Box sx={{ mt: 3, mb: 2 }}>
                <LinearProgress variant="determinate" value={uploadProgress} />
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mt: 1 }}
                >
                  {selectedFiles.length > 1
                    ? `Uploading files: ${uploadProgress}%`
                    : `Uploading: ${uploadProgress}%`}
                </Typography>
              </Box>
            )}

            {uploadError && (
              <Typography color="error" sx={{ mt: 2 }}>
                {uploadError}
              </Typography>
            )}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={uploading}>
          Cancel
        </Button>
        <Button
          onClick={handleUpload}
          variant="contained"
          disabled={uploading || !selectedAccount || selectedFiles.length === 0}
        >
          {uploading ? <CircularProgress size={24} /> : "Upload"}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default UploadModal;
