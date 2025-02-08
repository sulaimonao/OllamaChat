// frontend/src/components/MessageInput.js
import React, { useState, useRef, useEffect } from 'react';
import { Box, TextField, Button, IconButton, Tooltip, Select, MenuItem, FormControl, InputLabel, Grid } from '@mui/material'; // Import Grid
import UploadFileIcon from '@mui/icons-material/UploadFile';
import SearchIcon from '@mui/icons-material/Search';
import ImageIcon from '@mui/icons-material/Image';
import { uploadFile, webSearch, getSystemPrompts } from '../api';

const MessageInput = ({ onSendMessage }) => {
  const [message, setMessage] = useState('');
  const [attachedFile, setAttachedFile] = useState(null);
  const [searchResult, setSearchResult] = useState('');
  const [reasoningStyle, setReasoningStyle] = useState(''); // Keep reasoningStyle
  const [persona, setPersona] = useState(''); // Separate state for persona
  const [image, setImage] = useState(null);
  const fileInputRef = useRef(null);
  const imageInputRef = useRef(null);
  const [availablePersonas, setAvailablePersonas] = useState({});

  useEffect(() => {
    getSystemPrompts()
      .then((data) => {
        console.log("System Prompts Data (frontend):", data); // Keep this
        console.log("Type of data.system_prompts:", typeof data.system_prompts); // Add this
        console.log("Keys of data.system_prompts:", Object.keys(data.system_prompts)); // Add this
        setAvailablePersonas(data.system_prompts);
        if (Object.keys(data.system_prompts).length > 0) {
          setPersona(Object.keys(data.system_prompts)[0]);
        }
      })
      .catch((error) => {
        console.error("Error fetching system prompts:", error);
      });
  }, []);  

  const handleFileChange = (e) => {
    console.log("File selected:", e.target.files[0]); // Log selected file
    if (e.target.files && e.target.files[0]) {
      setAttachedFile(e.target.files[0]);
    }
  };

  const handleImageChange = (e) => {
    console.log("Image selected:", e.target.files[0]); // Log selected image
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
    console.log("Search query:", query); // Log search query
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
    onSendMessage(finalMessage, persona, null, base64Image, reasoningStyle); // Pass BOTH persona and reasoningStyle
    setMessage('');
    setImage(null);
  };

  const handleReasoningStyleChange = (event) => {
    setReasoningStyle(event.target.value);
  };

  const handlePersonaChange = (event) => {
    setPersona(event.target.value);
  };

  return (
    <Box sx={{ marginTop: 2 }}>
      <TextField
        fullWidth
        variant="outlined"
        placeholder="Type your message..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        sx={{ marginBottom: 2 }}
      />
      <Grid container spacing={1} alignItems="center">
        <Grid item>
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            onChange={handleFileChange}
          />
          <Tooltip title="Attach File">
            <IconButton onClick={() => fileInputRef.current.click()}>
              <UploadFileIcon />
            </IconButton>
          </Tooltip>
        </Grid>
        <Grid item>
          <input
            type="file"
            accept="image/*"
            ref={imageInputRef}
            style={{ display: 'none' }}
            onChange={handleImageChange}
          />
          <Tooltip title="Attach Image">
            <IconButton onClick={() => imageInputRef.current.click()}>
              <ImageIcon />
            </IconButton>
          </Tooltip>
        </Grid>
        <Grid item>
          <Tooltip title="Web Search">
            <IconButton onClick={handleSearchIconClick}>
              <SearchIcon />
            </IconButton>
          </Tooltip>
        </Grid>
        <Grid item>
        <FormControl sx={{ minWidth: 120 }}>
          <InputLabel>Persona</InputLabel>
          <Select
            value={persona}
            onChange={handlePersonaChange}
            label="Persona"
          >
            {Object.entries(availablePersonas).map(([key, description]) => (
              <MenuItem key={key} value={key}>{description}</MenuItem>
            ))}
          </Select>
        </FormControl>
        </Grid>
        <Grid item>
          <FormControl sx={{ minWidth: 120 }}>
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
        </Grid>
        <Grid item>
          <Button variant="contained" onClick={handleSend}>
            Send
          </Button>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MessageInput;