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
    <Container maxWidth="lg" style={{ marginTop: '20px' }}>
      <Grid container spacing={2}>
        {/* Chat History Sidebar with Hardware Metrics */}
        <Grid item xs={12} md={4} style={{ display: 'flex', flexDirection: 'column', height: '80vh' }}>
          <Paper style={{ padding: '10px', flex: 3, overflowY: 'auto' }}>
            <Typography variant="h6">Chat Sessions</Typography>
            <Divider sx={{ my: 1 }} />
            {sessions.map((session) => (
              <div key={session.id}>
                <Typography variant="body2" onClick={() => loadChatHistory(session.id)} style={{ cursor: 'pointer' }}>
                  Session {session.id}
                </Typography>
                <Divider />
              </div>
            ))}
          </Paper>

          {/* Hardware Metrics - Color Coded and Scrollable */}
          <Paper style={{ padding: '10px', flex: 1, marginTop: '10px', overflowY: 'auto', backgroundColor: '#f8f9fa' }}>
            <Typography variant="h6" style={{ color: '#007bff' }}>Hardware Metrics</Typography>
            <HardwareMetrics />
          </Paper>
        </Grid>

        {/* Chat Window */}
        <Grid item xs={12} md={8}>
          <Paper style={{ padding: '10px', height: '80vh', display: 'flex', flexDirection: 'column' }}>
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
