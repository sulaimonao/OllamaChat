# backend/code_execution/executor.py
import docker
import os
import uuid
import time
import logging
from typing import Optional
from fastapi import HTTPException

client = docker.from_env()

# Configuration (consider moving this to a config file)
BASE_WORKSPACE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "workspaces")  # Top-level workspaces dir
IMAGE_NAME = "code-executor:latest"  # Name of the Docker image
TIMEOUT_SECONDS = 60  # Maximum execution time
MEMORY_LIMIT = "512m"  # Memory limit

os.makedirs(BASE_WORKSPACE_DIR, exist_ok=True)


def create_workspace():
    """Creates a unique workspace directory for a session."""
    workspace_id = str(uuid.uuid4())
    workspace_path = os.path.join(BASE_WORKSPACE_DIR, workspace_id)
    os.makedirs(workspace_path, exist_ok=True)
    return workspace_id, workspace_path


def delete_workspace(workspace_id: str):
    """Deletes a workspace directory."""
    workspace_path = os.path.join(BASE_WORKSPACE_DIR, workspace_id)
    try:
        # Use a more robust deletion method (e.g., shutil.rmtree)
        for root, dirs, files in os.walk(workspace_path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(workspace_path)
    except FileNotFoundError:
        pass  # Ignore if already deleted
    except Exception as e:
        logging.error(f"Error deleting workspace {workspace_id}: {e}")


def execute_code(code: str, language: str, workspace_id: str) -> dict:
    """Executes code within a Docker container."""
    workspace_path = os.path.join(BASE_WORKSPACE_DIR, workspace_id)
    print(f"Attempting to execute code in: {workspace_path}") #ADD LOG
    if not os.path.exists(workspace_path):
        raise HTTPException(status_code=404, detail="Workspace not found")

    try:
        # Create a unique file name for the code
        file_name = f"script.{'py' if language == 'python' else 'js'}" # Expand as needed
        file_path = os.path.join(workspace_path, file_name)

        # Write the code to the file within the workspace
        with open(file_path, "w") as f:
            f.write(code)

        # --- Prepare Docker command ---
        if language == "python":
            command = ["python", file_name]
        elif language == "javascript":
            command = ["node", file_name]
        # Add more language support as needed (e.g., Java, C++, etc.)
        else:
            raise ValueError(f"Unsupported language: {language}")

        # --- Run the container ---
        container = client.containers.run(
            IMAGE_NAME,
            command,
            volumes={workspace_path: {"bind": "/app", "mode": "rw"}},  # Mount workspace
            network_disabled=True,  # Disable network access
            mem_limit=MEMORY_LIMIT,  # Set memory limit
            detach=True,  # Run in detached mode
        )

        # Wait for the container to finish (with timeout)
        start_time = time.time()
        while container.status != 'exited':
            time.sleep(0.1)
            if time.time() - start_time > TIMEOUT_SECONDS:
                container.kill()
                return {"output": "Timeout: Code execution exceeded time limit.", "error": True}
            container.reload() #Update status

        # Get output
        output = container.logs(stdout=True, stderr=True).decode("utf-8")
        container.remove()  # Clean up the container

        return {"output": output, "error": False}

    except docker.errors.ImageNotFound:
        logging.error(f"Docker image not found: {IMAGE_NAME}")
        return {"output": f"Error: Docker image '{IMAGE_NAME}' not found. Build it first.", "error": True}
    except Exception as e:
        logging.exception(f"Error executing code: {e}")
        return {"output": f"Error: {e}", "error": True}


def read_file(workspace_id: str, filename: str) -> str:
    """Reads a file from the model's workspace."""
    workspace_path = os.path.join(BASE_WORKSPACE_DIR, workspace_id)
    file_path = os.path.join(workspace_path, filename)

    # --- Security Check: Prevent path traversal ---
    if not os.path.realpath(file_path).startswith(os.path.realpath(workspace_path)):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        with open(file_path, "r") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))


def write_file(workspace_id: str, filename: str, content: str):
    """Writes a file to the model's workspace."""
    workspace_path = os.path.join(BASE_WORKSPACE_DIR, workspace_id)
    file_path = os.path.join(workspace_path, filename)
    try:
        #Prevent overwriting files outside of the workspace
        if not os.path.realpath(file_path).startswith(os.path.realpath(workspace_path)):
            raise HTTPException(status_code=403, detail="Access Denied.")
        with open(file_path, "w") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write to file. {str(e)}")