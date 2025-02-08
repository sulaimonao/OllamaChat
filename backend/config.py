# backend/config.py
import os
import json
import logging

def load_system_prompts(prompts_dir=None):
    """Loads system prompts from JSON files in the specified directory."""

    if prompts_dir is None:
        prompts_dir = os.path.join(os.path.dirname(__file__), "system_prompts")

    system_prompts = {}
    try:
        if not os.path.exists(prompts_dir):
            logging.warning(f"System prompts directory not found: {prompts_dir}")
            return {"default": {"description": "Default Assistant", "prompt": "You are a helpful assistant."}}
        for filename in os.listdir(prompts_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(prompts_dir, filename)
                try:
                    with open(filepath, "r") as f:
                        prompt_data = json.load(f)
                        # Validate the structure of the loaded JSON
                        if not isinstance(prompt_data, dict):
                            logging.warning(f"Invalid system prompt format in {filename}: Expected a dictionary.")
                            continue
                        for key, value in prompt_data.items():
                            if not isinstance(value, dict) or "description" not in value or "prompt" not in value:
                                logging.warning(f"Invalid system prompt format in {filename}: Missing 'description' or 'prompt' in key '{key}'.")
                                continue
                            system_prompts[key] = value

                except json.JSONDecodeError:
                    logging.error(f"Error decoding JSON in {filename}")
                except Exception as e:
                    logging.exception(f"Error loading system prompt from {filename}")

    except Exception as e:
        logging.exception(f"Error loading system prompts from {prompts_dir}")
        return {"default": {"description": "Default Assistant", "prompt": "You are a helpful assistant."}}

    if not system_prompts:
        logging.warning("No valid system prompts found.")
        system_prompts = {"default": {"description": "Default Assistant", "prompt": "You are a helpful assistant."}}

    return system_prompts