// frontend/src/components/MessageInput.js
import React, { useState, useRef, useEffect } from 'react';
import { Box, TextField, Button, IconButton, Tooltip, Select, MenuItem, FormControl, InputLabel, Grid, Typography, Switch, FormControlLabel } from '@mui/material';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import ClearIcon from '@mui/icons-material/Clear';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';

const MessageInput = ({ onSendMessage, availablePersonas }) => {
    const [message, setMessage] = useState('');
    const [attachedFile, setAttachedFile] = useState(null);
    const [persona, setPersona] = useState('');
    const [useBrowser, setUseBrowser] = useState(false);
    const fileInputRef = useRef(null);

    useEffect(() => {
        if (Object.keys(availablePersonas).length > 0 && !persona) {
            setPersona(Object.keys(availablePersonas)[0]);
        }
    }, [availablePersonas, persona]);

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setAttachedFile(e.target.files[0]);
        }
    };

    const handleSend = async () => {
        if (!message.trim() && !attachedFile) {
            return; // Don't send empty messages
        }
        // onSendMessage is now expected to handle the file object directly
        onSendMessage(message, persona, attachedFile, useBrowser);

        // Reset state
        setMessage('');
        setAttachedFile(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
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
                onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                sx={{ marginBottom: 1 }}
                multiline
                rows={2}
            />
             {attachedFile && (
                <Box sx={{ mb: 1, p: 1, display: 'flex', alignItems: 'center', border: '1px solid #ccc', borderRadius: 1 }}>
                    <InsertDriveFileIcon sx={{ mr: 1, color: 'grey.700' }} />
                    <Typography variant="body2" sx={{ flexGrow: 1 }}>{attachedFile.name}</Typography>
                    <IconButton onClick={() => { setAttachedFile(null); if(fileInputRef.current) fileInputRef.current.value = ""; }} size="small">
                        <ClearIcon />
                    </IconButton>
                </Box>
            )}
            <Grid container spacing={1} alignItems="center">
                <Grid item>
                    <input
                        type="file"
                        accept="image/*,audio/*,video/*"
                        ref={fileInputRef}
                        style={{ display: 'none' }}
                        onChange={handleFileChange}
                    />
                    <Tooltip title="Attach File (Image, Audio, Video)">
                        <IconButton onClick={() => fileInputRef.current.click()}>
                            <AttachFileIcon />
                        </IconButton>
                    </Tooltip>
                </Grid>

                <Grid item>
                    <FormControlLabel
                        control={<Switch checked={useBrowser} onChange={(e) => setUseBrowser(e.target.checked)} />}
                        label="Browser"
                    />
                </Grid>

                <Grid item>
                    <FormControl sx={{ minWidth: 120 }} size="small">
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

                <Grid item xs>
                    {/* Spacer */}
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