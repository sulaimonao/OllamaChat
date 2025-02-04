// frontend/src/components/MessageInput.js
import React, { useState, useRef } from 'react';
import { Box, TextField, Button, IconButton, Tooltip, Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import SearchIcon from '@mui/icons-material/Search';
import { uploadFile, webSearch } from '../api';  // Import from api.js

const MessageInput = ({ onSendMessage }) => {
  const [message, setMessage] = useState('');
  const [attachedFile, setAttachedFile] = useState(null);
  const [searchResult, setSearchResult] = useState('');
  const [reasoningStyle, setReasoningStyle] = useState('');
  const fileInputRef = useRef(null);

  // Trigger the hidden file input
  const handleFileIconClick = () => {
    fileInputRef.current.click();
  };

  // When a file is chosen, store it in state
  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setAttachedFile(e.target.files[0]);
    }
  };

  // When the search icon is clicked, prompt for a search query and call the /search endpoint
  const handleSearchIconClick = async () => {
    const query = prompt("Enter web search query:");
    if (query) {
      try {
        const data = await webSearch(query); // Use webSearch from api.js
        // For simplicity, use the abstract as the search result summary.
        const abstract = data.abstract || "No abstract available.";
        // Format the result to be appended to the message.
        setSearchResult(`[WEB_SEARCH: ${abstract}]`);
      } catch (error) {
        console.error("Error during web search:", error);
      }
    }
  };

  const handleSend = async () => {
    let finalMessage = message;

    // If a file is attached, upload it and append file info to the message
    if (attachedFile) {
      const formData = new FormData();
      formData.append('file', attachedFile);
      try {
        const response = await uploadFile(formData); // Use uploadFile from api.js
        // Append the file location to the message
        finalMessage += `\n[FILE: ${response.data.location}]`;
      } catch (error) {
        console.error("File upload error:", error);
      }
      // Clear the attached file after uploading
      setAttachedFile(null);
    }

    // If there is a search result, append it to the message
    if (searchResult) {
      finalMessage += `\n${searchResult}`;
      setSearchResult('');
    }

    if (finalMessage.trim() !== '') {
      onSendMessage(finalMessage, reasoningStyle);
      setMessage('');
    }
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
