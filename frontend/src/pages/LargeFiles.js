import React, { useState, useEffect, useCallback } from 'react';
import { FaEye, FaTrash, FaInfoCircle, FaLock, FaTimes, FaCloud, FaSortAmountDown, FaSortAmountUp, FaFileAlt } from 'react-icons/fa';
import api from '../services/api';
import FileIcon from '../components/FileIcon';
import toast from 'react-hot-toast';
import { useLocation, useNavigate } from 'react-router-dom';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, Box, IconButton, MenuItem, FormControl, InputLabel, Select, CircularProgress } from '@mui/material';
import config from '../config'; // Import the default export config

const getProviderIcon = (providerId) => {
  const provider = config.CLOUD_PROVIDERS.find(p => p.id === providerId);
  return provider ? provider.icon : <FaCloud />;
};

const LargeFileRowSkeleton = () => (
  <div className="bg-oc-white rounded-lg shadow p-4 flex items-center justify-between animate-pulse mb-3">
    <div className="flex items-center">
      <div className="w-8 h-8 bg-gray-300 rounded-md flex-shrink-0"></div>
      <div className="ml-4">
        <div className="h-4 bg-gray-300 rounded w-48 mb-2"></div>
        <div className="h-3 bg-gray-300 rounded w-32"></div>
      </div>
    </div>
    <div className="flex items-center space-x-2">
      <div className="h-8 bg-gray-300 rounded-md w-20"></div>
      <div className="h-8 bg-gray-300 rounded-md w-20"></div>
      <div className="h-8 bg-gray-300 rounded-md w-20"></div>
    </div>
  </div>
);

