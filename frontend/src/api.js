    // frontend/src/api.js
    import axios from 'axios';

    const API_URL = 'http://127.0.0.1:8000'; //backend url

    export const createSession = async () => {
      const response = await axios.post(`${API_URL}/session`);
      return response.data;
    };

    // Updated to include reasoning_style and image
    export const sendChatMessage = async (sessionId, modelId, message, persona, imageBase64, reasoning_style) => {
        const payload = {
          session_id: sessionId,
          model_id: modelId,
          message: message,
          reasoning_style: reasoning_style,
          image: imageBase64, // Add image to payload
          persona: persona
        };
        const response = await axios.post(`${API_URL}/chat`, payload);
        return response.data;
    };

    // Add getChatHistory function (THIS WAS MISSING)
    export const getChatHistory = async (sessionId) => {
        const response = await axios.get(`${API_URL}/chat/${sessionId}`);
        return response.data;
    };

    // Add a function to fetch the available custom models
    export const getCustomModels = async () => {
      const response = await axios.get(`${API_URL}/custom_models`);
      return response.data;
    };

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

    // Keep these for the workspace management tab:
    export const createWorkspace = async () => {
      const response = await axios.post(`${API_URL}/workspace/create`);
      return response.data;
    };

    export const deleteWorkspace = async (workspaceId) => {
      const response = await axios.delete(`${API_URL}/workspace/${workspaceId}`);
      return response.data;
    };

    export const getSystemPrompts = async () => {
      const response = await axios.get(`${API_URL}/system_prompts`);
      return response.data;
    };