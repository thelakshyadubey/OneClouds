import React, { useState, useEffect, useCallback } from "react";
import { FaTrash, FaEye, FaLock } from "react-icons/fa";
import api from "../services/api";
import FileIcon from "../components/FileIcon";
import toast from "react-hot-toast";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Checkbox,
} from "@mui/material";

// Skeleton loader for a single duplicate file item
const DuplicateFileSkeleton = () => (
  <div className="px-6 py-4 flex items-center justify-between animate-pulse">
    <div className="flex items-center">
      <div className="w-8 h-8 bg-gray-300 rounded-md"></div>
      <div className="ml-4">
        <div className="h-4 bg-gray-300 rounded w-40 mb-2"></div>
        <div className="h-3 bg-gray-300 rounded w-64"></div>
      </div>
    </div>
    <div className="h-8 bg-gray-300 rounded-md w-24"></div>
  </div>
);

// Skeleton loader for a duplicate group
const DuplicateGroupSkeleton = () => (
  <div className="bg-oc-white rounded-lg shadow overflow-hidden animate-pulse">
    <div className="px-6 py-4 bg-oc-steel/10 border-b border-oc-steel/20">
      <div className="h-6 bg-gray-300 rounded w-1/2 mb-2"></div>
      <div className="h-4 bg-gray-300 rounded w-1/3"></div>
    </div>
    <div className="divide-y divide-oc-steel/20">
      <DuplicateFileSkeleton />
      <DuplicateFileSkeleton />
      <DuplicateFileSkeleton />
    </div>
  </div>
);

