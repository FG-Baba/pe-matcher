"""
PE Matcher - Streamlit Application
Find potential PE buyers for SMB companies by analyzing their websites.
"""

import streamlit as st
import time
import json
import io
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

# Modern, vibrant CSS styling
st.markdown("""
<style>
    /* Main background and fonts */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
    }

    /* Headers */
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(120deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        text-align: center;
    }

    .sub-header {
        font-size: 1.2rem;
        color: #64748b;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* Cards */
    .stExpander {
        background: white;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* Input areas */
    .stTextArea textarea {
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        transition: border-color 0.2s;
    }

    .stTextArea textarea:focus {
        border-color: #8b5cf6;
        box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(120deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1.1rem;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px -5px rgba(99, 102, 241, 0.4);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #f1f5f9;
        padding: 8px;
        border-radius: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
        color: #6366f1;
    }

    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(120deg, #6366f1 0%, #8b5cf6 100%);
    }

    /* Info boxes */
    .stAlert {
        border-radius: 12px;
        border: none;
    }

    /* Section headers */
    .section-header {
        font-size: 1.4rem;
        font-weight: 700;
        color: #1e293b;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #8b5cf6;
        display: inline-block;
    }

    /* Match cards */
    .match-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #8b5cf6;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    /* Score badges */
    .score-high {
        background: linear-gradient(120deg, #10b981, #34d399);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
    }

    .score-medium {
        background: linear-gradient(120deg, #f59e0b, #fbbf24);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
    }

    .score-low {
        background: linear-gradient(120deg, #ef4444, #f87171);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
    }

    /* Download buttons */
    .stDownloadButton > button {
        background: white;
        color: #6366f1;
        border: 2px solid #6366f1;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s;
    }

    .stDownloadButton > button:hover {
        background: #6366f1;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


class PDFReport(FPDF):
    """Custom PDF class for PE Matcher reports."""

    def header(self):
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(99, 102, 241)
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

    # Company name
    company_name = company_profile.get("company_name", "Unknown Company")
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, f'Analysis: {company_name}', ln=True)

    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 8, f'Source: {url}', ln=True)
    pdf.ln(5)

    # Company Profile Section
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(0, 10, 'Company Profile', ln=True)

    pdf.set_font('Helvetica', '', 11)
    pdf.set_text_color(30, 41, 59)

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

    # PE Readiness
    analysis = pe_matches.get("analysis", {})
    if analysis:
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(99, 102, 241)
        pdf.cell(0, 10, 'PE Readiness Assessment', ln=True)

        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(30, 41, 59)

        if analysis.get("pe_readiness"):
            pdf.cell(0, 7, f'Readiness: {analysis["pe_readiness"]}', ln=True)
        if analysis.get("estimated_enterprise_value"):
            pdf.cell(0, 7, f'Est. Value: {analysis["estimated_enterprise_value"]}', ln=True)
        if analysis.get("pe_readiness_rationale"):
            pdf.set_font('Helvetica', 'I', 10)
            pdf.multi_cell(0, 6, analysis["pe_readiness_rationale"])

        pdf.ln(8)

    # PE Matches
    matches = pe_matches.get("matches", [])
    if matches:
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(99, 102, 241)
        pdf.cell(0, 10, 'Top PE Fund Matches', ln=True)

        for match in matches[:7]:  # Limit to top 7 for PDF
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(30, 41, 59)

            rank = match.get("rank", "")
            name = match.get("fund_name", "Unknown")
            score = match.get("fit_score", 0)

            pdf.cell(0, 8, f'{rank}. {name} (Score: {score}/100)', ln=True)

            if match.get("rationale"):
                pdf.set_font('Helvetica', '', 10)
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

    # Step 1: Scrape website
    scraped = scrape_website(url)
    if not scraped["success"]:
        result["error"] = f"Scraping failed: {scraped.get('error', 'Unknown error')}"
        return result

    # Step 2: Extract company profile
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

    # Step 3: Match PE funds
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
    st.markdown('<h1 class="main-header">🎯 PE Matcher</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Discover the perfect private equity partners for SMB acquisitions</p>', unsafe_allow_html=True)

    # Input section with columns
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("#### 🔗 Company URLs")
        urls_input = st.text_area(
            "Enter website URLs (one per line)",
            height=140,
            placeholder="https://example-company.com\nhttps://another-smb.com",
            help="Analyze up to 10 companies at once",
            label_visibility="collapsed"
        )

    with col2:
        st.markdown("#### 💡 Deal Context")
        user_context = st.text_area(
            "Optional context",
            height=140,
            placeholder="• Founder seeking exit in 12 months\n• Prefers growth equity\n• $5M ARR, profitable",
            help="Add deal-specific details to customize recommendations",
            label_visibility="collapsed"
        )

    # Centered analyze button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        analyze_clicked = st.button("🚀 Analyze Companies", type="primary", use_container_width=True)

    if analyze_clicked:
        urls = [u.strip() for u in urls_input.strip().split("\n") if u.strip()]

        if not urls:
            st.error("⚠️ Please enter at least one URL")
            return

        if len(urls) > 10:
            st.warning("📝 Maximum 10 URLs allowed. Processing first 10.")
            urls = urls[:10]

        # Process each URL
        results = []

        # Progress section
        st.markdown("---")
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, url in enumerate(urls):
                status_text.markdown(f"🔍 **Analyzing** `{url}`")
                result = process_single_url(url, user_context)
                results.append(result)
                progress_bar.progress((i + 1) / len(urls))

            status_text.markdown("✅ **Analysis complete!**")
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()

        st.session_state["results"] = results

    # Display results
    if "results" in st.session_state and st.session_state["results"]:
        st.markdown("---")
        st.markdown('<p class="section-header">📊 Results</p>', unsafe_allow_html=True)

        for i, result in enumerate(st.session_state["results"]):
            company_name = result.get("company_profile", {}).get("company_name", result["url"])

            with st.expander(f"🏢 {company_name}", expanded=(i == 0)):
                if not result["success"] and result["error"]:
                    st.error(f"❌ {result['error']}")
                    continue

                # Tabs
                tab1, tab2, tab3 = st.tabs(["📋 Company Profile", "🎯 PE Matches", "📥 Export"])

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
        st.markdown("##### 🏢 Company Details")

        details = []
        if profile.get("company_name"):
            details.append(f"**Name:** {profile['company_name']}")
        if profile.get("industry"):
            details.append(f"**Industry:** {profile['industry']}")

        location = profile.get("location", {})
        if location:
            loc_parts = [location.get("city"), location.get("state"), location.get("country")]
            loc_str = ", ".join([p for p in loc_parts if p])
            if loc_str:
                details.append(f"**Location:** {loc_str}")

        size_info = profile.get("company_size", {})
        if size_info.get("estimate"):
            details.append(f"**Size:** {size_info['estimate']}")

        if profile.get("founded_year"):
            details.append(f"**Founded:** {profile['founded_year']}")

        if profile.get("business_model"):
            details.append(f"**Model:** {profile['business_model']}")

        for detail in details:
            st.markdown(detail)

    with col2:
        st.markdown("##### 📦 Products & Services")
        products = profile.get("products_services", [])
        if products:
            for product in products[:5]:
                st.markdown(f"• {product}")
        else:
            st.caption("Not identified")

        st.markdown("##### 👥 Target Customers")
        customers = profile.get("customer_segments", [])
        if customers:
            for customer in customers[:4]:
                st.markdown(f"• {customer}")
        else:
            st.caption("Not identified")

    if profile.get("summary"):
        st.info(f"💬 {profile['summary']}")

    # Confidence metric
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
            emoji = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}.get(readiness, "⚪")
            st.metric("PE Readiness", f"{emoji} {readiness}")

        with col2:
            ev = analysis.get("estimated_enterprise_value", "N/A")
            st.metric("Est. Value", ev)

        with col3:
            match_count = len(matches.get("matches", []))
            st.metric("Matches Found", match_count)

        if analysis.get("pe_readiness_rationale"):
            st.caption(analysis["pe_readiness_rationale"])

    st.markdown("---")

    fund_matches = matches.get("matches", [])
    if not fund_matches:
        st.info("No PE fund matches found for this company.")
        return

    for match in fund_matches:
        rank = match.get("rank", "")
        name = match.get("fund_name", "Unknown")
        score = match.get("fit_score", 0)

        # Score styling
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
                st.markdown(f"_{match['rationale']}_")

        with col2:
            st.markdown(f'<span class="{score_class}">{score}/100</span>', unsafe_allow_html=True)

        with st.expander("View details", expanded=False):
            if match.get("key_alignment"):
                st.markdown("**✅ Key Alignment:**")
                for point in match["key_alignment"]:
                    st.markdown(f"  • {point}")

            if match.get("potential_concerns"):
                st.markdown("**⚠️ Concerns:**")
                for concern in match["potential_concerns"]:
                    st.markdown(f"  • {concern}")

            if match.get("deal_type_fit"):
                st.markdown(f"**Deal Type:** {match['deal_type_fit']}")

        st.markdown("")


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

    # Generate PDF
    pdf_bytes = generate_pdf_report(
        result["url"],
        result.get("company_profile", {}),
        result.get("pe_matches", {})
    )

    st.markdown("#### Download Options")

    col1, col2, col3 = st.columns(3)

    filename_base = result['url'].replace('https://', '').replace('http://', '').replace('/', '_')[:25]

    with col1:
        st.download_button(
            label="📄 PDF Report",
            data=pdf_bytes,
            file_name=f"pe_analysis_{filename_base}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    with col2:
        st.download_button(
            label="📝 Markdown",
            data=markdown_output,
            file_name=f"pe_analysis_{filename_base}.md",
            mime="text/markdown",
            use_container_width=True
        )

    with col3:
        st.download_button(
            label="🔧 JSON",
            data=json.dumps(json_output, indent=2),
            file_name=f"pe_analysis_{filename_base}.json",
            mime="application/json",
            use_container_width=True
        )

    # Preview section
    with st.expander("👀 Preview JSON"):
        st.json(json_output)


if __name__ == "__main__":
    main()
