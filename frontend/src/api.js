    // frontend/src/api.js
    import axios from 'axios';
    import { API_URL } from './config';

    export const createSession = async () => {
      const response = await axios.post(`${API_URL}/session`);
      return response.data;
    };

    export const sendChatMessage = async (sessionId, modelId, message, persona, file, useBrowser, workspaceId) => {
      const formData = new FormData();
      formData.append('session_id', sessionId);
      formData.append('model_id', modelId);
      formData.append('message', message);
      formData.append('persona', persona || '');
      formData.append('use_browser', useBrowser);
      if (workspaceId) {
        formData.append('workspace_id', workspaceId);
      }

      if (file) {
        formData.append('file', file);
      }

      const response = await axios.post(`${API_URL}/chat`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
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
      console.log("Raw response from /system_prompts:", response); // Keep for debugging
      return response.data;
    };
