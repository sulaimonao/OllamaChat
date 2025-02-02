// frontend/src/components/ChatWindow.js
import React, { useRef, useEffect } from 'react';
import { Box, Typography, CircularProgress } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import CodeBlock from './CodeBlock';

const ChatWindow = ({ messages, isLoading }) => {
  const endOfMessagesRef = useRef(null);

  // Scroll to the latest message when messages or loading state changes.
  useEffect(() => {
    if (endOfMessagesRef.current) {
      endOfMessagesRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading]);

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
        <Box key={index} sx={{ marginBottom: 2 }}>
          <Typography variant="subtitle2" color={msg.sender === 'user' ? 'primary' : 'secondary'}>
            {msg.sender === 'user' ? 'You' : 'Model'}
          </Typography>
          {msg.sender === 'model' ? (
            // Render markdown with custom code block rendering.
            <ReactMarkdown components={{ code: CodeBlock }}>
              {msg.content}
            </ReactMarkdown>
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
