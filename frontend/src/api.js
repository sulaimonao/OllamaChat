import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000'; // Backend URL

export const createSession = async () => {
  const response = await axios.post(`${API_URL}/session`);
  return response.data;
};

export const sendChatMessage = async (sessionId, modelId, message) => {
  const payload = {
    session_id: sessionId,  // make sure sessionId is a number
    model_id: modelId,
    message: message
  };
  const response = await axios.post(`${API_URL}/chat`, payload);
  return response.data;
};

export const getChatHistory = async (sessionId) => {
  const response = await axios.get(`${API_URL}/chat/${sessionId}`);
  return response.data;
};
