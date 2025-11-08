import React from 'react';

const FileIcon = ({ file, mode }) => {
  const getFileType = (mimeType, extension) => {
    if (!mimeType && !extension) return 'unknown';
    
    const type = mimeType || '';
    const ext = (extension || '').toLowerCase();

    // Image files
    if (type.startsWith('image/') || ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'].includes(ext)) {
      return 'image';
    }

    // Video files
    if (type.startsWith('video/') || ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm'].includes(ext)) {
      return 'video';
    }

    // Audio files
    if (type.startsWith('audio/') || ['mp3', 'wav', 'flac', 'aac', 'm4a', 'ogg'].includes(ext)) {
      return 'audio';
    }

    // Document files
    if (type.includes('pdf') || ext === 'pdf') return 'document';
    if (type.includes('word') || ['doc', 'docx'].includes(ext)) return 'document';
    if (type.includes('text') || ['txt', 'md', 'rtf'].includes(ext)) return 'document';

    // Spreadsheet files
    if (type.includes('sheet') || ['xls', 'xlsx', 'csv'].includes(ext)) return 'spreadsheet';

    // Presentation files
    if (type.includes('presentation') || ['ppt', 'pptx'].includes(ext)) return 'presentation';

    // Archive files
    if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return 'archive';

    return 'unknown';
  };

  const fileType = getFileType(file.mime_type, file.file_extension);
  const extension = file.file_extension || 'file';
  const isMetadataMode = mode === 'metadata';

  return (
    <div className={`file-icon ${fileType} ${isMetadataMode ? 'metadata-mode' : ''}`}>
      {extension.substring(0, 3)}
    </div>
  );
};

export default FileIcon;
