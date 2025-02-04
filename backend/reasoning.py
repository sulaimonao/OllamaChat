# backend/reasoning.py
import json
from ollama import call_ollama_cli

def load_reasoning_templates():
    with open("reasoning_templates.json", "r") as file:
        return json.load(file)

reasoning_templates = load_reasoning_templates()

reasoning_models = {"deepseek-r1"}  # Add more local reasoning models here

def auto_select_reasoning(question):
    if "why" in question.lower():
        return "explanatory"
    elif "compare" in question.lower() or "difference" in question.lower():
        return "comparative"
    elif "steps" in question.lower() or "process" in question.lower():
        return "step_by_step"
    elif "alternatives" in question.lower():
        return "alternatives"
    else:
        return "default"

def generate_reasoning_prompt(question, user_selected_reasoning=None):
    reasoning_style = user_selected_reasoning or auto_select_reasoning(question)
    template = reasoning_templates.get(reasoning_style, reasoning_templates["default"])
    return f"""I want to understand how you arrive at your answer. {template} Question: {question}

**Answer:**

**Reasoning:**"""

def call_ollama_with_reasoning(model, question, reasoning_style=None):
    if model.split(":")[0] in reasoning_models:
        prompt = generate_reasoning_prompt(question, reasoning_style)
    else:
        prompt = question
    
    return call_ollama_cli(model, prompt)