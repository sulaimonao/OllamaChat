import './App.css';
import React, { useState, useEffect } from 'react';
import { Container, Grid, Paper, Typography, Divider } from '@mui/material';
import ChatWindow from './components/ChatWindow';
import MessageInput from './components/MessageInput';
import ModelSelector from './components/ModelSelector';
import HardwareMetrics from './components/HardwareMetrics';
import { createSession, getChatHistory, sendChatMessage } from './api';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!sessionId) {
      createSession().then((newSession) => {
        setSessionId(newSession.id);
        setMessages([]);
        setSessions((prev) => [...prev, newSession]);
      });
    }
  }, [sessionId]);

  const handleSendMessage = async (messageText) => {
    setIsLoading(true);
    try {
      const response = await sendChatMessage(sessionId, selectedModel, messageText);
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
      setSessionId(sessionData.id);
      setMessages(sessionData.messages);
    } catch (error) {
      console.error('Error fetching chat history:', error);
      alert('Error fetching chat history');
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}> {/* Use sx for styling */}
      <Grid container spacing={2}>
        {/* Chat History Sidebar with Hardware Metrics */}
        <Grid item xs={12} md={4} sx={{ display: 'flex', flexDirection: 'column', height: '75vh' }}> {/* Adjusted height */}
          <Paper elevation={3} sx={{ p: 2, flex: 3, overflowY: 'auto' }}> {/* Use sx and elevation */}
            <Typography variant="h6" gutterBottom>Chat Sessions</Typography> {/* gutterBottom for spacing */}
            <Divider />
            {sessions.map((session) => (
              <Box key={session.id} sx={{ py: 0.5, cursor: 'pointer' }} onClick={() => loadChatHistory(session.id)}> {/* Box for better styling */}
                <Typography variant="body2">
                  Session {session.id}
                </Typography>
                <Divider />
              </Box>
            ))}
          </Paper>

          {/* Hardware Metrics - Color Coded and Scrollable */}
          <Paper elevation={3} sx={{ p: 2, flex: 1, mt: 2, overflowY: 'auto', bgcolor: '#f8f9fa' }}> {/* sx for styling */}
            <Typography variant="h6" color="primary" gutterBottom>Hardware Metrics</Typography> {/* Color with MUI theme */}
            <HardwareMetrics />
          </Paper>
        </Grid>

        {/* Chat Window */}
        <Grid item xs={12} md={8}>
          <Paper elevation={3} sx={{ p: 2, height: '75vh', display: 'flex', flexDirection: 'column' }}> {/* Adjusted height and elevation */}
            <Typography variant="h6" gutterBottom>Chat Session {sessionId}</Typography> {/* gutterBottom for spacing */}
            <ModelSelector selectedModel={selectedModel} setSelectedModel={setSelectedModel} sx={{ mb: 2 }} /> {/* Margin bottom with sx */}
            <ChatWindow messages={messages} isLoading={isLoading} sx={{ flexGrow: 1 }} /> {/* flexGrow to fill space */}
            <MessageInput onSendMessage={handleSendMessage} />
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}

export default App;
