// frontend/src/App.js
import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Divider,
  CircularProgress
} from '@mui/material';
import ChatWindow from './components/ChatWindow';
import MessageInput from './components/MessageInput';
import ModelSelector from './components/ModelSelector';
import { createSession, getChatHistory, sendChatMessage } from './api';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Create a new session on initial load if one doesn't exist.
  useEffect(() => {
    if (!sessionId) {
      createSession().then((newSession) => {
        setSessionId(newSession.id);
        setMessages([]);
        // Add the new session to the sessions list.
        setSessions((prev) => [...prev, newSession]);
      });
    }
  }, [sessionId]);

  // Handle sending a message.
  const handleSendMessage = async (messageText) => {
    setIsLoading(true);
    try {
      const response = await sendChatMessage(sessionId, selectedModel, messageText);
      // Append both the user's message and the model's response.
      setMessages((prev) => [
        ...prev,
        { sender: 'user', content: response.user_message },
        { sender: 'model', content: response.model_message },
      ]);
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Error sending message');
    } finally {
      setIsLoading(false);
    }
  };

  // Load chat history for the selected session.
  const loadChatHistory = async (sessionId) => {
    try {
      const sessionData = await getChatHistory(sessionId);
      setSessionId(sessionData.id);
      setMessages(sessionData.messages);
    } catch (error) {
      console.error('Error fetching chat history:', error);
      alert('Error fetching chat history');
    }
  };

  return (
    <Container maxWidth="lg" style={{ marginTop: '20px' }}>
      <Grid container spacing={2}>
        {/* Chat History Sidebar */}
        <Grid item xs={12} md={3}>
          <Paper style={{ padding: '10px', height: '80vh', overflowY: 'auto' }}>
            <Typography variant="h6">Chat Sessions</Typography>
            <List>
              {sessions.map((session) => (
                <div key={session.id}>
                  <ListItem disablePadding>
                    <ListItemButton onClick={() => loadChatHistory(session.id)}>
                      <ListItemText primary={`Session ${session.id}`} />
                    </ListItemButton>
                  </ListItem>
                  <Divider />
                </div>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Chat Window */}
        <Grid item xs={12} md={9}>
          <Paper
            style={{
              padding: '10px',
              height: '80vh',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <Typography variant="h6">Chat Session {sessionId}</Typography>
            <ModelSelector selectedModel={selectedModel} setSelectedModel={setSelectedModel} />
            <ChatWindow messages={messages} isLoading={isLoading} />
            <MessageInput onSendMessage={handleSendMessage} />
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}

export default App;
