import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the backend directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.chat import send_chat_message
from schemas import ChatRequest

@patch('docker.from_env')
class TestAutoToolUse(unittest.TestCase):

    @patch('api.chat.crud')
    @patch('api.chat.AgentExecutor')
    @patch('api.chat.ChatOllama')
    def test_search_tool_is_called(self, mock_chat_ollama, mock_agent_executor, mock_crud, mock_docker):
        # --- Arrange ---
        # Mock the docker client is now done by the class decorator
        mock_docker.return_value = MagicMock()
        # Mock the database session and crud functions
        mock_db = MagicMock()
        mock_crud.get_db.return_value = mock_db
        mock_crud.get_session.return_value = MagicMock(id=1, workspace_id="test_ws")

        # Mock the agent executor to simulate a tool call
        async def mock_ainvoke_side_effect(*args, **kwargs):
            return {"output": "The answer is python. Sources: [test.txt]"}
        mock_agent_executor.return_value.ainvoke.side_effect = mock_ainvoke_side_effect

        # --- Act ---
        chat_request = ChatRequest(
            session_id=1,
            message="What is the test file about?",
            model_id="test_model"
        )

        # This is an async function, but we can run it synchronously for the test
        import asyncio
        response = asyncio.run(send_chat_message(chat_request, db=mock_db))

        # --- Assert ---
        # Assert that the agent was invoked
        mock_agent_executor.return_value.ainvoke.assert_called_once()

        # Assert that the final response contains a citation
        self.assertIn("Sources:", response.model_message)

if __name__ == '__main__':
    unittest.main()
