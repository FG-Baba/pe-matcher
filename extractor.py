"""
LLM-based company profile extraction module.
"""

import json
from anthropic import Anthropic
import config

client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

EXTRACTION_PROMPT = """Analyze the following website content and extract a structured company profile.

WEBSITE CONTENT:
{content}

Extract the following information. If information is not available, use null. Include a confidence score (0.0-1.0) for each field based on how clearly it was stated vs inferred.

Return ONLY valid JSON in this exact format:
{{
    "company_name": "string or null",
    "industry": "string - be specific (e.g., 'B2B SaaS - Marketing Automation' not just 'Technology')",
    "industry_confidence": 0.0-1.0,
    "location": {{
        "city": "string or null",
        "state": "string or null",
        "country": "string or null"
    }},
    "location_confidence": 0.0-1.0,
    "products_services": ["list of main products/services offered"],
    "products_confidence": 0.0-1.0,
    "company_size": {{
        "estimate": "string (e.g., '10-50 employees', '50-100 employees', '100-500 employees')",
        "signals": ["list of signals used to estimate - e.g., 'careers page shows 12 open roles', 'team page lists 25 people'"]
    }},
    "size_confidence": 0.0-1.0,
    "founded_year": "integer or null",
    "founded_confidence": 0.0-1.0,
    "leadership": [
        {{"name": "string", "title": "string"}}
    ],
    "leadership_confidence": 0.0-1.0,
    "customer_segments": ["list of target customer types - e.g., 'Enterprise', 'SMB', 'Healthcare providers'"],
    "customers_confidence": 0.0-1.0,
    "tech_signals": ["any technology stack indicators found"],
    "business_model": "string - e.g., 'SaaS subscription', 'Professional services', 'E-commerce'",
    "business_model_confidence": 0.0-1.0,
    "growth_signals": ["any indicators of growth stage - funding, hiring, expansion mentions"],
    "summary": "2-3 sentence summary of what this company does"
}}
"""


def extract_company_profile(website_content: str) -> dict:
    """
    Use Claude to extract structured company profile from website content.

    Args:
        website_content: Combined text content from scraped website

    Returns:
        dict with extracted company profile
    """
    if not website_content:
        return {"error": "No content to analyze"}

    # Truncate if too long
    if len(website_content) > 50000:
        website_content = website_content[:50000] + "\n[Content truncated...]"

    try:
        message = client.messages.create(
            model=config.EXTRACTION_MODEL,
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(content=website_content)
                }
            ]
        )

        response_text = message.content[0].text

        # Parse JSON from response
        # Handle potential markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        profile = json.loads(response_text.strip())
        profile['extraction_success'] = True
        return profile

    except json.JSONDecodeError as e:
        return {
            "extraction_success": False,
            "error": f"Failed to parse LLM response as JSON: {e}",
            "raw_response": response_text if 'response_text' in dir() else None
        }
    except Exception as e:
        return {
            "extraction_success": False,
            "error": f"Extraction failed: {e}"
        }


def calculate_overall_confidence(profile: dict) -> float:
    """Calculate weighted overall confidence score for the profile."""
    if not profile.get('extraction_success'):
        return 0.0

    weights = {
        'industry_confidence': 0.25,
        'location_confidence': 0.15,
        'products_confidence': 0.20,
        'size_confidence': 0.15,
        'business_model_confidence': 0.15,
        'customers_confidence': 0.10
    }

    total_weight = 0
    weighted_sum = 0

    for field, weight in weights.items():
        if field in profile and profile[field] is not None:
            weighted_sum += profile[field] * weight
            total_weight += weight

    if total_weight == 0:
        return 0.0

    return round(weighted_sum / total_weight, 2)
