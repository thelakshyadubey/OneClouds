import React, { useState, useEffect, useCallback } from "react"; // Import useCallback
import { FaSearch, FaEye } from "react-icons/fa";
import api from "../services/api";
import FileIcon from "../components/FileIcon";
import { useLocation, useNavigate } from "react-router-dom";
import toast from "react-hot-toast"; // Corrected import for toast
import { IconButton, Menu, MenuItem } from "@mui/material";
import { FaDownload, FaTrash, FaInfoCircle, FaEllipsisV } from "react-icons/fa"; // Import new icons

// Skeleton loader for a single file row
const FileRowSkeleton = () => (
  <tr className="animate-pulse">
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="flex items-center">
        <div className="w-8 h-8 bg-gray-300 rounded-md"></div>
        <div className="ml-4">
          <div className="h-4 bg-gray-300 rounded w-48 mb-2"></div>
          <div className="h-3 bg-gray-300 rounded w-32"></div>
        </div>
      </div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-300 rounded w-20"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-300 rounded w-24"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-300 rounded w-20"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-300 rounded w-16"></div>
    </td>
  </tr>
);

const Files = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState("modified_at_source");
  const [sortOrder, setSortOrder] = useState("desc");
  const [providerFilter, setProviderFilter] = useState("");
  const location = useLocation(); // Initialize useLocation
  const navigate = useNavigate(); // Initialize useNavigate
  const [selectedMode, setSelectedMode] = useState(null); // State to store the selected mode
  const [anchorEl, setAnchorEl] = useState(null); // For the action menu
  const [selectedFile, setSelectedFile] = useState(null); // File for which the menu is open
  const [showDeleteRestrictionModal, setShowDeleteRestrictionModal] =
    useState(false); // New state for delete restriction modal

  const fetchFiles = useCallback(async () => {
    // Wrap in useCallback
    setLoading(true);
    try {
      const params = {
        page: currentPage,
        per_page: 25,
        sort_by: sortBy,
        sort_order: sortOrder,
      };

      if (searchTerm) params.search = searchTerm;
      if (providerFilter) params.provider = providerFilter;
      if (selectedMode) params.mode = selectedMode; // Pass the selected mode to the backend

      const response = await api.get("/api/files", { params });
      setFiles(response.data.files);
      setTotalPages(response.data.pages);
    } catch (error) {
      console.error("Failed to fetch files:", error);
    } finally {
      setLoading(false);
    }
  }, [
    currentPage,
    searchTerm,
    sortBy,
    sortOrder,
    providerFilter,
    selectedMode,
  ]); // Add all dependencies

  useEffect(() => {
    // Extract mode from URL query parameter
    const queryParams = new URLSearchParams(location.search);
    const mode = queryParams.get("mode");
    if (mode) {
      setSelectedMode(mode);
    } else {
      // If no mode is provided, show all files (set mode to null/empty)
      setSelectedMode(null);
    }
    fetchFiles();
  }, [location.search, fetchFiles]); // Add fetchFiles to dependency array

  const handlePreview = (file) => {
    // Preview is allowed for both modes - opens in new tab
    if (file.web_view_link) {
      window.open(file.web_view_link, "_blank");
    } else {
      toast.error("Preview link not available for this file.");
    }
  };

  const handleDownload = (file) => {
    if (file.storage_account && file.storage_account.mode === "metadata") {
      toast.error("File download is not available in Metadata Mode.");
      return;
    }
    if (file.download_link) {
      window.open(file.download_link, "_blank");
    } else {
      toast.error("Download link not available.");
    }
  };

  const handleDelete = async (file) => {
    // Check if the file belongs to a metadata mode account
    if (file.storage_account && file.storage_account.mode === "metadata") {
      setSelectedFile(file); // Set the file to show in the modal
      setShowDeleteRestrictionModal(true); // Open the modal
      return;
    }
    if (
      window.confirm(
        `Are you sure you want to delete ${
          file.name
        } from ${file.storage_account.provider.replace(
          "_",
          " "
        )}? This action cannot be undone.`
      )
    ) {
      try {
        await api.delete(`/api/files/${file.id}`);
        toast.success("File deleted successfully!");
        fetchFiles(); // Refresh the list
      } catch (error) {
        console.error("Failed to delete file:", error);
        toast.error(error.response?.data?.detail || "Failed to delete file.");
      }
    }
  };

  const handleCloseDeleteRestrictionModal = () => {
    setShowDeleteRestrictionModal(false);
    setSelectedFile(null);
  };

  const handleSwitchToDeleteFullManagement = () => {
    handleCloseDeleteRestrictionModal();
    toast.info(
      "Redirecting to settings to switch to Full Management Mode. You will need to re-authenticate."
    );
    navigate("/settings");
  };

  const handleFileDetails = (file) => {
    // Implement modal or new page for file details
    toast.info(`Showing details for ${file.name}`);
    console.log("File details:", file);
  };

  const handleMenuClick = (event, file) => {
    setAnchorEl(event.currentTarget);
    setSelectedFile(file);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedFile(null);
  };

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-oc-dark">All Files</h1>
        <p className="text-oc-steel mt-2">
          Browse and manage files from all your cloud storage accounts
        </p>
      </div>

      {/* Search and Filters */}
      <div className="bg-oc-white rounded-lg shadow mb-6 p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <FaSearch className="absolute left-3 top-3 text-oc-steel" />
              <input
                type="text"
                placeholder="Search files..."
                className="w-full pl-10 pr-4 py-2 border border-oc-steel/20 rounded-md text-oc-dark focus:ring-oc-teal focus:border-oc-teal"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          <select
            className="px-3 py-2 border border-oc-steel/20 rounded-md bg-oc-white text-oc-dark focus:ring-oc-teal focus:border-oc-teal"
            value={providerFilter}
            onChange={(e) => setProviderFilter(e.target.value)}
          >
            <option value="">All Providers</option>
            <option value="google_drive">Google Drive</option>
            <option value="dropbox">Dropbox</option>
            <option value="onedrive">OneDrive</option>
          </select>

          <select
            className="px-3 py-2 border border-oc-steel/20 rounded-md bg-oc-white text-oc-dark focus:ring-oc-teal focus:border-oc-teal"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="modified_at_source">Modified Date</option>
            <option value="name">Name</option>
            <option value="size">Size</option>
            <option value="created_at_source">Created Date</option>
          </select>

          <select
            className="px-3 py-2 border border-oc-steel/20 rounded-md bg-oc-white text-oc-dark focus:ring-oc-teal focus:border-oc-teal"
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value)}
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </div>
      </div>

      {/* Files Table */}
      <div className="bg-oc-white shadow rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-oc-steel/20">
          <thead className="bg-oc-steel/10">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-oc-steel uppercase tracking-wider">
                File
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-oc-steel uppercase tracking-wider">
                Size
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-oc-steel uppercase tracking-wider">
                Modified
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-oc-steel uppercase tracking-wider">
                Provider
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-oc-steel uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-oc-white divide-y divide-oc-steel/20">
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <FileRowSkeleton key={i} />
              ))
            ) : files.length === 0 ? (
              <tr>
                <td colSpan="5" className="text-center py-12">
                  <p className="text-oc-steel">No files found</p>
                </td>
              </tr>
            ) : (
              files.map((file) => (
                <tr key={file.id} className="hover:bg-oc-steel/5">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <FileIcon file={file} mode={selectedMode} />
                      <div className="ml-4">
                        <div className="text-sm font-medium text-oc-dark truncate max-w-xs">
                          {file.name}
                        </div>
                        <div className="text-sm text-oc-steel truncate max-w-xs">
                          {file.path}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-oc-dark">
                    {file.size_formatted}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-oc-dark">
                    {formatDate(file.modified_at_source)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`provider-badge ${file.provider.replace(
                        "_",
                        "-"
                      )}`}
                    >
                      {file.storage_account.provider.replace("_", " ")}
                    </span>
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
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex items-center">
                      {file.web_view_link && (
                        <IconButton
                          onClick={() => handlePreview(file)}
                          color="primary"
                          size="small"
                          aria-label="preview"
                          title="Preview File"
                        >
                          <FaEye />
                        </IconButton>
                      )}
                      <IconButton
                        aria-label="more actions"
                        aria-controls="long-menu"
                        aria-haspopup="true"
                        onClick={(event) => handleMenuClick(event, file)}
                        size="small"
                        title="More Actions"
                      >
                        <FaEllipsisV />
                      </IconButton>
                      <Menu
                        id="long-menu"
                        MenuListProps={{ "aria-labelledby": "long-button" }}
                        anchorEl={anchorEl}
                        open={Boolean(anchorEl) && selectedFile?.id === file.id}
                        onClose={handleMenuClose}
                        PaperProps={{
                          style: {
                            maxHeight: 48 * 4.5,
                            width: "20ch",
                          },
                        }}
                      >
                        <MenuItem
                          onClick={() => {
                            handleDownload(selectedFile);
                            handleMenuClose();
                          }}
                          disabled={
                            selectedFile?.storage_account?.mode === "metadata"
                          }
                        >
                          <FaDownload className="mr-2" /> Download
                        </MenuItem>
                        <MenuItem
                          onClick={() => {
                            handleDelete(selectedFile);
                            handleMenuClose();
                          }}
                          disabled={
                            selectedFile?.storage_account?.mode === "metadata"
                          }
                        >
                          <FaTrash className="mr-2" /> Delete
                        </MenuItem>
                        <MenuItem
                          onClick={() => {
                            handleFileDetails(selectedFile);
                            handleMenuClose();
                          }}
                        >
                          <FaInfoCircle className="mr-2" /> Details
                        </MenuItem>
                      </Menu>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="bg-oc-white px-4 py-3 flex items-center justify-between border-t border-oc-steel/20">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="relative inline-flex items-center px-4 py-2 border border-oc-steel/20 text-sm font-medium rounded-md text-oc-dark bg-oc-white hover:bg-oc-steel/5"
              >
                Previous
              </button>
              <button
                onClick={() =>
                  setCurrentPage(Math.min(totalPages, currentPage + 1))
                }
                disabled={currentPage === totalPages}
                className="ml-3 relative inline-flex items-center px-4 py-2 border border-oc-steel/20 text-sm font-medium rounded-md text-oc-dark bg-oc-white hover:bg-oc-steel/5"
              >
                Next
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-oc-steel">
                  Page <span className="font-medium">{currentPage}</span> of{" "}
                  <span className="font-medium">{totalPages}</span>
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-oc-steel/20 bg-oc-white text-sm font-medium text-oc-dark hover:bg-oc-steel/5"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() =>
                      setCurrentPage(Math.min(totalPages, currentPage + 1))
                    }
                    disabled={currentPage === totalPages}
                    className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-oc-steel/20 bg-oc-white text-sm font-medium text-oc-dark hover:bg-oc-steel/5"
                  >
                    Next
                  </button>
                </nav>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Delete Restriction Modal */}
      {showDeleteRestrictionModal && selectedFile && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex justify-center items-center">
          <div className="bg-white p-8 rounded-lg shadow-xl max-w-md w-full mx-auto text-center">
            <FaTrash className="text-5xl text-red-600 mx-auto mb-4" />
            <h3 className="text-2xl font-bold text-oc-dark mb-3">
              Deletion Not Available
            </h3>
            <p className="text-oc-steel mb-4">
              You're currently using the account
              <span className="font-semibold">
                {selectedFile.storage_account.provider.replace("_", " ")}
              </span>
              in <span className="font-semibold">Metadata Mode</span>, which
              doesn't allow file deletions.
            </p>
            <p className="text-oc-steel mb-6">
              To delete files, please switch this account to
              <span className="font-semibold">Full Management Mode</span>.
            </p>
            <div className="flex justify-center space-x-4">
              <button
                onClick={handleSwitchToDeleteFullManagement}
                className="bg-oc-teal text-oc-white px-6 py-2 rounded-md hover:bg-oc-navy transition-colors"
              >
                Switch to Full Management Mode
              </button>
              <button
                onClick={handleCloseDeleteRestrictionModal}
                className="border border-oc-steel text-oc-steel px-6 py-2 rounded-md hover:bg-gray-100 transition-colors"
              >
                Cancel
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-4">
              Warning: Switching modes will disconnect and reconnect your
              account. Existing metadata will be preserved, but you'll need to
              re-authenticate.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default Files;
