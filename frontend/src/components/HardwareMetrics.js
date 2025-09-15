// frontend/src/components/HardwareMetrics.js
import React, { useState, useEffect } from 'react';
import { Box, Typography, Grid, Paper } from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import axios from 'axios';
import { API_URL } from '../config';

const HardwareMetrics = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchMetrics = async () => {
    try {
      const response = await axios.get(`${API_URL}/metrics`);
      setMetrics(response.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching metrics:", error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []); // Empty dependency array

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!metrics) {
    return <Typography variant="body1">No metrics available.</Typography>;
  }

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="h6" gutterBottom>
        Hardware Metrics
      </Typography>
      <Grid container spacing={2}>
        {/* CPU Metrics */}
        <Grid item xs={12} sm={6} md={3}>
          <Typography variant="subtitle2">CPU Usage</Typography>
          <Typography variant="body1">{metrics.cpu.usage_percent}%</Typography>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Typography variant="subtitle2">CPU Frequency</Typography>
          <Typography variant="body1">
            {metrics.cpu.frequency ? `${metrics.cpu.frequency.toFixed(2)} MHz` : "N/A"}
          </Typography>
        </Grid>
        {/* Memory Metrics */}
        <Grid item xs={12} sm={6} md={3}>
          <Typography variant="subtitle2">Memory Usage</Typography>
          <Typography variant="body1">{metrics.memory.usage_percent}%</Typography>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Typography variant="subtitle2">Memory (Used/Total)</Typography>
          <Typography variant="body1">
            {(metrics.memory.used / (1024 ** 3)).toFixed(2)} GB / {(metrics.memory.total / (1024 ** 3)).toFixed(2)} GB
          </Typography>
        </Grid>
        {/* Disk I/O Metrics */}
        <Grid item xs={12} sm={6} md={3}>
          <Typography variant="subtitle2">Disk Read</Typography>
          <Typography variant="body1">
            {(metrics.disk.read_bytes / (1024 ** 2)).toFixed(2)} MB
          </Typography>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Typography variant="subtitle2">Disk Write</Typography>
          <Typography variant="body1">
            {(metrics.disk.write_bytes / (1024 ** 2)).toFixed(2)} MB
          </Typography>
        </Grid>
        {/* GPU Metrics (if any) */}
        {metrics.gpu.length > 0 && metrics.gpu.map((gpu, idx) => (
          <Grid item xs={12} sm={6} md={3} key={idx}>
            <Typography variant="subtitle2">GPU: {gpu.name}</Typography>
            <Typography variant="body1">Load: {gpu.load.toFixed(2)}%</Typography>
            <Typography variant="body1">
              Memory: {gpu.memoryUsed} / {gpu.memoryTotal} MB
            </Typography>
            <Typography variant="body1">Temp: {gpu.temperature}°C</Typography>
          </Grid>
        ))}
        {/* System Info */}
        <Grid item xs={12}>
          <Typography variant="subtitle2">System Info</Typography>
          <Typography variant="body2">
            {metrics.system_info.system} - {metrics.system_info.platform}<br/>
            CPU: {metrics.system_info.cpu_model}<br/>
            Machine: {metrics.system_info.machine}
          </Typography>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default HardwareMetrics;
