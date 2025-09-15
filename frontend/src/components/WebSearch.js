// frontend/src/components/WebSearch.js
import React, { useState } from 'react';
import { Box, TextField, Button, Typography, List, ListItem, Divider } from '@mui/material';
import axios from 'axios';
import { API_URL } from '../config';

const WebSearch = ({ onAddMessage }) => {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/search`, { params: { query } });
      const data = response.data;
      // Build a message that summarizes the search result.
      const searchMessage = `**Web Search Result for "${query}":**\n\nAbstract: ${data.abstract || "No abstract available."}\n\n` +
        (data.related_topics && data.related_topics.length > 0
          ? "Related Topics:\n" + data.related_topics.map((topic, idx) => `- ${topic.Text || topic.Name}`).join("\n")
          : "");
      // Add the search result as a message in the conversation.
      if (onAddMessage) {
        onAddMessage({ sender: "search", content: searchMessage });
      }
    } catch (error) {
      console.error("Error during web search:", error);
    } finally {
      setLoading(false);
      setQuery("");  // Clear the search box if desired.
    }
  };

  return (
    <Box sx={{ p: 2, mb: 2, border: '1px solid #ccc', borderRadius: 1 }}>
      <Typography variant="h6">Web Search</Typography>
      <Box sx={{ display: 'flex', mt: 1 }}>
        <TextField
          fullWidth
          placeholder="Enter search query..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button variant="contained" onClick={handleSearch} sx={{ ml: 1 }}>Search</Button>
      </Box>
      {loading && <Typography variant="body2">Loading search results...</Typography>}
    </Box>
  );
};

export default WebSearch;
