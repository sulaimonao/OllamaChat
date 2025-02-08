// frontend/src/components/MessageInput.js
import React, { useState, useRef, useEffect } from 'react'; // Add useEffect
import { Box, TextField, Button, IconButton, Tooltip, Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import SearchIcon from '@mui/icons-material/Search';
import ImageIcon from '@mui/icons-material/Image';
import { uploadFile, webSearch, getSystemPrompts } from '../api'; // Import getSystemPrompts

const MessageInput = ({ onSendMessage }) => {
  const [message, setMessage] = useState('');
  const [attachedFile, setAttachedFile] = useState(null);
  const [searchResult, setSearchResult] = useState('');
  const [reasoningStyle, setReasoningStyle] = useState('');  // Will also be used for persona
  const [image, setImage] = useState(null);
  const fileInputRef = useRef(null);
  const imageInputRef = useRef(null);
  const [availablePersonas, setAvailablePersonas] = useState({}); // Add state for personas

    useEffect(() => {
      // Fetch available personas (system prompts)
      getSystemPrompts()
        .then((data) => {
          setAvailablePersonas(data.system_prompts);
          // Optionally set a default persona here, e.g.,
          if (Object.keys(data.system_prompts).length > 0) {
            setReasoningStyle(Object.keys(data.system_prompts)[0]); // Set first as default
          }
        })
        .catch((error) => {
          console.error("Error fetching system prompts:", error);
        });
    }, []); // Empty dependency array - only run once on mount


  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setAttachedFile(e.target.files[0]);
    }
  };

  const handleImageChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImage(reader.result);
      };
      reader.readAsDataURL(e.target.files[0]);
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
    let fileInfo = null;

    if (attachedFile) {
      const formData = new FormData();
      formData.append('file', attachedFile);
      try {
        const response = await uploadFile(formData);
        fileInfo = response.data.location.trim();
      } catch (error) {
        console.error("File upload error:", error);
      }
      setAttachedFile(null);
    }

    let finalMessage = message;
    if (searchResult) {
      finalMessage += `\n${searchResult}`;
      setSearchResult('');
    }

    if (fileInfo) {
      finalMessage += `\n[FILE:${fileInfo}]`;
    }
    const base64Image = image ? image.split(',')[1] : null;
    onSendMessage(finalMessage, reasoningStyle, null, base64Image); // reasoningStyle is now persona
    setMessage('');
    setImage(null);
  };

  const handleReasoningStyleChange = (event) => {
    setReasoningStyle(event.target.value); // Update reasoningStyle (now persona)
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
      <input
        type="file"
        ref={fileInputRef}
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />
      <input
        type="file"
        accept="image/*"
        ref={imageInputRef}
        style={{ display: 'none' }}
        onChange={handleImageChange}
      />
      <Tooltip title="Attach File">
        <IconButton onClick={() => fileInputRef.current.click()}>
          <UploadFileIcon />
        </IconButton>
      </Tooltip>
      <Tooltip title="Attach Image">
        <IconButton onClick={() => imageInputRef.current.click()}>
          <ImageIcon />
        </IconButton>
      </Tooltip>
      <Tooltip title="Web Search">
        <IconButton onClick={handleSearchIconClick}>
          <SearchIcon />
        </IconButton>
      </Tooltip>
      <FormControl sx={{ minWidth: 120, ml: 1 }}>
        <InputLabel>Persona</InputLabel>
        <Select
          value={reasoningStyle}  {/* Value is now the selected persona */}
          onChange={handleReasoningStyleChange}
          label="Persona"
        >
          <MenuItem value="">
            <em>None</em>
          </MenuItem>
            {/* Populate options from availablePersonas */}
            {Object.entries(availablePersonas).map(([key, description]) => (
              <MenuItem key={key} value={key}>{description}</MenuItem>
            ))}
        </Select>
      </FormControl>
      <Button variant="contained" onClick={handleSend} sx={{ marginLeft: 1 }}>
        Send
      </Button>
    </Box>
  );
};

export default MessageInput;