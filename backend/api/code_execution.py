# backend/api/code_execution.py
from fastapi import APIRouter
from pydantic import BaseModel
from code_execution import executor

router = APIRouter()


class CodeExecutionRequest(BaseModel):
    code: str
    language: str


class FileContentRequest(BaseModel):
    content: str


@router.post("/workspace/{workspace_id}/execute")
async def execute_code_endpoint(workspace_id: str, request: CodeExecutionRequest):
    return executor.execute_code(request.code, request.language, workspace_id)


@router.get("/workspace/{workspace_id}/file/{filename}")
async def read_file_endpoint(workspace_id: str, filename: str):
    content = executor.read_file(workspace_id, filename)
    return {"content": content}


@router.post("/workspace/{workspace_id}/file/{filename}")
async def write_file_endpoint(workspace_id: str, filename: str, request: FileContentRequest):
    executor.write_file(workspace_id, filename, request.content)
    return {"message": "File written successfully"}
