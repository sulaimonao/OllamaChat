// frontend/src/components/WorkspaceManager.js
import React, { useState, useEffect } from 'react';
import { Box, Typography, List, ListItem, ListItemText, Button, TextField } from '@mui/material';
import { createWorkspace, deleteWorkspace } from '../api';
import {ListSubheader} from '@mui/material';
import axios from 'axios'; // Import axios

const WorkspaceManager = () => {
  const [workspaces, setWorkspaces] = useState([]);
  const [newWorkspaceName, setNewWorkspaceName] = useState(''); //If you support custom naming

  useEffect(() => {
    // Fetch workspaces from the backend
    const fetchWorkspaces = async () => {
        try{
            const response = await axios.get('http://127.0.0.1:8000/workspaces');
            setWorkspaces(response.data.workspaces);
        } catch (error) {
            console.error("Error fetching workspaces:", error);
            // Handle error (e.g., display an error message to the user)
        }
    }
    fetchWorkspaces();
  }, []);

  const handleCreateWorkspace = async () => {
    const response = await createWorkspace();
    //Refresh workspace
    setWorkspaces((prevWorkspaces) => [...prevWorkspaces, {id: response.workspace_id, name: response.workspace_id}])

  };

  const handleDeleteWorkspace = async (workspaceId) => {
    await deleteWorkspace(workspaceId);
    //Refresh workspace list
    setWorkspaces((prevWorkspaces) => prevWorkspaces.filter((workspace) => workspace.id !== workspaceId));
  };
  //TODO: implement file browsing.
  return (
    <Box>
      <Typography variant="h6">Workspace Management</Typography>

      <Button variant="contained" onClick={handleCreateWorkspace}>
        Create New Workspace
      </Button>

      <List component="nav" aria-labelledby="nested-list-subheader"
        subheader={
            <ListSubheader component="div" id="nested-list-subheader">
            Workspaces
            </ListSubheader>
        }>
        {workspaces.map((workspace) => (
          <ListItem key={workspace.id}>
            <ListItemText primary={workspace.name} secondary={"ID: "+workspace.id}/>
            <Button
              variant="outlined"
              color="error"
              onClick={() => handleDeleteWorkspace(workspace.id)}
            >
              Delete
            </Button>
          </ListItem>
        ))}
      </List>
      {/* Add UI for file browsing/editing here */}\
    </Box>
  );
};

export default WorkspaceManager;