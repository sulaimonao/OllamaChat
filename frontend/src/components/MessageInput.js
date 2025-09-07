// frontend/src/components/MessageInput.js
import React, { useState, useRef, useEffect } from 'react';
import { Box, TextField, Button, IconButton, Tooltip, Select, MenuItem, FormControl, InputLabel, Grid, Typography, Switch, FormControlLabel } from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import ImageIcon from '@mui/icons-material/Image';
import { uploadFile, webSearch, getSystemPrompts } from '../api';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';

const MessageInput = ({ onSendMessage, availablePersonas }) => {
    const [message, setMessage] = useState('');
    const [attachedFile, setAttachedFile] = useState(null);
    const [attachedFileName, setAttachedFileName] = useState(''); // Store filename for display
    const [searchResult, setSearchResult] = useState('');
    const [useBrowser, setUseBrowser] = useState(false);
    const [reasoningStyle, setReasoningStyle] = useState('');
    const [persona, setPersona] = useState('');
    const [image, setImage] = useState(null);
    const [imageName, setImageName] = useState('');  // Store image name
    const fileInputRef = useRef(null);
    const imageInputRef = useRef(null);

    useEffect(() => {
        if (Object.keys(availablePersonas).length > 0 && !persona) {
            setPersona(Object.keys(availablePersonas)[0]);
        }
    }, [availablePersonas, persona]);

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setAttachedFile(e.target.files[0]);
            setAttachedFileName(e.target.files[0].name); // Store the filename
        }
    };

    const handleImageChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            const reader = new FileReader();
            reader.onloadend = () => {
                setImage(reader.result);
                setImageName(e.target.files[0].name); // Store image name
            };
            reader.readAsDataURL(e.target.files[0]);
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
            setAttachedFileName(''); // Clear filename after sending
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
        onSendMessage(finalMessage, persona, null, base64Image, reasoningStyle, useBrowser);
        setMessage('');
        setImage(null);
        setImageName(''); //Clear image name after submit
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
                {/* File Upload */}
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
                    {/* Display attached file name */}
                    {attachedFileName && (
                        <Typography variant="body2" sx={{ ml: 1 }}>
                            <InsertDriveFileIcon sx={{ fontSize: '1em', verticalAlign: 'middle' }} />
                            {attachedFileName}
                        </Typography>
                    )}
                </Grid>

                {/* Image Upload */}
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
                    {/* Display attached image name */}
                    {imageName && (
                        <Typography variant="body2" sx={{ ml: 1 }}>
                            <ImageIcon sx={{ fontSize: '1em', verticalAlign: 'middle' }} />
                            {imageName}
                        </Typography>
                    )}
                </Grid>
                {/* Browser Toggle */}
                <Grid item>
                    <FormControlLabel
                        control={<Switch checked={useBrowser} onChange={(e) => setUseBrowser(e.target.checked)} />}
                        label="Browser"
                    />
                </Grid>
                {/* Persona Selection */}
                <Grid item>
                    <FormControl sx={{ minWidth: 120 }}>
                        <InputLabel>Persona</InputLabel>
                        <Select
                            value={persona}
                            onChange={handlePersonaChange}
                            label="Persona"
                        >
                            {Object.keys(availablePersonas).map((key) => (
                                <MenuItem key={key} value={key}>{key}</MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                </Grid>

                {/* ... (Reasoning Style Selection, Send Button) ... */}
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