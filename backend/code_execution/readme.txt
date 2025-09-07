# Code Execution

This module allows the chat application to run small snippets of Python or
JavaScript inside an isolated Docker container. Each session gets its own
workspace so files created during execution are kept separate.

## Build the Docker image

1. Install and start Docker on your machine.
2. From the `backend/code_execution` directory build the runtime image:

   ```bash
   docker build -t code-executor:latest .
   ```

## Workspace management

Workspaces live under `backend/workspaces` and are created via the backend API.

```bash
# Create a workspace
curl -X POST http://localhost:8000/workspace/create

# List existing workspaces
curl http://localhost:8000/workspaces

# Delete a workspace
curl -X DELETE http://localhost:8000/workspace/<workspace_id>
```

The create endpoint returns a JSON object with a `workspace_id` that is used for
subsequent code and file operations.

## Run code

Code is executed inside the workspace with the helper function
`execute_code`.

```python
from code_execution.executor import create_workspace, execute_code

workspace_id, _ = create_workspace()
result = execute_code("print('hello world')", "python", workspace_id)
print(result["output"])
```

## Access files

Files in the workspace can be accessed with `read_file` and `write_file`:

```python
from code_execution.executor import write_file, read_file

write_file(workspace_id, "notes.txt", "some text")
print(read_file(workspace_id, "notes.txt"))
```

## Sample UI flow

1. The user starts a new chat session – the backend creates a workspace.
2. When the model needs to run code, the backend calls `execute_code` inside
   that workspace and returns the output.
3. Generated files can be viewed by requesting them with `read_file` or by
   listing the workspace contents.

Docker must remain running in the background for code execution to work.

