"""Small helper script showing how to query a local Ollama model from Python.

Usage:
    # make sure `ollama serve` is running in another terminal
    python ollama_example.py

This will send a prompt to the llama2 model you've pulled and
print the resulting text.  You can adapt `send_prompt` for use in
your Pygame project to generate dialogue, descriptions, etc.
"""

import json
import subprocess
from typing import Any, Dict

import requests

# --- configuration ---------------------------------------------------------
OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "llama2"  # change if you pulled another model

# --- http helper -----------------------------------------------------------

def send_prompt_http(prompt: str, max_tokens: int = 200) -> str:
    """Send a prompt to the local Ollama HTTP API.

    Requires `ollama serve` or `ollama run <model>` listening on 11434.
    """
    url = f"{OLLAMA_HOST}/v1/completions"
    headers = {"Content-Type": "application/json"}
    payload: Dict[str, Any] = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "max_tokens": max_tokens,
    }

    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    # the structure mirrors OpenAI; choices[0].text holds the answer
    return data.get("choices", [{}])[0].get("text", "")

# --- cli helper ------------------------------------------------------------

def send_prompt_cli(prompt: str) -> str:
    """Alternative: invoke `ollama query` via subprocess."""
    result = subprocess.run(
        ["ollama", "query", MODEL_NAME, "--prompt", prompt],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


# --- demo ------------------------------------------------------------------

if __name__ == "__main__":
    example = "Donne-moi un petit poème sur la mer"
    print("Prompt:", example)
    print("Using HTTP API...")
    try:
        answer = send_prompt_http(example)
        print("Response:\n", answer)
    except Exception as exc:
        print("HTTP error, falling back to CLI:", exc)
        print("Response CLI:\n", send_prompt_cli(example))
