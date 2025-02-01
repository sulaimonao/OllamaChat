import React, { useState, useEffect } from 'react';
import { FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import axios from 'axios';

const ModelSelector = ({ selectedModel, setSelectedModel }) => {
  const [models, setModels] = useState([]);

  useEffect(() => {
    axios.get('http://127.0.0.1:8000/models')
      .then(response => {
        setModels(response.data.models);
        if (response.data.models.length > 0 && !selectedModel) {
          setSelectedModel(response.data.models[0]);
        }
      })
      .catch(error => {
        console.error('Error fetching models:', error);
      });
  }, [selectedModel, setSelectedModel]);

  const handleChange = (event) => {
    setSelectedModel(event.target.value);
  };

  return (
    <FormControl fullWidth sx={{ marginBottom: 2 }}>
      <InputLabel id="model-selector-label">Select Model</InputLabel>
      <Select
        labelId="model-selector-label"
        id="model-selector"
        value={selectedModel}
        label="Select Model"
        onChange={handleChange}
      >
        {models.length > 0 ? models.map((model, index) => (
          <MenuItem key={index} value={model}>{model}</MenuItem>
        )) : (
          <MenuItem value="model1">Model 1</MenuItem>
        )}
      </Select>
    </FormControl>
  );
};

export default ModelSelector;
