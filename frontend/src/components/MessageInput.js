import React, { useState } from 'react';
import { Box, TextField, Button } from '@mui/material';

const MessageInput = ({ onSendMessage }) => {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    if (message.trim() !== '') {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  return (
    <Box sx={{ display: 'flex', marginTop: 2 }}>
      <TextField
        fullWidth
        variant="outlined"
        placeholder="Type your message..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyPress={handleKeyPress}
      />
      <Button variant="contained" color="primary" onClick={handleSend} sx={{ marginLeft: 1 }}>
        Send
      </Button>
    </Box>
  );
};

export default MessageInput;