const Duplicates = () => {
  const [duplicateGroups, setDuplicateGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const location = useLocation();
  const navigate = useNavigate();
  const [selectedMode, setSelectedMode] = useState(null);
  const [selectedDuplicates, setSelectedDuplicates] = useState({}); // {fileId: true/false}
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [fileToDelete, setFileToDelete] = useState(null);
  const [bulkDeleteConfirmation, setBulkDeleteConfirmation] = useState(false);
  const [showDeleteRestrictionModal, setShowDeleteRestrictionModal] =
    useState(false);
  const [fileToRestrict, setFileToRestrict] = useState(null);

  const fetchDuplicates = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get("/api/duplicates", {
        params: { mode: selectedMode },
      });
      setDuplicateGroups(response.data);
      // Initialize selectedDuplicates for all files from full_access accounts
      const initialSelected = {};
      response.data.forEach((group) => {
        group.files.forEach((file) => {
          if (file.storage_account.mode === "full_access") {
            initialSelected[file.id] = false;
          }
        });
      });
      setSelectedDuplicates(initialSelected);
    } catch (error) {
      console.error("Failed to fetch duplicates:", error);
      toast.error("Failed to load duplicates");
    } finally {
      setLoading(false);
    }
  }, [selectedMode]);

  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    const mode = queryParams.get("mode");
    if (mode) {
      setSelectedMode(mode);
    } else {
      // Default to full_access if no mode is specified
      setSelectedMode("full_access");
    }
    fetchDuplicates();
  }, [location.search, fetchDuplicates]);

  const handleCheckboxChange = (fileId) => {
    setSelectedDuplicates((prev) => ({
      ...prev,
      [fileId]: !prev[fileId],
    }));
  };

  const getSelectedFileIds = () => {
    return Object.keys(selectedDuplicates).filter(
      (fileId) => selectedDuplicates[fileId]
    );
  };

  const openDeleteConfirm = (file) => {
    // Check if file is from metadata mode account
    if (file.storage_account && file.storage_account.mode === "metadata") {
      setFileToRestrict(file);
      setShowDeleteRestrictionModal(true);
      return;
    }
    setFileToDelete(file);
    setShowDeleteConfirm(true);
  };

  const handleRemoveDuplicates = async (filesToRemove) => {
    if (!filesToRemove || filesToRemove.length === 0) return;

    const fileIds = Array.isArray(filesToRemove)
      ? filesToRemove
      : [filesToRemove.id];

    try {
      const response = await api.post("/api/duplicates/remove", {
        file_ids: fileIds,
      });
      toast.success(response.data.message);
      fetchDuplicates(); // Refresh the list
      setShowDeleteConfirm(false);
      setBulkDeleteConfirmation(false);
      setFileToDelete(null);
      setSelectedDuplicates({}); // Clear selections after deletion
    } catch (error) {
      console.error("Failed to remove duplicates:", error);
      toast.error(
        error.response?.data?.detail?.message || "Failed to remove duplicates"
      );
    }
  };

  const handleCancelDelete = () => {
    setShowDeleteConfirm(false);
    setFileToDelete(null);
    setBulkDeleteConfirmation(false);
  };

  const handlePreviewFile = async (file) => {
    // Preview is allowed for both modes - will open web_view_link
    if (file.web_view_link) {
      window.open(file.web_view_link, "_blank");
    } else {
      toast.error("Preview link not available for this file.");
    }
  };

  const handleCloseDeleteRestrictionModal = () => {
    setShowDeleteRestrictionModal(false);
    setFileToRestrict(null);
  };

  const handleSwitchToFullManagement = async () => {
    if (fileToRestrict) {
      try {
        // Call the API to get the OAuth URL with authentication
        const response = await api.get(
          `/api/auth/${fileToRestrict.storage_account.provider}`,
          {
            params: { mode: "full_access" },
          }
        );

        // Show toast notification
        toast(
          `Switching to Full Access Mode for ${fileToRestrict.storage_account.provider.replace(
            "_",
            " "
          )}. You will be redirected to re-authenticate.`,
          { duration: 4000 }
        );

        // Close the modal
        handleCloseDeleteRestrictionModal();

        // Redirect to the OAuth URL from backend response
        window.location.href = response.data.oauth_url;
      } catch (error) {
        console.error("Failed to switch mode:", error);
        toast.error(error.response?.data?.detail || "Failed to switch mode.");
      }
    }
  };

  const handleBulkDeleteClick = () => {
    const selected = getSelectedFileIds();
    if (selected.length === 0) {
      toast.error("Please select at least one duplicate file to delete.");
      return;
    }
    // Check if any selected file is from metadata mode
    const hasMetadataFile = duplicateGroups.some((group) =>
      group.files.some(
        (f) =>
          selected.includes(String(f.id)) &&
          f.storage_account.mode === "metadata"
      )
    );
    if (hasMetadataFile) {
      toast.error(
        "Cannot delete files from Metadata Mode accounts. Please deselect them or switch to Full Access Mode."
      );
      return;
    }
    setBulkDeleteConfirmation(true);
  };

  const selectedCount = getSelectedFileIds().length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-oc-dark">Duplicate Files</h1>
          <p className="text-oc-steel mt-2">
            Find and remove duplicate files across all your cloud storage
            accounts
          </p>
        </div>
        {duplicateGroups.length > 0 && selectedCount > 0 && (
          <Button
            variant="contained"
            color="error"
            onClick={handleBulkDeleteClick}
            startIcon={<FaTrash />}
            disabled={selectedCount === 0}
          >
            Delete Selected ({selectedCount})
          </Button>
        )}
      </div>

      {loading ? (
        <div className="space-y-6">
          <DuplicateGroupSkeleton />
          <DuplicateGroupSkeleton />
        </div>
      ) : duplicateGroups.length === 0 ? (
        <div className="bg-oc-white rounded-lg shadow p-12 text-center">
          <p className="text-oc-steel text-lg">No duplicate files found!</p>
          <p className="text-oc-steel mt-2">Your files are well organized.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {duplicateGroups.map((group, groupIndex) => (
            <div
              key={group.hash || groupIndex}
              className="bg-oc-white rounded-lg shadow overflow-hidden"
            >
              <div className="px-6 py-4 bg-oc-steel/10 border-b border-oc-steel/20">
                <h3 className="text-lg font-medium text-oc-dark">
                  Duplicate Group {groupIndex + 1} ({group.count} files)
                </h3>
                <p className="text-sm text-oc-steel">
                  Total wasted space:{" "}
                  {group.files && group.files.length > 1
                    ? (
                        group.files
                          .slice(1)
                          .reduce((sum, file) => sum + (file.size || 0), 0) /
                        1024 ** 3
                      ).toFixed(2)
                    : 0}{" "}
                  GB
                </p>
              </div>

              <div className="divide-y divide-oc-steel/20">
                {group.files.map((file, fileIndex) => (
                  <div
                    key={file.id}
                    className="px-6 py-4 flex items-center justify-between hover:bg-oc-steel/5"
                  >
                    <div className="flex items-center">
                      {/* Show checkbox for all files from full_access accounts */}
                      {file.storage_account.mode === "full_access" && (
                        <Checkbox
                          checked={selectedDuplicates[file.id] || false}
                          onChange={() => handleCheckboxChange(file.id)}
                          sx={{ mr: 1 }}
                        />
                      )}
                      <FileIcon file={file} mode={file.storage_account.mode} />
                      <div className="ml-4">
                        <div className="text-sm font-medium text-oc-dark">
                          {file.name}
                          <span
                            className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${
                              file.storage_account.mode === "metadata"
                                ? "bg-gray-200 text-gray-700"
                                : "bg-oc-teal/20 text-oc-navy"
                            }`}
                          >
                            {file.storage_account.mode === "metadata"
                              ? "Metadata"
                              : "Full Access"}
                          </span>
                        </div>
                        <div className="text-sm text-oc-steel">
                          {file.storage_account.account_email} •{" "}
                          {file.storage_account.provider.replace("_", " ")} •{" "}
                          {file.size_formatted} •{" "}
                          {new Date(
                            file.modified_at_source
                          ).toLocaleDateString()}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<FaEye />}
                        onClick={() => handlePreviewFile(file)}
                        disabled={file.is_folder || !file.web_view_link}
                      >
                        Preview
                      </Button>
                      <Button
                        variant="contained"
                        color="error"
                        size="small"
                        onClick={() => openDeleteConfirm(file)}
                        startIcon={
                          file.storage_account.mode === "metadata" ? (
                            <FaLock />
                          ) : (
                            <FaTrash />
                          )
                        }
                      >
                        {file.storage_account.mode === "metadata"
                          ? "Locked"
                          : "Remove"}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Single File Delete Confirmation Dialog */}
      <Dialog open={showDeleteConfirm} onClose={handleCancelDelete}>
        <DialogTitle>Confirm Deletion</DialogTitle>
        <DialogContent>
          <Typography sx={{ mb: 2 }}>
            Are you sure you want to permanently delete
            <span className="font-semibold">{fileToDelete?.name}</span>
            from your{" "}
            <span className="font-semibold">
              {fileToDelete?.storage_account.provider.replace("_", " ")}
            </span>{" "}
            account?
          </Typography>
          <Typography variant="body2" color="error">
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelDelete}>Cancel</Button>
          <Button
            onClick={() => handleRemoveDuplicates(fileToDelete)}
            color="error"
            variant="contained"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Bulk Delete Confirmation Dialog */}
      <Dialog open={bulkDeleteConfirmation} onClose={handleCancelDelete}>
        <DialogTitle>Confirm Bulk Deletion</DialogTitle>
        <DialogContent>
          <Typography sx={{ mb: 2 }}>
            Are you sure you want to permanently delete
            <span className="font-semibold">
              {selectedCount} selected duplicate files
            </span>
            ?
          </Typography>
          <Typography variant="body2" color="error">
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelDelete}>Cancel</Button>
          <Button
            onClick={() => handleRemoveDuplicates(getSelectedFileIds())}
            color="error"
            variant="contained"
          >
            Delete All Selected
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Restriction Modal */}
      <Dialog
        open={showDeleteRestrictionModal}
        onClose={handleCloseDeleteRestrictionModal}
      >
        <DialogContent sx={{ p: 4, textAlign: "center" }}>
          <FaLock className="text-5xl text-red-500 mx-auto mb-4" />
          <Typography
            variant="h5"
            component="h2"
            sx={{ color: "text.primary", mb: 2 }}
          >
            Deletion Not Available
          </Typography>
          <Typography sx={{ mb: 2 }}>
            This account is connected in{" "}
            <span className="font-semibold">Metadata Mode</span>, which doesn't
            allow file deletions.
          </Typography>
          <Typography sx={{ mb: 3 }}>
            To delete files, please switch to{" "}
            <span className="font-semibold">Full Management Mode</span>.
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={handleSwitchToFullManagement}
            sx={{ mr: 2 }}
          >
            Switch to Full Management Mode
          </Button>
          <Button
            variant="outlined"
            onClick={handleCloseDeleteRestrictionModal}
          >
            Cancel
          </Button>
          <Typography
            variant="caption"
            display="block"
            sx={{ mt: 3, color: "text.secondary" }}
          >
            Warning: Switching modes will disconnect and reconnect your account.
            Existing metadata will be preserved, but you'll need to
            re-authenticate.
          </Typography>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Duplicates;
