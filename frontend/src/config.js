// frontend/src/config.js
// Central configuration for frontend runtime variables.

// The backend API base URL can be provided via the
// environment variable REACT_APP_API_URL. During development
// it defaults to the local FastAPI server.
export const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