const LargeFiles = () => {
  const [largeFiles, setLargeFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const location = useLocation();
  const navigate = useNavigate();
  const [selectedMode, setSelectedMode] = useState(null);
  const [sizeThreshold, setSizeThreshold] = useState(100); // in MB
  const [selectedProvider, setSelectedProvider] = useState('all');
  const [sortBy, setSortBy] = useState('size');
  const [sortOrder, setSortOrder] = useState('desc');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [previewUrl, setPreviewUrl] = useState('');
  const [previewLoading, setPreviewLoading] = useState(false);
  const [showPreviewRestrictionModal, setShowPreviewRestrictionModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [fileToDelete, setFileToDelete] = useState(null);
  const [showDeleteRestrictionModal, setShowDeleteRestrictionModal] = useState(false);
  const [fileToRestrict, setFileToRestrict] = useState(null);

  const fetchLargeFiles = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        size_threshold_mb: sizeThreshold,
        provider: selectedProvider === 'all' ? undefined : selectedProvider,
        sort_by: sortBy,
        sort_order: sortOrder,
        page: page,
        per_page: 20, // Hardcoded per_page to 20 as per_page state was removed
      };
      const response = await api.get('/api/large-files', { params });
      setLargeFiles(response.data.files);
      setTotalPages(response.data.total_pages);
    } catch (error) {
      console.error('Failed to fetch large files:', error);
      toast.error('Failed to load large files.');
    } finally {
      setLoading(false);
    }
  }, [sizeThreshold, selectedProvider, sortBy, sortOrder, page]);

  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    const mode = queryParams.get('mode');
    if (mode) {
      setSelectedMode(mode);
    } else {
      setSelectedMode('full_access'); // Default to full_access if no mode is specified
    }
    fetchLargeFiles();
  }, [location.search, fetchLargeFiles]);

  const handlePageChange = (newPage) => {
    setPage(newPage);
  };

  const handleThresholdChange = (e) => {
    setSizeThreshold(e.target.value);
    setPage(1); // Reset to first page on filter change
  };

  const handleProviderChange = (e) => {
    setSelectedProvider(e.target.value);
    setPage(1);
  };

  const handleSortChange = (newSortBy) => {
    if (sortBy === newSortBy) {
      setSortOrder(prev => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(newSortBy);
      setSortOrder('desc'); // Default sort order for new sort column
    }
    setPage(1);
  };

  const handlePreviewFile = async (file) => {
    if (file.storage_account.mode === 'metadata') {
      setFileToRestrict(file);
      setShowPreviewRestrictionModal(true);
      return;
    }
    setPreviewLoading(true);
    setShowPreviewModal(true);
    try {
      const response = await api.get(`/api/files/${file.id}/preview`);
      setPreviewUrl(response.data.preview_url);
    } catch (error) {
      console.error('Failed to get preview URL:', error);
      toast.error('Failed to load preview.');
      setPreviewUrl(''); // Clear URL on error
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleClosePreviewModal = () => {
    setShowPreviewModal(false);
    setPreviewUrl('');
  };

  const handleClosePreviewRestrictionModal = () => {
    setShowPreviewRestrictionModal(false);
    setFileToRestrict(null);
  };

  const handleSwitchToFullManagement = () => {
    if (fileToRestrict) {
      navigate('/accounts', { state: { highlightAccount: fileToRestrict.storage_account.id, targetMode: 'full_access' } });
      handleClosePreviewRestrictionModal();
      handleCloseDeleteRestrictionModal();
    }
  };

  const openDeleteConfirm = (file) => {
    setFileToDelete(file);
    setShowDeleteConfirm(true);
  };

  const handleDeleteFile = async () => {
    if (!fileToDelete) return;

    if (fileToDelete.storage_account.mode === 'metadata') {
      setShowDeleteRestrictionModal(true);
      setFileToRestrict(fileToDelete);
      setShowDeleteConfirm(false); // Close current dialog
      return;
    }

    try {
      await api.delete(`/api/files/${fileToDelete.id}`);
      toast.success(`${fileToDelete.name} deleted successfully.`);
      fetchLargeFiles(); // Refresh the list
      setShowDeleteConfirm(false);
      setFileToDelete(null);
    } catch (error) {
      console.error('Failed to delete file:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete file.');
    }
  };

  const handleCancelDelete = () => {
    setShowDeleteConfirm(false);
    setFileToDelete(null);
  };

  const handleCloseDeleteRestrictionModal = () => {
    setShowDeleteRestrictionModal(false);
    setFileToRestrict(null);
  };

  const formatBytes = (bytes, decimals = 2) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-oc-dark mb-6">Large Files ({selectedMode === 'metadata' ? 'Metadata Mode' : 'Full Access Mode'})</h1>

      <div className="bg-oc-white shadow rounded-lg p-6 mb-6 flex flex-col md:flex-row gap-4 items-center">
        <FormControl variant="outlined" size="small" sx={{ minWidth: 180 }}>
          <InputLabel>Size Threshold</InputLabel>
          <Select value={sizeThreshold} onChange={handleThresholdChange} label="Size Threshold">
            <MenuItem value={10}>10 MB</MenuItem>
            <MenuItem value={50}>50 MB</MenuItem>
            <MenuItem value={100}>100 MB</MenuItem>
            <MenuItem value={500}>500 MB</MenuItem>
            <MenuItem value={1000}>1 GB</MenuItem>
          </Select>
        </FormControl>

        <FormControl variant="outlined" size="small" sx={{ minWidth: 180 }}>
          <InputLabel>Cloud Provider</InputLabel>
          <Select value={selectedProvider} onChange={handleProviderChange} label="Cloud Provider">
            <MenuItem value="all">All Providers</MenuItem>
            {config.CLOUD_PROVIDERS.map(p => (
              <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl variant="outlined" size="small" sx={{ minWidth: 180 }}>
          <InputLabel>Sort By</InputLabel>
          <Select value={sortBy} onChange={(e) => handleSortChange(e.target.value)} label="Sort By">
            <MenuItem value="size">Size</MenuItem>
            <MenuItem value="name">Name</MenuItem>
            <MenuItem value="modified_at_source">Last Modified</MenuItem>
          </Select>
        </FormControl>

        <IconButton onClick={() => setSortOrder(prev => (prev === 'asc' ? 'desc' : 'asc'))}>
          {sortOrder === 'asc' ? <FaSortAmountUp /> : <FaSortAmountDown />}
        </IconButton>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[...Array(20)].map((_, i) => ( // Hardcoded 20 skeletons as per_page was removed
            <LargeFileRowSkeleton key={i} />
          ))}
        </div>
      ) : largeFiles.length === 0 ? (
        <div className="bg-oc-white rounded-lg shadow p-12 text-center">
          <p className="text-oc-steel text-lg">No large files found above {sizeThreshold} MB!</p>
          <p className="text-oc-steel mt-2">Adjust your filter criteria or check your connected accounts.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {largeFiles.map((file) => (
            <div key={file.id} className="bg-oc-white rounded-lg shadow p-4 flex items-center justify-between hover:bg-oc-steel/5">
              <div className="flex items-center">
                <FileIcon file={file} mode={file.storage_account.mode} />
                <div className="ml-4">
                  <div className="text-md font-medium text-oc-dark">
                    {file.name}
                    <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${file.storage_account.mode === 'metadata' ? 'bg-gray-200 text-gray-700' : 'bg-oc-teal/20 text-oc-navy'}`}>
                      {file.storage_account.mode === 'metadata' ? 'Metadata' : 'Full Access'}
                    </span>
                  </div>
                  <div className="text-sm text-oc-steel">
                    {getProviderIcon(file.storage_account.provider)} {file.storage_account.provider.replace('_', ' ')} • {formatBytes(file.size)} • {new Date(file.modified_at_source).toLocaleDateString()}
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Button 
                  variant="outlined" 
                  size="small" 
                  startIcon={<FaEye />} 
                  onClick={() => handlePreviewFile(file)}
                  disabled={file.is_folder}
                >
                  Preview
                </Button>
                <Button
                  variant="contained"
                  color="error"
                  size="small"
                  startIcon={<FaTrash />}
                  onClick={() => openDeleteConfirm(file)}
                  disabled={file.storage_account.mode === 'metadata'}
                >
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <Button onClick={() => handlePageChange(page - 1)} disabled={page === 1}>
            Previous
          </Button>
          <Typography sx={{ mx: 2 }}>
            Page {page} of {totalPages}
          </Typography>
          <Button onClick={() => handlePageChange(page + 1)} disabled={page === totalPages}>
            Next
          </Button>
        </Box>
      )}

      {/* Single File Delete Confirmation Dialog */}
      <Dialog open={showDeleteConfirm} onClose={handleCancelDelete}>
        <DialogTitle>Confirm Deletion</DialogTitle>
        <DialogContent>
          <Typography sx={{ mb: 2 }}>
            Are you sure you want to permanently delete 
            <span className="font-semibold">{fileToDelete?.name}</span>
            from your <span className="font-semibold">{fileToDelete?.storage_account.provider.replace('_', ' ')}</span> account?
          </Typography>
          <Typography variant="body2" color="error">
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelDelete}>Cancel</Button>
          <Button onClick={handleDeleteFile} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Preview Modal */}
      <Dialog open={showPreviewModal} onClose={handleClosePreviewModal} maxWidth="md" fullWidth>
        <DialogTitle>
          File Preview
          <IconButton
            aria-label="close"
            onClick={handleClosePreviewModal}
            sx={{
              position: 'absolute',
              right: 8,
              top: 8,
              color: (theme) => theme.palette.grey[500],
            }}
          >
            <FaTimes />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers sx={{ height: '70vh', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          {previewLoading ? (
            <CircularProgress className="text-oc-teal" />
          ) : previewUrl ? (
            <iframe src={previewUrl} title="File Preview" width="100%" height="100%" style={{ border: 'none' }}></iframe>
          ) : (
            <Box sx={{ textAlign: 'center', color: 'text.secondary' }}>
              <FaFileAlt className="text-5xl mb-3" />
              <Typography>No preview available or failed to load.</Typography>
            </Box>
          )}
        </DialogContent>
      </Dialog>

      {/* Preview Restriction Modal */}
      <Dialog open={showPreviewRestrictionModal} onClose={handleClosePreviewRestrictionModal}>
        <DialogContent sx={{ p: 4, textAlign: 'center' }}>
          <FaInfoCircle className="text-5xl text-oc-teal mx-auto mb-4" />
          <Typography variant="h5" component="h2" sx={{ color: 'text.primary', mb: 2 }}>
            Preview Not Available
          </Typography>
          <Typography sx={{ mb: 2 }}>
            You're currently using the account
            <span className="font-semibold">{fileToRestrict?.storage_account.provider.replace('_', ' ')}</span>
            in <span className="font-semibold">Metadata Mode</span>, which doesn't support file previews.
          </Typography>
          <Typography sx={{ mb: 3 }}>
            To enable preview functionality, you can switch this account to
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
          <Button variant="outlined" onClick={handleClosePreviewRestrictionModal}>
            Cancel
          </Button>
          <Typography variant="caption" display="block" sx={{ mt: 3, color: 'text.secondary' }}>
            Warning: Switching modes will disconnect and reconnect your account.
            Existing metadata will be preserved, but you'll need to re-authenticate.
          </Typography>
        </DialogContent>
      </Dialog>

      {/* Delete Restriction Modal */}
      <Dialog open={showDeleteRestrictionModal} onClose={handleCloseDeleteRestrictionModal}>
        <DialogContent sx={{ p: 4, textAlign: 'center' }}>
          <FaLock className="text-5xl text-red-500 mx-auto mb-4" />
          <Typography variant="h5" component="h2" sx={{ color: 'text.primary', mb: 2 }}>
            Deletion Not Available
          </Typography>
          <Typography sx={{ mb: 2 }}>
            This account is connected in <span className="font-semibold">Metadata Mode</span>, 
            which doesn't allow file deletions.
          </Typography>
          <Typography sx={{ mb: 3 }}>
            To delete files, please switch to <span className="font-semibold">Full Management Mode</span>.
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={handleSwitchToFullManagement}
            sx={{ mr: 2 }}
          >
            Switch to Full Management Mode
          </Button>
          <Button variant="outlined" onClick={handleCloseDeleteRestrictionModal}>
            Cancel
          </Button>
          <Typography variant="caption" display="block" sx={{ mt: 3, color: 'text.secondary' }}>
            Warning: Switching modes will disconnect and reconnect your account.
            Existing metadata will be preserved, but you'll need to re-authenticate.
          </Typography>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default LargeFiles;
