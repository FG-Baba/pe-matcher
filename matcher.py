"""
PE Fund matching module - matches company profiles to potential PE buyers.
"""

import json
from pathlib import Path
from anthropic import Anthropic
import config

client = Anthropic(api_key=config.ANTHROPIC_API_KEY)


def load_pe_funds() -> list[dict]:
    """Load the PE fund seed dataset."""
    data_path = Path(__file__).parent / "data" / "pe_funds.json"
    with open(data_path, 'r') as f:
        data = json.load(f)
    return data['funds']


MATCHING_PROMPT = """You are a PE deal sourcing expert. Analyze the company profile and find the best matching PE funds.

COMPANY PROFILE:
{company_profile}

USER CONTEXT (deal notes, preferences, timing):
{user_context}

PE FUND DATABASE:
{pe_funds}

Your task:
1. Analyze the company's industry, size, business model, and growth stage
2. Match against PE funds based on: sector focus, check size fit, geographic alignment, investment thesis fit
3. Consider the user context to adjust rankings (e.g., if they prefer growth equity over buyout)
4. Return the top {num_matches} matches with detailed rationale

IMPORTANT: Be realistic about fit. Not every company is a good PE target. If the company seems too small, too early, or misaligned, note that in your analysis.

Return ONLY valid JSON in this exact format:
{{
    "analysis": {{
        "company_summary": "1-2 sentence summary of the company",
        "estimated_enterprise_value": "rough estimate based on signals (e.g., '$10-25M', '$50-100M')",
        "pe_readiness": "High/Medium/Low - is this company likely PE-ready?",
        "pe_readiness_rationale": "Why or why not"
    }},
    "matches": [
        {{
            "rank": 1,
            "fund_name": "string",
            "fit_score": 0-100,
            "rationale": "2-3 sentences explaining why this fund is a good match",
            "key_alignment": ["list of specific alignment points"],
            "potential_concerns": ["list of any concerns or gaps"],
            "deal_type_fit": "growth equity / buyout / either"
        }}
    ],
    "additional_notes": "Any other relevant observations for the user"
}}
"""


def match_pe_funds(
    company_profile: dict,
    user_context: str = "",
    num_matches: int = 10
) -> dict:
    """
    Match a company profile against PE funds using LLM reasoning.

    Args:
        company_profile: Extracted company profile from extractor module
        user_context: Optional user-provided context about the deal
        num_matches: Number of matches to return

    Returns:
        dict with analysis and ranked PE fund matches
    """
    pe_funds = load_pe_funds()

    # Prepare PE funds summary for the prompt (keep it concise)
    pe_summary = []
    for fund in pe_funds:
        pe_summary.append({
            "name": fund["name"],
            "aum_billions": fund.get("aum_billions"),
            "sector_focus": fund.get("sector_focus", []),
            "check_size_mm": fund.get("check_size_mm", {}),
            "stage": fund.get("stage", []),
            "geography": fund.get("geography", []),
            "thesis_keywords": fund.get("thesis_keywords", [])
        })

    try:
        message = client.messages.create(
            model=config.MATCHING_MODEL,
            max_tokens=3000,
            messages=[
                {
                    "role": "user",
                    "content": MATCHING_PROMPT.format(
                        company_profile=json.dumps(company_profile, indent=2),
                        user_context=user_context if user_context else "No additional context provided",
                        pe_funds=json.dumps(pe_summary, indent=2),
                        num_matches=num_matches
                    )
                }
            ]
        )

        response_text = message.content[0].text

        # Parse JSON from response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text.strip())
        result['matching_success'] = True
        return result

    except json.JSONDecodeError as e:
        return {
            "matching_success": False,
            "error": f"Failed to parse LLM response: {e}",
            "raw_response": response_text if 'response_text' in dir() else None
        }
    except Exception as e:
        return {
            "matching_success": False,
            "error": f"Matching failed: {e}"
        }


def get_fund_details(fund_name: str) -> dict:
    """Get full details for a specific fund."""
    pe_funds = load_pe_funds()
    for fund in pe_funds:
        if fund["name"].lower() == fund_name.lower():
            return fund
    return {}


def filter_funds_by_criteria(
    min_check_size: int = None,
    max_check_size: int = None,
    sectors: list[str] = None,
    stages: list[str] = None
) -> list[dict]:
    """
    Pre-filter PE funds by basic criteria before LLM matching.
    Useful for reducing the dataset for very specific searches.
    """
    pe_funds = load_pe_funds()
    filtered = []

    for fund in pe_funds:
        # Check size filter
        if min_check_size:
            fund_max = fund.get("check_size_mm", {}).get("max", 0)
            if fund_max < min_check_size:
                continue

        if max_check_size:
            fund_min = fund.get("check_size_mm", {}).get("min", float('inf'))
            if fund_min > max_check_size:
                continue

        # Sector filter
        if sectors:
            fund_sectors = [s.lower() for s in fund.get("sector_focus", [])]
            if not any(s.lower() in ' '.join(fund_sectors) for s in sectors):
                continue

        # Stage filter
        if stages:
            fund_stages = [s.lower() for s in fund.get("stage", [])]
            if not any(s.lower() in fund_stages for s in stages):
                continue

        filtered.append(fund)

    return filtered
