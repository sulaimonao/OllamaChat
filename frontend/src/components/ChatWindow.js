import React, { useRef, useEffect } from 'react';
import { Box, Typography } from '@mui/material';

const ChatWindow = ({ messages }) => {
  const endOfMessagesRef = useRef(null);

  // Scroll to the latest message when messages update.
  useEffect(() => {
    if (endOfMessagesRef.current) {
      endOfMessagesRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  return (
    <Box
      sx={{
        flexGrow: 1,
        overflowY: 'auto',
        padding: 1,
        border: '1px solid #ccc',
        borderRadius: 1,
        marginY: 2,
      }}
    >
      {messages.map((msg, index) => (
        <Box key={index} sx={{ marginBottom: 1 }}>
          <Typography variant="subtitle2" color={msg.sender === 'user' ? 'primary' : 'secondary'}>
            {msg.sender === 'user' ? 'You' : 'Model'}
          </Typography>
          <Typography variant="body1">{msg.content}</Typography>
        </Box>
      ))}
      <div ref={endOfMessagesRef} />
    </Box>
  );
};

export default ChatWindow;
