// frontend/src/components/ChatWindow.js
import React, { useRef, useEffect } from 'react';
import { Box, Typography, CircularProgress, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ReactMarkdown from 'react-markdown';
import CodeBlock from './CodeBlock';
import ReasoningView from './ReasoningView';

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
          {msg.browser_results && (
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="body2">Show Browser Results</Typography>
              </AccordionSummary>
              <AccordionDetails>
                {msg.browser_results.map((result, i) => (
                  <Box key={i} sx={{ mb: 1 }}>
                    <Typography variant="body2" component="a" href={result.url} target="_blank" rel="noopener noreferrer">
                      {result.title}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                      {result.snippet}
                    </Typography>
                  </Box>
                ))}
              </AccordionDetails>
            </Accordion>
          )}
          {msg.sender === 'model' ? (
            <ReactMarkdown components={{ code: CodeBlock }}>
              {msg.content}
            </ReactMarkdown>
          ) : (
            <Typography variant="body1">{msg.content}</Typography>
          )}
          {msg.reasoning && <ReasoningView reasoning={msg.reasoning} />}
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
