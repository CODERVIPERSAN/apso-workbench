import os

# Deterministic CI / unit tests — no live Ollama calls
os.environ["APSO_LLM"] = "0"
