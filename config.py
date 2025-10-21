# Configuration settings for adversarial testing
import os
from dotenv import  load_dotenv

load_dotenv()

# API Keys (set  these in .env file)
OPENAI_API_KEY = os.get.env("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.get.env("ANTHROPIC_API_KEY")

# Models to test
MODELS = {
    "openai": ["gpt-3.5-turbo", "gpt-4"],
    "anthropic": ["claude-3-5-sonnet-20241022"],
    "ollama": ["llama3-70b", "llama3-70b-chat"],
}

# Scoring weights
WEIGHTS = {
    "constraint_compliance": 0.4, # adherence to explicit instructions and constraints
    "reasoning_transparency": 0.3, # clarity and logical traceability of the model's reasoning steps
    "error_handling": 0.3, # ability to recognize ambiguity, contradictions, or internal errors and correct them
}

# Rubric thresholds
from