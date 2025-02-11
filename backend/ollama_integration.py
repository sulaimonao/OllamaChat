# backend/ollama_integration.py 
from langchain_ollama import ChatOllama
import logging
from typing import Optional

def call_ollama_api(model: str, prompt: str, image: Optional[str] = None) -> str:
    """Calls the Ollama API to generate a response, handling images."""
    try:
        ollama = ChatOllama(model=model, base_url="http://localhost:11434")

        if image:
            messages = [
                {
                    "type": "human",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image}"}}
                    ],
                }
            ]
        else:
            messages = [
                {"type": "human", "content": prompt}
            ]

        response = ollama.invoke(messages)
        return response.content

    except Exception as e:
        logging.exception(f"Error calling Ollama API: {e}")
        return "Error: Could not process your request."