#backend/reasoning.py (remove call to ollama, this call has now been refactored)
import json
#from ollama import call_ollama_api  # No longer needed, using langchain
from typing import Optional

import os

def load_reasoning_templates():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, "reasoning_templates.json")
    with open(file_path, "r") as file:
        return json.load(file)

reasoning_templates = load_reasoning_templates()
reasoning_models = {"deepseek-r1"}

def auto_select_reasoning(question):
    if "why" in question.lower(): return "explanatory"
    if "compare" in question.lower() or "difference" in question.lower(): return "comparative"
    if "steps" in question.lower() or "process" in question.lower(): return "step_by_step"
    if "alternatives" in question.lower(): return "alternatives"
    return "default"

def generate_reasoning_prompt(question, user_selected_reasoning=None):
    reasoning_style = user_selected_reasoning or auto_select_reasoning(question)
    template = reasoning_templates.get(reasoning_style, reasoning_templates["default"])
    return f"""I want to understand how you arrive at your answer. {template} Question: {question}
**Answer:**

**Reasoning:**"""

from backend.api.web_search import web_search

async def route_to_browser(prompt: str) -> Optional[str]:
    """
    Determines if a prompt requires web browsing and returns search results if so.
    """
    # Keywords that suggest a web search is needed
    search_keywords = [
        "search for", "what is", "who is", "when is", "where is",
        "latest news on", "current events", "stock price of",
        "how to", "what are the reviews for"
    ]

    if any(keyword in prompt.lower() for keyword in search_keywords):
        try:
            # Extract the query from the prompt
            query = prompt
            for keyword in search_keywords:
                if keyword in prompt.lower():
                    # A simple way to extract the query after the keyword
                    query = prompt.lower().split(keyword)[1].strip()
                    break

            search_results = await web_search(query)
            # Format the results for the model
            formatted_results = []
            if search_results.get("results"):
                for result in search_results["results"][:3]: # Limit to top 3 results
                    formatted_results.append(f"- Title: {result['title']}\n  URL: {result['url']}\n  Snippet: {result['snippet']}")
                return "\n".join(formatted_results)
            else:
                return "No search results found."

        except Exception as e:
            print(f"Error during web search: {e}")
            return None

    return None

#No longer need call_ollama_with_reasoning, this function is no longer called in chat.py