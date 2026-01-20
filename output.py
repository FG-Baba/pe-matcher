"""
Output formatting module - JSON and Markdown formatters.
"""

import json
from datetime import datetime


def format_json_output(
    url: str,
    company_profile: dict,
    pe_matches: dict,
    processing_time: float
) -> dict:
    """
    Format the complete analysis as structured JSON.
    """
    return {
        "input_url": url,
        "company_profile": company_profile,
        "pe_analysis": pe_matches.get("analysis", {}),
        "pe_matches": pe_matches.get("matches", []),
        "additional_notes": pe_matches.get("additional_notes", ""),
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "processing_time_seconds": round(processing_time, 2),
            "extraction_confidence": company_profile.get("overall_confidence", 0),
            "matching_success": pe_matches.get("matching_success", False)
        }
    }


def format_markdown_report(
    url: str,
    company_profile: dict,
    pe_matches: dict
) -> str:
    """
    Format the analysis as a human-readable Markdown report.
    """
    lines = []

    # Header
    company_name = company_profile.get("company_name", "Unknown Company")
    lines.append(f"# PE Buyer Analysis: {company_name}")
    lines.append("")
    lines.append(f"**Source URL**: {url}")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # Company Profile Section
    lines.append("---")
    lines.append("## Company Profile")
    lines.append("")

    if company_profile.get("industry"):
        lines.append(f"**Industry**: {company_profile['industry']}")

    location = company_profile.get("location", {})
    if location:
        loc_parts = [location.get("city"), location.get("state"), location.get("country")]
        loc_str = ", ".join([p for p in loc_parts if p])
        if loc_str:
            lines.append(f"**Location**: {loc_str}")

    size_info = company_profile.get("company_size", {})
    if size_info.get("estimate"):
        lines.append(f"**Size**: {size_info['estimate']}")

    if company_profile.get("founded_year"):
        lines.append(f"**Founded**: {company_profile['founded_year']}")

    if company_profile.get("business_model"):
        lines.append(f"**Business Model**: {company_profile['business_model']}")

    lines.append("")

    # Products/Services
    products = company_profile.get("products_services", [])
    if products:
        lines.append("### Products & Services")
        for product in products[:5]:  # Limit to 5
            lines.append(f"- {product}")
        lines.append("")

    # Customer Segments
    customers = company_profile.get("customer_segments", [])
    if customers:
        lines.append("### Target Customers")
        for customer in customers[:5]:
            lines.append(f"- {customer}")
        lines.append("")

    # Summary
    if company_profile.get("summary"):
        lines.append("### Summary")
        lines.append(company_profile["summary"])
        lines.append("")

    # PE Analysis Section
    analysis = pe_matches.get("analysis", {})
    if analysis:
        lines.append("---")
        lines.append("## PE Readiness Assessment")
        lines.append("")

        if analysis.get("company_summary"):
            lines.append(f"**Overview**: {analysis['company_summary']}")

        if analysis.get("estimated_enterprise_value"):
            lines.append(f"**Est. Enterprise Value**: {analysis['estimated_enterprise_value']}")

        if analysis.get("pe_readiness"):
            lines.append(f"**PE Readiness**: {analysis['pe_readiness']}")

        if analysis.get("pe_readiness_rationale"):
            lines.append(f"**Rationale**: {analysis['pe_readiness_rationale']}")

        lines.append("")

    # PE Matches Section
    matches = pe_matches.get("matches", [])
    if matches:
        lines.append("---")
        lines.append("## Top PE Fund Matches")
        lines.append("")

        for match in matches:
            rank = match.get("rank", "")
            name = match.get("fund_name", "Unknown")
            score = match.get("fit_score", 0)

            lines.append(f"### {rank}. {name}")
            lines.append(f"**Fit Score**: {score}/100")
            lines.append("")

            if match.get("rationale"):
                lines.append(f"**Why they're a fit**: {match['rationale']}")
                lines.append("")

            if match.get("key_alignment"):
                lines.append("**Key Alignment Points**:")
                for point in match["key_alignment"]:
                    lines.append(f"- {point}")
                lines.append("")

            if match.get("potential_concerns"):
                lines.append("**Potential Concerns**:")
                for concern in match["potential_concerns"]:
                    lines.append(f"- {concern}")
                lines.append("")

            if match.get("deal_type_fit"):
                lines.append(f"**Deal Type**: {match['deal_type_fit']}")
                lines.append("")

            lines.append("---")
            lines.append("")

    # Additional Notes
    if pe_matches.get("additional_notes"):
        lines.append("## Additional Notes")
        lines.append(pe_matches["additional_notes"])
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("*Report generated by PE Matcher Tool*")

    return "\n".join(lines)


def export_to_file(content: str, filepath: str, format: str = "md"):
    """Export content to a file."""
    if format == "json":
        with open(filepath, 'w') as f:
            if isinstance(content, dict):
                json.dump(content, f, indent=2)
            else:
                f.write(content)
    else:
        with open(filepath, 'w') as f:
            f.write(content)
