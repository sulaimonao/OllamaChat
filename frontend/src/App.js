// frontend/src/App.js
import './App.css';
import React, { useState, useEffect } from 'react';
import { Container, Grid, Paper, Typography, Divider, Box, Tabs, Tab } from '@mui/material'; // Import Tabs and Tab
import ChatWindow from './components/ChatWindow';
import MessageInput from './components/MessageInput';
import ModelSelector from './components/ModelSelector';
import HardwareMetrics from './components/HardwareMetrics';
import { createSession, getChatHistory, sendChatMessage, getCustomModels } from './api';
import WorkspaceManager from './components/WorkspaceManager'; // Import the new component


function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [availableModels, setAvailableModels] = useState([]);
  const [tabValue, setTabValue] = useState(0); // State for tab index

  useEffect(() => {
    getCustomModels()
      .then((data) => {
        setAvailableModels(data.models);
        if (data.models.length > 0 && !selectedModel) {
          setSelectedModel(data.models[0]);
        }
      })
      .catch((error) => {
        console.error("Error fetching custom models:", error);
      });
  }, [selectedModel]);

    useEffect(() => {
    if (!sessionId) {
      createSession().then((newSession) => {
        if (newSession) {
          setSessionId(newSession.id);
          setMessages([]);
          setSessions((prev) => [...prev, newSession]);

          getCustomModels()
            .then((data) => {
              setAvailableModels(data.models);
            });
        }
      });
    }
  }, [sessionId]);

  const handleSendMessage = async (messageText, reasoning_style, fileInfo, imageBase64, persona) => { // Add imageBase64
    setIsLoading(true);
    try {
      // Include file information in the message sent to the backend
      const fullMessage = fileInfo ? `${messageText}\n${fileInfo}` : messageText;

      // Now send the image along with other data
      const response = await sendChatMessage(sessionId, selectedModel, fullMessage, reasoning_style, imageBase64, persona);

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

  const loadChatHistory = async (sessionId) => {
    try {
      const sessionData = await getChatHistory(sessionId);
      if (sessionData) {
        setSessionId(sessionData.id);
        setMessages(sessionData.messages);
      }
    } catch (error) {
      console.error('Error fetching chat history:', error);
      alert('Error fetching chat history');
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Tabs value={tabValue} onChange={handleTabChange} aria-label="main tabs">
        <Tab label="Chat" />
        <Tab label="Workspace" />
      </Tabs>

      {tabValue === 0 && ( // Chat Tab
        <Grid container spacing={2}>
          <Grid item xs={12} md={4} sx={{ display: 'flex', flexDirection: 'column', height: '75vh' }}>
            <Paper elevation={3} sx={{ p: 2, flex: 3, overflowY: 'auto' }}>
              <Typography variant="h6" gutterBottom>Chat Sessions</Typography>
              <Divider sx={{ my: 1 }} />
              {sessions.map((session) => (
                <Box key={session.id} sx={{ py: 0.5, cursor: 'pointer' }} onClick={() => loadChatHistory(session.id)}>
                  <Typography variant="body2">Session {session.id} - {session.workspace_id}</Typography>
                  <Divider />
                </Box>
              ))}</Paper>
            <Paper elevation={3} sx={{ p: 2, flex: 1, mt: 2, overflowY: 'auto', bgcolor: '#f8f9fa' }}>
              <Typography variant="h6" color="primary" gutterBottom>Hardware Metrics</Typography>
              <HardwareMetrics />
            </Paper>
          </Grid>

          <Grid item xs={12} md={8}>
            <Paper elevation={3} sx={{ p: 2, height: '75vh', display: 'flex', flexDirection: 'column' }}>
              <Typography variant="h6" gutterBottom>Chat Session {sessionId}</Typography>
              <ModelSelector selectedModel={selectedModel} setSelectedModel={setSelectedModel} availableModels={availableModels} sx={{ mb: 2 }} />
              <ChatWindow messages={messages} isLoading={isLoading} sx={{ flexGrow: 1 }} />
              <MessageInput onSendMessage={handleSendMessage}  />
            </Paper>
          </Grid>
        </Grid>
      )}

      {tabValue === 1 && ( // Workspace Tab
        <WorkspaceManager />
      )}
    </Container>
  );
}

export default App;