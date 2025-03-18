import os
from dotenv import load_dotenv

load_dotenv()

# SPADE Configuration
FACILITATOR_JID = os.getenv("FACILITATOR_JID", "facilitator@localhost")
FACILITATOR_PASSWORD = os.getenv("FACILITATOR_PASSWORD", "123456")

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
