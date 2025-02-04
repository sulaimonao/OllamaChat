// frontend/src/components/MessageInput.js
import React, { useState, useRef } from 'react';
import { Box, TextField, Button, IconButton, Tooltip, Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import SearchIcon from '@mui/icons-material/Search';
import { uploadFile, webSearch } from '../api';

const MessageInput = ({ onSendMessage }) => {
  const [message, setMessage] = useState('');
  const [attachedFile, setAttachedFile] = useState(null);
  const [searchResult, setSearchResult] = useState('');
  const [reasoningStyle, setReasoningStyle] = useState('');
  const fileInputRef = useRef(null);

  const handleFileIconClick = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setAttachedFile(e.target.files[0]);
    }
  };

  const handleSearchIconClick = async () => {
    const query = prompt("Enter web search query:");
    if (query) {
      try {
        const data = await webSearch(query);
        const abstract = data.abstract || "No abstract available.";
        setSearchResult(`[WEB_SEARCH: ${abstract}]`);
      } catch (error) {
        console.error("Error during web search:", error);
      }
    }
  };

  const handleSend = async () => {
    let fileInfo = null; // Initialize fileInfo

    // If a file is attached, upload it
    if (attachedFile) {
      const formData = new FormData();
      formData.append('file', attachedFile);
      try {
        const response = await uploadFile(formData);
        // Instead of appending to the message, store the file info separately
        fileInfo = `[FILE: ${response.location}]`;
      } catch (error) {
        console.error("File upload error:", error);
      }
      setAttachedFile(null); // Clear the attached file after uploading
    }

    let finalMessage = message;
    // If there is a search result, append it to the message
    if (searchResult) {
      finalMessage += `\n${searchResult}`;
      setSearchResult('');
    }

    // Pass the fileInfo along with the message and reasoning style
    onSendMessage(finalMessage, reasoningStyle, fileInfo);
    setMessage('');
  };

  const handleReasoningStyleChange = (event) => {
    setReasoningStyle(event.target.value);
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', marginTop: 2 }}>
      <TextField
        fullWidth
        variant="outlined"
        placeholder="Type your message..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
      />
      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />
      <Tooltip title="Attach File">
        <IconButton onClick={handleFileIconClick}>
          <UploadFileIcon />
        </IconButton>
      </Tooltip>
      <Tooltip title="Web Search">
        <IconButton onClick={handleSearchIconClick}>
          <SearchIcon />
        </IconButton>
      </Tooltip>
      <FormControl sx={{ minWidth: 120, ml: 1 }}>
        <InputLabel>Reasoning</InputLabel>
        <Select
          value={reasoningStyle}
          onChange={handleReasoningStyleChange}
          label="Reasoning"
        >
          <MenuItem value="">
            <em>None</em>
          </MenuItem>
          <MenuItem value="default">Default</MenuItem>
          <MenuItem value="explanatory">Explanatory</MenuItem>
          <MenuItem value="comparative">Comparative</MenuItem>
          <MenuItem value="step_by_step">Step-by-Step</MenuItem>
          <MenuItem value="alternatives">Alternatives</MenuItem>
        </Select>
      </FormControl>
      <Button variant="contained" onClick={handleSend} sx={{ marginLeft: 1 }}>
        Send
      </Button>
    </Box>
  );
};

export default MessageInput;
