// frontend/src/components/FileUpload.js
import React, { useState } from 'react';
import { Box, Button, Typography } from '@mui/material';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import axios from 'axios';

const FileUpload = ({ onAddMessage }) => {
  const [file, setFile] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post("http://127.0.0.1:8000/upload", formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setUploadResult(response.data);
      const fileMessage = `**File Uploaded:** ${response.data.filename}\nLocation: ${response.data.location}`;
      if (onAddMessage) {
        onAddMessage({ sender: "file", content: fileMessage });
      }
    } catch (error) {
      console.error("File upload error:", error);
    } finally {
      setFile(null);
    }
  };

  return (
    <Box sx={{ p: 2, mb: 2, border: '1px solid #ccc', borderRadius: 1 }}>
      <Typography variant="h6">File Upload for Analysis</Typography>
      <input type="file" onChange={handleFileChange} />
      <Button variant="contained" onClick={handleUpload} sx={{ ml: 1, mt: 1 }}>
        Upload
      </Button>
      {uploadResult && (
        <Typography variant="body2" sx={{ mt: 1 }}>
          Uploaded: {uploadResult.filename}
          <InsertDriveFileIcon sx={{ ml: 1, verticalAlign: 'middle' }} />
        </Typography>
      )}
    </Box>
  );
};

export default FileUpload;
