import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Model Configuration
EXTRACTION_MODEL = "claude-sonnet-4-20250514"  # Fast, cost-effective for extraction
MATCHING_MODEL = "claude-sonnet-4-20250514"     # Can upgrade to opus for complex reasoning

# Scraping Configuration
REQUEST_TIMEOUT = 10  # seconds
MAX_URLS_PER_BATCH = 10
USER_AGENT = "Mozilla/5.0 (compatible; PEMatcher/1.0; +research)"

# Output Configuration
MAX_PE_MATCHES = 10
