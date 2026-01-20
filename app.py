"""
PE Matcher - Streamlit Application
Find potential PE buyers for SMB companies by analyzing their websites.
"""

import streamlit as st
import time
import json
from fpdf import FPDF

from scraper import scrape_website, get_combined_content
from extractor import extract_company_profile, calculate_overall_confidence
from matcher import match_pe_funds
from output import format_json_output, format_markdown_report

# Page configuration
st.set_page_config(
    page_title="PE Matcher",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Clean, professional CSS styling
st.markdown("""
<style>
    /* Clean white background */
    .stApp {
        background-color: #ffffff;
    }

    /* Main header */
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.25rem;
        text-align: center;
        letter-spacing: -0.5px;
    }

    .sub-header {
        font-size: 1.1rem;
        color: #6b7280;
        text-align: center;
        margin-bottom: 2.5rem;
        font-weight: 400;
    }

    /* Input section labels */
    .input-label {
        font-size: 0.9rem;
        font-weight: 600;
        color: #374151;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Input areas */
    .stTextArea textarea {
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        background: #f9fafb;
        font-size: 0.95rem;
        transition: all 0.2s ease;
    }

    .stTextArea textarea:focus {
        border-color: #2563eb;
        background: #ffffff;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }

    /* Primary button */
    .stButton > button {
        background: #1a1a2e;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        letter-spacing: 0.3px;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background: #2d2d44;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(26, 26, 46, 0.15);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: transparent;
        border-bottom: 1px solid #e5e7eb;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 0;
        padding: 12px 24px;
        font-weight: 500;
        color: #6b7280;
        border-bottom: 2px solid transparent;
        background: transparent;
    }

    .stTabs [aria-selected="true"] {
        color: #1a1a2e;
        border-bottom: 2px solid #1a1a2e;
        background: transparent;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.6rem;
        font-weight: 700;
        color: #1a1a2e;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.8rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Progress bar */
    .stProgress > div > div {
        background: #1a1a2e;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #1a1a2e;
        background: #f9fafb;
        border-radius: 8px;
    }

    /* Info/Alert boxes */
    .stAlert {
        border-radius: 8px;
        border: none;
        background: #f0f9ff;
    }

    /* Section divider */
    hr {
        border: none;
        border-top: 1px solid #e5e7eb;
        margin: 1.5rem 0;
    }

    /* Result cards */
    .result-card {
        background: #f9fafb;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 3px solid #1a1a2e;
    }

    /* Score pills */
    .score-high {
        background: #dcfce7;
        color: #166534;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: 600;
        font-size: 0.85rem;
    }

    .score-medium {
        background: #fef3c7;
        color: #92400e;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: 600;
        font-size: 0.85rem;
    }

    .score-low {
        background: #fee2e2;
        color: #991b1b;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: 600;
        font-size: 0.85rem;
    }

    /* Download buttons */
    .stDownloadButton > button {
        background: #ffffff;
        color: #1a1a2e;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }

    .stDownloadButton > button:hover {
        background: #f9fafb;
        border-color: #1a1a2e;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Clean typography */
    h1, h2, h3, h4, h5 {
        color: #1a1a2e;
        font-weight: 600;
    }

    /* Subtle shadows for depth */
    .stExpander {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
</style>
""", unsafe_allow_html=True)


class PDFReport(FPDF):
    """Custom PDF class for PE Matcher reports."""

    def header(self):
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(26, 26, 46)
        self.cell(0, 15, 'PE Matcher Report', align='C', ln=True)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')


def generate_pdf_report(url: str, company_profile: dict, pe_matches: dict) -> bytes:
    """Generate a PDF report from the analysis results."""
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    company_name = company_profile.get("company_name", "Unknown Company")
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(26, 26, 46)
    pdf.cell(0, 10, f'Analysis: {company_name}', ln=True)

    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(0, 8, f'Source: {url}', ln=True)
    pdf.ln(5)

    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(26, 26, 46)
    pdf.cell(0, 10, 'Company Profile', ln=True)

    pdf.set_font('Helvetica', '', 11)
    pdf.set_text_color(55, 65, 81)

    if company_profile.get("industry"):
        pdf.cell(0, 7, f'Industry: {company_profile["industry"]}', ln=True)

    location = company_profile.get("location", {})
    if location:
        loc_parts = [location.get("city"), location.get("state"), location.get("country")]
        loc_str = ", ".join([p for p in loc_parts if p])
        if loc_str:
            pdf.cell(0, 7, f'Location: {loc_str}', ln=True)

    size_info = company_profile.get("company_size", {})
    if size_info.get("estimate"):
        pdf.cell(0, 7, f'Size: {size_info["estimate"]}', ln=True)

    if company_profile.get("business_model"):
        pdf.cell(0, 7, f'Business Model: {company_profile["business_model"]}', ln=True)

    if company_profile.get("summary"):
        pdf.ln(3)
        pdf.set_font('Helvetica', 'I', 10)
        pdf.multi_cell(0, 6, company_profile["summary"])

    pdf.ln(8)

    analysis = pe_matches.get("analysis", {})
    if analysis:
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(26, 26, 46)
        pdf.cell(0, 10, 'PE Readiness Assessment', ln=True)

        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(55, 65, 81)

        if analysis.get("pe_readiness"):
            pdf.cell(0, 7, f'Readiness: {analysis["pe_readiness"]}', ln=True)
        if analysis.get("estimated_enterprise_value"):
            pdf.cell(0, 7, f'Est. Value: {analysis["estimated_enterprise_value"]}', ln=True)
        if analysis.get("pe_readiness_rationale"):
            pdf.set_font('Helvetica', 'I', 10)
            pdf.multi_cell(0, 6, analysis["pe_readiness_rationale"])

        pdf.ln(8)

    matches = pe_matches.get("matches", [])
    if matches:
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(26, 26, 46)
        pdf.cell(0, 10, 'Top PE Fund Matches', ln=True)

        for match in matches[:7]:
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(26, 26, 46)

            rank = match.get("rank", "")
            name = match.get("fund_name", "Unknown")
            score = match.get("fit_score", 0)

            pdf.cell(0, 8, f'{rank}. {name} (Score: {score}/100)', ln=True)

            if match.get("rationale"):
                pdf.set_font('Helvetica', '', 10)
                pdf.set_text_color(55, 65, 81)
                pdf.multi_cell(0, 5, match["rationale"])

            pdf.ln(3)

    return bytes(pdf.output())


def process_single_url(url: str, user_context: str) -> dict:
    """Process a single URL through the full pipeline."""
    result = {
        "url": url,
        "success": False,
        "error": None,
        "company_profile": None,
        "pe_matches": None,
        "processing_time": 0
    }

    start_time = time.time()

    scraped = scrape_website(url)
    if not scraped["success"]:
        result["error"] = f"Scraping failed: {scraped.get('error', 'Unknown error')}"
        return result

    content = get_combined_content(scraped)
    if not content:
        result["error"] = "No content extracted from website"
        return result

    profile = extract_company_profile(content)
    if not profile.get("extraction_success"):
        result["error"] = f"Extraction failed: {profile.get('error', 'Unknown error')}"
        return result

    profile["overall_confidence"] = calculate_overall_confidence(profile)
    result["company_profile"] = profile

    matches = match_pe_funds(profile, user_context)
    if not matches.get("matching_success"):
        result["error"] = f"Matching failed: {matches.get('error', 'Unknown error')}"
        result["success"] = True
        result["processing_time"] = time.time() - start_time
        return result

    result["pe_matches"] = matches
    result["success"] = True
    result["processing_time"] = time.time() - start_time

    return result


def main():
    # Header
    st.markdown('<h1 class="main-header">PE Matcher</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Identify potential private equity buyers for SMB companies</p>', unsafe_allow_html=True)

    # Input section
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown('<p class="input-label">Company URLs</p>', unsafe_allow_html=True)
        urls_input = st.text_area(
            "URLs",
            height=120,
            placeholder="https://example-company.com\nhttps://another-smb.com",
            help="Enter up to 10 URLs, one per line",
            label_visibility="collapsed"
        )

    with col2:
        st.markdown('<p class="input-label">Deal Context (Optional)</p>', unsafe_allow_html=True)
        user_context = st.text_area(
            "Context",
            height=120,
            placeholder="Founder seeking exit in 12 months\nPrefers growth equity\n$5M ARR, profitable",
            help="Add context to customize PE fund recommendations",
            label_visibility="collapsed"
        )

    # Analyze button
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        analyze_clicked = st.button("Analyze Companies", type="primary", use_container_width=True)

    if analyze_clicked:
        urls = [u.strip() for u in urls_input.strip().split("\n") if u.strip()]

        if not urls:
            st.error("Please enter at least one URL")
            return

        if len(urls) > 10:
            st.warning("Maximum 10 URLs. Processing first 10 only.")
            urls = urls[:10]

        results = []

        st.markdown("---")
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, url in enumerate(urls):
            status_text.text(f"Analyzing {url}...")
            result = process_single_url(url, user_context)
            results.append(result)
            progress_bar.progress((i + 1) / len(urls))

        status_text.text("Analysis complete")
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()

        st.session_state["results"] = results

    # Results
    if "results" in st.session_state and st.session_state["results"]:
        st.markdown("---")
        st.markdown("### Results")

        for i, result in enumerate(st.session_state["results"]):
            company_name = result.get("company_profile", {}).get("company_name", result["url"])

            with st.expander(f"{company_name}", expanded=(i == 0)):
                if not result["success"] and result["error"]:
                    st.error(result["error"])
                    continue

                tab1, tab2, tab3 = st.tabs(["Profile", "PE Matches", "Export"])

                with tab1:
                    display_company_profile(result["company_profile"])

                with tab2:
                    display_pe_matches(result["pe_matches"])

                with tab3:
                    display_export_options(result)


def display_company_profile(profile: dict):
    """Display the extracted company profile."""
    if not profile:
        st.warning("No profile data available")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Company Details**")

        if profile.get("company_name"):
            st.markdown(f"Name: {profile['company_name']}")
        if profile.get("industry"):
            st.markdown(f"Industry: {profile['industry']}")

        location = profile.get("location", {})
        if location:
            loc_parts = [location.get("city"), location.get("state"), location.get("country")]
            loc_str = ", ".join([p for p in loc_parts if p])
            if loc_str:
                st.markdown(f"Location: {loc_str}")

        size_info = profile.get("company_size", {})
        if size_info.get("estimate"):
            st.markdown(f"Size: {size_info['estimate']}")

        if profile.get("founded_year"):
            st.markdown(f"Founded: {profile['founded_year']}")

        if profile.get("business_model"):
            st.markdown(f"Model: {profile['business_model']}")

    with col2:
        st.markdown("**Products & Services**")
        products = profile.get("products_services", [])
        if products:
            for product in products[:5]:
                st.markdown(f"• {product}")
        else:
            st.caption("Not identified")

        st.markdown("**Target Customers**")
        customers = profile.get("customer_segments", [])
        if customers:
            for customer in customers[:4]:
                st.markdown(f"• {customer}")
        else:
            st.caption("Not identified")

    if profile.get("summary"):
        st.info(profile["summary"])

    overall_conf = profile.get("overall_confidence", 0)
    st.metric("Extraction Confidence", f"{overall_conf:.0%}")


def display_pe_matches(matches: dict):
    """Display PE fund matches."""
    if not matches:
        st.warning("No matching data available")
        return

    analysis = matches.get("analysis", {})
    if analysis:
        col1, col2, col3 = st.columns(3)

        with col1:
            readiness = analysis.get("pe_readiness", "Unknown")
            st.metric("PE Readiness", readiness)

        with col2:
            ev = analysis.get("estimated_enterprise_value", "N/A")
            st.metric("Est. Value", ev)

        with col3:
            match_count = len(matches.get("matches", []))
            st.metric("Matches", match_count)

        if analysis.get("pe_readiness_rationale"):
            st.caption(analysis["pe_readiness_rationale"])

    st.markdown("---")

    fund_matches = matches.get("matches", [])
    if not fund_matches:
        st.info("No PE fund matches found.")
        return

    for match in fund_matches:
        rank = match.get("rank", "")
        name = match.get("fund_name", "Unknown")
        score = match.get("fit_score", 0)

        if score >= 80:
            score_class = "score-high"
        elif score >= 60:
            score_class = "score-medium"
        else:
            score_class = "score-low"

        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(f"**{rank}. {name}**")
            if match.get("rationale"):
                st.caption(match["rationale"])

        with col2:
            st.markdown(f'<span class="{score_class}">{score}</span>', unsafe_allow_html=True)

        with st.expander("Details"):
            if match.get("key_alignment"):
                st.markdown("**Alignment:**")
                for point in match["key_alignment"]:
                    st.markdown(f"• {point}")

            if match.get("potential_concerns"):
                st.markdown("**Concerns:**")
                for concern in match["potential_concerns"]:
                    st.markdown(f"• {concern}")

            if match.get("deal_type_fit"):
                st.markdown(f"**Deal Type:** {match['deal_type_fit']}")


def display_export_options(result: dict):
    """Display export options."""
    if not result.get("success"):
        st.warning("No data to export")
        return

    json_output = format_json_output(
        result["url"],
        result.get("company_profile", {}),
        result.get("pe_matches", {}),
        result.get("processing_time", 0)
    )

    markdown_output = format_markdown_report(
        result["url"],
        result.get("company_profile", {}),
        result.get("pe_matches", {})
    )

    pdf_bytes = generate_pdf_report(
        result["url"],
        result.get("company_profile", {}),
        result.get("pe_matches", {})
    )

    filename_base = result['url'].replace('https://', '').replace('http://', '').replace('/', '_')[:25]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            label="Download PDF",
            data=pdf_bytes,
            file_name=f"pe_analysis_{filename_base}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    with col2:
        st.download_button(
            label="Download Markdown",
            data=markdown_output,
            file_name=f"pe_analysis_{filename_base}.md",
            mime="text/markdown",
            use_container_width=True
        )

    with col3:
        st.download_button(
            label="Download JSON",
            data=json.dumps(json_output, indent=2),
            file_name=f"pe_analysis_{filename_base}.json",
            mime="application/json",
            use_container_width=True
        )

    with st.expander("Preview JSON"):
        st.json(json_output)


if __name__ == "__main__":
    main()
