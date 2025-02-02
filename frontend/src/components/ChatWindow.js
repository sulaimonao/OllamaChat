// frontend/src/components/ChatWindow.js
import React, { useRef, useEffect, useState } from 'react';
import {
  Box,
  Typography,
  CircularProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import ReactMarkdown from 'react-markdown';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

const ChatWindow = ({ messages, isLoading }) => {
  const endOfMessagesRef = useRef(null);
  const [copiedIndex, setCopiedIndex] = useState(null);

  // Scroll to the latest message when messages or loading state changes.
  useEffect(() => {
    if (endOfMessagesRef.current) {
      endOfMessagesRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading]);

  // Copy the provided text to clipboard.
  const handleCopy = (text, index) => {
    navigator.clipboard.writeText(text)
      .then(() => {
        setCopiedIndex(index);
        setTimeout(() => setCopiedIndex(null), 2000); // Reset after 2 seconds.
      })
      .catch((err) => {
        console.error('Failed to copy!', err);
      });
  };

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
        <Box key={index} sx={{ marginBottom: 2, position: 'relative' }}>
          <Typography variant="subtitle2" color={msg.sender === 'user' ? 'primary' : 'secondary'}>
            {msg.sender === 'user' ? 'You' : 'Model'}
          </Typography>
          {msg.sender === 'model' ? (
            <Box sx={{ position: 'relative', paddingRight: 4 }}>
              <ReactMarkdown>{msg.content}</ReactMarkdown>
              <Tooltip title={copiedIndex === index ? "Copied!" : "Copy to clipboard"} arrow>
                <IconButton
                  onClick={() => handleCopy(msg.content, index)}
                  size="small"
                  sx={{ position: 'absolute', top: 0, right: 0 }}
                >
                  <ContentCopyIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          ) : (
            <Typography variant="body1">{msg.content}</Typography>
          )}
        </Box>
      ))}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
          <CircularProgress />
        </Box>
      )}
      <div ref={endOfMessagesRef} />
    </Box>
  );
};

export default ChatWindow;
