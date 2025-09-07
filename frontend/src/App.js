// frontend/src/App.js
import './App.css';
import React, { useState, useEffect } from 'react';
import { Container, Grid, Paper, Typography, Divider, Box, Tabs, Tab } from '@mui/material';
import ChatWindow from './components/ChatWindow';
import MessageInput from './components/MessageInput';
import ModelSelector from './components/ModelSelector';
import HardwareMetrics from './components/HardwareMetrics';
import { createSession, getChatHistory, sendChatMessage, getCustomModels, getSystemPrompts } from './api';
import WorkspaceManager from './components/WorkspaceManager';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [availableModels, setAvailableModels] = useState([]);
  const [availablePersonas, setAvailablePersonas] = useState({});
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    getSystemPrompts()
      .then((data) => {
        console.log("System Prompts Data (App.js):", data); // Add this log
        setAvailablePersonas(data.system_prompts);
      })
      .catch((error) => {
        console.error("Error fetching system prompts:", error);
      });
  }, []);

  useEffect(() => {
    if (!sessionId) {
      createSession()
        .then((newSession) => {
          if (newSession) {
            console.log("New session created:", newSession);
            setSessionId(parseInt(newSession.id, 10));
            setMessages([]);
            setSessions((prev) => [...prev, newSession]);

            getCustomModels() // Fetch custom models *after* creating the session
              .then((data) => {
                setAvailableModels(data.models);
                if (data.models.length > 0 && !selectedModel) {
                  setSelectedModel(data.models[0]);
                }
              });
          }
        });
    }
  }, [sessionId, selectedModel]); // Depend on selectedModel as well

  const handleSendMessage = async (messageText, persona, fileInfo, imageBase64, reasoning_style, useBrowser) => {
    console.log("handleSendMessage called. sessionId:", sessionId, "selectedModel:", selectedModel, "persona", persona, "useBrowser", useBrowser);
    setIsLoading(true);
    try {
        const fullMessage = fileInfo ? `${messageText}\n${fileInfo}` : messageText;
        const currentSession = sessions.find((s) => s.id === sessionId);
        const workspaceId = currentSession ? currentSession.workspace_id : null;
        const response = await sendChatMessage(sessionId, selectedModel, fullMessage, persona, imageBase64, reasoning_style, useBrowser, workspaceId);

        // Create new message array
        const newMessages = [
            ...messages, // keep existing messages
            { sender: 'user', content: response.user_message },
            { sender: 'model', content: response.model_message, browser_results: response.browser_results, reasoning: response.reasoning },
        ]
        setMessages(newMessages)

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

          {tabValue === 0 && (
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
                  <MessageInput onSendMessage={handleSendMessage} availablePersonas={availablePersonas}  />
                </Paper>
              </Grid>
            </Grid>
          )}

          {tabValue === 1 && (
            <WorkspaceManager />
          )}
        </Container>
      );
    }

export default App;