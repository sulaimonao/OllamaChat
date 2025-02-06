// frontend/src/components/ModelSelector.js
import React, { useState, useEffect } from 'react';
import { FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import { getModels, getCustomModels } from '../api'; // Import BOTH API functions

const ModelSelector = ({ selectedModel, setSelectedModel }) => {
    const [ollamaModels, setOllamaModels] = useState([]);
    const [customModels, setCustomModels] = useState([]);
    const [loading, setLoading] = useState(true); // Add loading state
    const [error, setError] = useState(null); // Add error state

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            setError(null); // Clear previous errors
            try {
                const ollamaResponse = await getModels();
                const customResponse = await getCustomModels();
                setOllamaModels(ollamaResponse.models);
                setCustomModels(customResponse.models);

                // Select first model (if none selected)
                if (!selectedModel) {
                    const allModels = [...ollamaResponse.models, ...customResponse.models];
                    if (allModels.length > 0) {
                        setSelectedModel(allModels[0]);
                    }
                }
            } catch (err) {
                console.error("Error fetching models:", err);
                setError("Failed to load models."); // Set error message
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [selectedModel, setSelectedModel]); // Keep dependencies - they might be relevant

    const handleChange = (event) => {
        setSelectedModel(event.target.value);
    };

    const allModels = [...ollamaModels, ...customModels];


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
                {loading && <MenuItem value=""><em>Loading...</em></MenuItem>}
                {error && <MenuItem value=""><em>{error}</em></MenuItem>}
                {!loading && !error && allModels.length === 0 && (
                    <MenuItem value=""><em>No models available</em></MenuItem>
                )}

                {!loading && !error && allModels.length > 0 && allModels.map((model) => (
                    <MenuItem key={model} value={model}>{model}</MenuItem>
                ))}
            </Select>
        </FormControl>
    );
};

export default ModelSelector;