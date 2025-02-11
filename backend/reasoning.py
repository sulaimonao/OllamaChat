#backend/reasoning.py (remove call to ollama, this call has now been refactored)
import json
#from ollama import call_ollama_api  # No longer needed, using langchain
from typing import Optional

def load_reasoning_templates():
    with open("reasoning_templates.json", "r") as file:
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

#No longer need call_ollama_with_reasoning, this function is no longer called in chat.py