// frontend/src/components/WorkspaceManager.js
import React, { useState, useEffect } from 'react';
import { Box, Typography, List, ListItem, ListItemText, Button, TextField } from '@mui/material';
import { createWorkspace, deleteWorkspace } from '../api';
import {ListSubheader} from '@mui/material';

const WorkspaceManager = () => {
  const [workspaces, setWorkspaces] = useState([]);
  const [newWorkspaceName, setNewWorkspaceName] = useState(''); //If you support custom naming

  //TODO: Implement a /list_workspaces route on the backend to display a list of workspaces.
  useEffect(() => {
    // Fetch workspaces (you'll need a backend endpoint for this)
    // Example:
    // fetchWorkspaces().then(data => setWorkspaces(data));
    const mockWorkspaces = [{id: "123", name: "abc"}, {id: "456", name: "def"}];
    setWorkspaces(mockWorkspaces)
  }, []);

  const handleCreateWorkspace = async () => {
    const response = await createWorkspace();
    //Refresh workspace
    const mockWorkspaces = [{id: "123", name: "abc"}, {id: "456", name: "def"}, {id: response.workspace_id, name: response.workspace_id}];
    setWorkspaces(mockWorkspaces)
  };

  const handleDeleteWorkspace = async (workspaceId) => {
    await deleteWorkspace(workspaceId);
    //Refresh workspace list
    const mockWorkspaces = [{id: "123", name: "abc"}, {id: "456", name: "def"}];
    setWorkspaces(mockWorkspaces)
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
      {/* Add UI for file browsing/editing here */}
    </Box>
  );
};

export default WorkspaceManager;