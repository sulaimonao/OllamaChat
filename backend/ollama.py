# backend/ollama.py
import subprocess
import logging

def call_ollama_cli(model: str, prompt: str) -> str:
    command = ["ollama", "run", model, prompt]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Error calling Ollama CLI: {e.stderr}")
        return "Error: Could not process your request."

def process_ollama_response(response):
    try:
        answer_start = response.index("**Answer:**") + len("**Answer:**")
        reasoning_start = response.index("**Reasoning:**") + len("**Reasoning:**")
        answer = response[answer_start:reasoning_start].strip()
        reasoning = response[reasoning_start:].strip()
        return {"reasoning": reasoning, "answer": answer}
    except ValueError:
        return {"reasoning": "Could not parse response. Check model output.", "answer": response.strip()}