// frontend/src/api.js
import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000'; //backend url

export const createSession = async () => {
  const response = await axios.post(`${API_URL}/session`);
  return response.data;
};

// Updated to include reasoning_style
export const sendChatMessage = async (sessionId, modelId, message, reasoning_style) => {
  const payload = {
    session_id: sessionId,
    model_id: modelId,
    message: message,
    reasoning_style: reasoning_style
  };
  const response = await axios.post(`${API_URL}/chat`, payload);
  return response.data;
};

export const getChatHistory = async (sessionId) => {
  const response = await axios.get(`${API_URL}/chat/${sessionId}`);
  return response.data;
};

// Add other API functions as needed (no changes required for these)
export const getModels = async () => {
  const response = await axios.get(`${API_URL}/models`);
  return response.data;
};

export const getMetrics = async () => {
  const response = await axios.get(`${API_URL}/metrics`);
  return response.data;
};

export const webSearch = async (query) => {
  const response = await axios.get(`${API_URL}/search`, { params: { query } });
  return response.data;
};

export const uploadFile = async (formData) => {
  const response = await axios.post(`${API_URL}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};